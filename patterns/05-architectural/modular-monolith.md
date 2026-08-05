---
name: Modular Monolith
slug: modular-monolith
family: 05-architectural
category: Architectural
aliases: [Majestic Monolith, Modulith, Component-Based Monolith]
first_described: "Simon Brown, conference talks and Software Architecture for Developers, circa 2014, popularizing a term already in informal use among practitioners"
maturity: established
related: [layered-architecture, hexagonal-architecture, clean-architecture, microkernel, event-driven-architecture]
incompatible_with: []
verified: 2026-08-02
---

# Modular Monolith

## 1. Name, aliases, and lineage

The canonical name is Modular Monolith, sometimes shortened in casual
engineering conversation to Modulith. There is no single paper of origin the
way there is for a Gang of Four pattern. The term is a reaction, and its
lineage runs through three separate threads that converged over roughly a
decade.

The first thread is the word itself. Software architect Simon Brown used
"modular monolith" in conference talks and in his book on software
architecture as a label for a single deployable application whose internal
code is organized into modules with explicit boundaries and explicit public
interfaces, as distinct from a monolith with no internal boundaries at all,
what the software engineering literature separately names a Big Ball of Mud
(Brian Foote and Joseph Yoder, "Big Ball of Mud," in *Pattern Languages of
Program Design 4*, Addison-Wesley, 2000, originating from the Fourth
Conference on Pattern Languages of Programs, 1997, http://www.laputan.org/mud/mud.html,
verified 2026-08-02). Brown's argument, repeated across his conference
talks and writing, is that the opposite of microservices is not necessarily a
disorganized monolith, it can be a disciplined one, and the discipline is
the point.

The second thread is David Heinemeier Hansson's 2015 essay "The Majestic
Monolith," published on the Basecamp company blog. Hansson does not use the
word modular in the essay, but the argument he makes, that a single
deployable Rails application can scale to hundreds of thousands of methods
and a healthy team size without splitting into services, is the same
architectural claim under a different name, and "majestic monolith" is
listed in the frontmatter above as an alias because industry usage
frequently treats the two terms as synonyms (David Heinemeier Hansson, "The
Majestic Monolith," Signal v. Noise, 2015,
https://signalvnoise.com/the-majestic-monolith/, verified 2026-08-02).

The third thread is the retrospective one. Between roughly 2015 and 2020, a
wave of companies that had adopted microservices architectures published
engineering blog posts describing the operational cost of that decision, and
several of them, most visibly Segment, described consolidating services back
into a single deployable unit while explicitly preserving internal
separation. This is where "modular monolith" stopped being a contrarian
talking point and became a name for an established, chosen architecture
rather than a stage a system passes through before it graduates to
microservices (Alexandra Noonan, "Goodbye Microservices. From 100+ Problem
Children to 1 Superstar," originally Segment engineering blog, republished
by Twilio,
https://www.twilio.com/en-us/blog/developers/best-practices/goodbye-microservices/,
verified 2026-08-02).

A modular monolith is not a stepping stone by definition, though it is
frequently discussed as one. It is a distinct architectural choice with its
own name because the internal modularity is treated as a first class design
goal rather than an accident of how the codebase happened to grow.

## 2. Problem and context

A team is building a system that will run as one process, or one small
cluster of identical processes behind a load balancer, and deploys as one
unit. Over months or years of feature work, the codebase accumulates
functions and classes that call each other freely, because nothing stops
them. Eventually nobody can change the order module without touching the
inventory module, the inventory module without touching the shipping module,
and the shipping module without touching billing, because every import is
allowed and every team has, at some point, taken the shortest path through
someone else's code rather than through a defined interface. This is the Big
Ball of Mud, and it is the starting condition the modular monolith pattern
exists to prevent or to repair.

The context in which this problem is acute is a single process application
of real size, usually once a codebase passes somewhere in the range
of tens of thousands of lines and more than a handful of engineers working
in it concurrently. Below that size, the coordination cost of enforcing
module boundaries can exceed the cost of the disorder it prevents, and a
simpler layered architecture (see dimension 13) is often sufficient. Above
that size, without enforced boundaries, every change requires understanding
an ever growing share of the whole system, onboarding a new engineer takes
longer each quarter, and the team eventually proposes extracting services
not because the domain calls for network boundaries but because the code has
become impossible to reason about locally.

The modular monolith reframes the actual problem. The problem was never "we
are deployed as one unit," it was "our code has no internal boundaries." The
fix for a boundary problem is a boundary, and a boundary can be enforced
inside a single process at compile time or build time, without paying the
cost of a network hop, a serialization format, a service registry, or
distributed transaction semantics between every pair of collaborating
modules.

## 3. Forces

**Coupling versus deployment simplicity.** Splitting into physical services
forces a hard boundary because a network call cannot silently reach into
another module's internals, but it pays for that guarantee with the full
operational cost of a distributed system, described under dimension 4. A
modular monolith tries to get the coupling discipline without the
distribution cost, and the honest cost it accepts in exchange is that the
boundary is enforced by tooling and discipline rather than by physics, which
is a weaker guarantee, expanded under dimension 11.

**Team topology versus code topology.** Conway's Law observes that a
system's structure mirrors the communication structure of the organization
that built it (Melvin E. Conway, "How Do Committees Invent?," Datamation,
April 1968, http://www.melconway.com/Home/pdf/committees.pdf, verified
2026-08-02). A modular monolith lets module boundaries track team
boundaries without forcing team boundaries to also become deployment
boundaries, which is valuable when the organization is smaller or less
stable than the eventual service boundaries would demand.

**Latency and consistency versus isolation.** Inside one process, a call
between modules is a function call. It is synchronous by default, it can
participate in one database transaction, and it does not need to reason
about partial failure the way a call across a network does. This is a real
advantage this pattern favours over microservices, at the cost of the
isolation and independent failure domains that a genuine service boundary
would provide.

**Operability now versus optionality later.** A modular monolith deploys as
one artifact, so there is one thing to build, one thing to version, one
thing to roll back, and one process to observe, which is operationally
cheap. The pattern sacrifices the ability to scale, deploy, or choose a
runtime independently per module, which matters when different parts of a
system have genuinely different load profiles or genuinely different
non-functional requirements. This is the force microservices proponents
usually name first, and the modular monolith's answer is that this
optionality is not needed by most systems that adopted it, and where it is
needed for one specific module, that module alone can be extracted later
(dimension 14) precisely because the boundary already exists in the code.

**Cognitive load.** A developer working inside a well bounded module needs
to hold only that module's public interface and its own internals in their
head to make most changes, which is close to the cognitive load of working
in a small service. A developer working across module boundaries in a
modular monolith still benefits from a single IDE, a single test run, and a
single stack trace, which is strictly less cognitive load than the same
cross cutting change spread across several repositories and services.

## 4. Applicability and non-applicability

Reach for a modular monolith when the following hold together.

- The system deploys, and will likely continue to deploy, as a small number
  of homogeneous processes rather than needing independent scaling per
  feature area.
- The domain has identifiable subdomains, in the Domain-Driven Design sense,
  each with a defensible reason to exist as a unit of ownership (Eric Evans,
  *Domain-Driven Design. Tackling Complexity in the Heart of Software*,
  Addison-Wesley, 2003, Part IV).
- The team is small enough, or is organized loosely enough, that operating
  a fleet of independently deployable services would add coordination cost
  the team cannot yet absorb.
- The organization wants the option to extract a module into a real service
  later, without having designed for that outcome from day one at full
  distributed systems cost.
- Data consistency requirements favour transactions that a single database
  can provide, rather than requiring independent data stores per module.

Do **not** reach for a modular monolith when any of the following hold.

- Different parts of the system have radically different scaling profiles,
  for example a low traffic administrative back office sharing a deploy
  with a high traffic public checkout path, such that scaling the whole
  process to serve the busy part wastes resources serving the quiet part.
  This is the scaling force a genuine service split answers directly.
- Different parts of the system must run on genuinely different runtimes or
  languages, for example a machine learning inference path that needs a
  Python runtime embedded inside a system otherwise written in Go. A
  modular monolith is bound to one process and, in most implementations, one
  language runtime.
- Regulatory or organizational requirements demand that one part of the
  system be operated, deployed, and audited by a completely separate team
  with no shared release train, which argues for a real service boundary
  with its own deployment pipeline regardless of the technical coupling
  argument.
- The team enforcing the module boundaries has no tooling and no discipline
  to keep them enforced, in which case the codebase will regress to a Big
  Ball of Mud that merely has folders named after modules, which is worse
  than either extreme because it looks organized while being coupled.
- The system is genuinely small, a single team, a handful of thousand lines,
  early in its life, and does not yet know its own domain boundaries. Eric
  Evans and Martin Fowler both note that most successful microservice
  systems in the wild started as a monolith precisely because domain
  boundaries are usually discovered by building the thing, not designed
  correctly in advance (Martin Fowler, "MonolithFirst," martinfowler.com,
  2015, https://martinfowler.com/bliki/MonolithFirst.html, verified
  2026-08-02). A team that tries to draw hard module boundaries before the
  domain is understood usually draws them in the wrong place, and moving a
  boundary inside a monolith is a refactor, while moving a boundary between
  two already deployed services is a migration.

## 5. Structure

- **Module (or component).** A cohesive unit of the codebase, owning one
  subdomain's data model, business rules, and persistence. A module exposes
  a small, deliberate public interface, usually a set of functions,
  classes, or an explicit facade type, and keeps everything else private to
  the module.
- **Public interface (the module's contract).** The only surface through
  which other modules may interact with a given module. In languages with a
  package or module visibility system, this is enforced by the language
  itself, package private, internal, unexported. In languages without one,
  it is enforced by convention plus a static analysis tool that fails the
  build on a violation, expanded in dimension 8 and dimension 16.
- **Shared kernel (optional, used sparingly).** A small set of types, or a
  thin infrastructure layer, that every module is allowed to depend on
  because factoring it per module would create needless duplication,
  commonly things like a logging interface, a base entity type, or a
  request context. Evans names this pattern Shared Kernel and warns
  explicitly that it must stay small, because every type placed in it
  becomes a dependency every module carries (Eric Evans, *Domain-Driven
  Design. Tackling Complexity in the Heart of Software*, Addison-Wesley,
  2003, Part IV, "Shared Kernel").
- **Composition root.** The single place, usually the application's entry
  point or its dependency injection configuration, where modules are wired
  together. Modules do not construct each other's dependencies directly,
  they receive what they need through their public interface, and the
  composition root is the only code allowed to know about every module at
  once.
- **The single deployable artifact.** All modules ship together as one
  binary, one container image, or one process group, sharing one runtime,
  and in the common case one database, though dimension 8 covers the
  variant where each module owns its own schema inside a shared physical
  database.

A useful discipline for keeping the structure honest, borrowed from
hexagonal and clean architecture practice, see dimension 13, is that a
module's public interface should be defined in terms the module's own
domain, not in terms of another module's internal types, so that a module
can be tested, and eventually extracted, without dragging a second module's
internals along with it.

## 6. ASCII structure diagram

```
+---------------------------------------------------------------+
|                    single deployable process                  |
|                                                                 |
|   +--------------+   +--------------+   +--------------+       |
|   |   Ordering   |   |  Inventory   |   |   Billing    |       |
|   |--------------|   |--------------|   |--------------|       |
|   | public/      |   | public/      |   | public/      |       |
|   |  OrderApi    |   |  StockApi    |   |  BillingApi  |       |
|   | internal/    |   | internal/    |   | internal/    |       |
|   |  order model |   |  stock model |   |  invoice mdl |       |
|   |  repo, rules |   |  repo, rules |   |  repo, rules |       |
|   +------+-------+   +------+-------+   +------+-------+       |
|          |     calls only public APIs, never internal/  |      |
|          +-----------------+------------------+          |      |
|                             |                             |      |
|                     +-------+--------+                    |      |
|                     |  Shared Kernel |                    |      |
|                     |  (types, log,  |                    |      |
|                     |   request ctx) |                    |      |
|                     +-------+--------+                    |      |
|                             |                             |      |
|                     +-------+--------+                    |      |
|                     | Composition Rt |  wires all modules  |      |
|                     +----------------+                    |      |
+---------------------------------------------------------------+
                             |
                     one process boundary
                             |
                    +--------+--------+
                    |  one database   |
                    |  (schema per    |
                    |   module,       |
                    |   optionally)   |
                    +-----------------+
```

The static analysis boundary is drawn where `internal/` folders meet.
Nothing outside a module's own folder may import from another module's
`internal/` path, and the build fails if it tries to. The only cross module
traffic is through the `public/` API, and the only code that references
every module by name is the composition root.

## 7. Dynamics

```
Client request arrives at the process
   |
   v
Composition root has already wired:
   OrderApi   -> depends on -> StockApi (public interface only)
   OrderApi   -> depends on -> BillingApi (public interface only)
   |
   v
HTTP handler in Ordering module receives the request
   |
   v
Ordering module calls StockApi.Reserve(sku, qty)
   |                     (in-process function call, one stack,
   |                      no serialization, no network hop)
   v
Inventory module executes its own domain rules,
writes to its own tables inside the shared database transaction,
returns a typed result across the OrderApi/StockApi boundary
   |
   v
Ordering module calls BillingApi.Authorize(orderId, amount)
   |
   v
Billing module executes its own domain rules,
participates in the SAME database transaction as Ordering
and Inventory did (because it is one process, one connection,
one transaction scope)
   |
   v
Ordering module commits the transaction once, atomically,
across data that three separate modules touched
   |
   v
Response returned to client
```

The dynamic that most distinguishes this pattern from a microservices
equivalent of the same flow is the transaction step near the bottom.
Because Ordering, Inventory, and Billing are modules inside one process
sharing one database connection, the whole operation can be wrapped in a
single ACID transaction, so a failure partway through rolls back cleanly. A
microservices version of the identical flow would need a saga, a
compensating transaction protocol, or eventual consistency, because no
single transaction can span three separately deployed services with
separate databases, which is why the comparison is formalized in dimension
12.

## 8. Implementation variants

**Language-enforced module boundaries.** In languages with a real
visibility system at the package or module level, the module boundary is
enforced by the compiler. Java packages using package private visibility,
Kotlin's `internal` modifier scoped to a Gradle module, Rust's
`pub(crate)` and module tree, and Go's convention of an `internal/`
directory, whose contents the Go toolchain refuses to let any package
outside that directory's parent tree import, are all compiler level
enforcement (the Go `internal` directory rule is documented in the Go 1.4
release notes, https://go.dev/doc/go1.4#internalpackages, verified
2026-08-02). This is the strongest variant because a developer cannot
accidentally violate the boundary, the code will not compile.

**Static-analysis-enforced module boundaries.** In languages without strong
built in module visibility across the relevant granularity, most commonly
Ruby, Python, and JavaScript or TypeScript at the application module
level rather than the file module level, the boundary is defined by
convention, usually a folder per module with a declared public entry
point, and enforced by a dependency checking tool that runs in CI and
fails the build on a violation. Shopify's Packwerk is the most documented
example of this variant for Ruby, statically parsing the codebase's
constant references and failing a pull request when a module reaches into
another module's private namespace (Shopify Engineering, "Deconstructing
the Monolith," shopify.engineering, https://shopify.engineering/shopify-monolith,
verified 2026-08-02). The trade-off named directly in dimension 11 is that
this variant is only as strong as the tool's coverage and as consistently
as the team runs it.

**Database-per-module inside one physical database.** Each module owns a
separate schema, or a separate set of tables prefixed by module name,
inside one physical database instance. Cross module data access happens
only through the owning module's public API, never through a direct SQL
join against another module's tables. This variant preserves single
process transactional guarantees, dimension 7, while still preventing the
data layer coupling that is usually the deepest and hardest coupling to
unwind later, the specific coupling Fowler calls out as the reason later
decomposition usually fails, in the MonolithFirst article cited under
dimension 4.

**Shared database, no schema separation.** The weakest variant, where
modules are organized in application code but all read and write a shared
set of tables without ownership. This is common in codebases that adopted
"modular monolith" as a naming convention after the fact without enforcing
data ownership, and it is the variant most likely to regress toward the
Big Ball of Mud, because the database layer, which is usually the hardest
layer to refactor, was never actually modularized.

**Modular monolith with an internal message bus.** Modules communicate
through an in-process event bus or command dispatcher rather than direct
function calls, still inside one process and usually still one
transaction, but with the calling convention of an event-driven system,
cross reference dimension 13. This variant is chosen when a team wants
the loose coupling communication style of event-driven architecture and
the option to move a module's event handling out to a real message broker
later, without paying the network cost until that extraction actually
happens.

## 9. Known production uses

**Shopify.** Shopify's core commerce platform is a large Ruby on Rails
application, and Shopify has been explicit in public engineering writing
that they deliberately keep it as one deployable Rails monolith rather
than splitting it into services, organizing the codebase into internally
enforced components with public interfaces, and building the Packwerk tool
specifically to enforce those boundaries at the static analysis level
described in dimension 8. The team states plainly, "We are very deliberate
about when to split functionality out into separate services, and we only
do it for good reasons" (Shopify Engineering, "Deconstructing the
Monolith," shopify.engineering, https://shopify.engineering/shopify-monolith,
verified 2026-08-02).

**Basecamp.** Basecamp, the flagship product of the company of the same
name, formerly 37signals, has run as a single deployable Ruby on Rails
application since 2003, and its creator David Heinemeier Hansson has
published the resulting scale figures directly, "200 controllers with a
total of 900 methods" and "190 classes with some 1,473 methods," maintained
by a team of roughly a dozen programmers across web, iOS, Android, and
desktop clients, as an explicit counter-argument to the claim that a
monolith cannot scale past a small team (David Heinemeier Hansson, "The
Majestic Monolith," Signal v. Noise, 2015,
https://signalvnoise.com/the-majestic-monolith/, verified 2026-08-02).

**Segment.** Segment operated more than 140 independently deployed
microservices, one per third party destination integration, and
documented publicly that the operational overhead of that many
independently deployed units, differing dependency versions, and per
service deployment pipelines became a larger cost than the isolation
benefit was worth for their workload, consolidating the destinations into
a single monolithic service with per destination logic organized
internally as modules, and reporting that the number of shared library
improvements the team was able to ship rose from 32 in the year before
consolidation to 46 in the year after (Alexandra Noonan, "Goodbye
Microservices. From 100+ Problem Children to 1 Superstar," originally
Segment engineering blog, hosted by Twilio,
https://www.twilio.com/en-us/blog/developers/best-practices/goodbye-microservices/,
verified 2026-08-02).

## 10. Consequences

Positive consequences.

- A single deployment pipeline, a single build, and a single runtime to
  operate, monitor, and roll back, which reduces the operational surface
  area relative to an equivalent system split into independently deployed
  services.
- In-process function calls between modules avoid network latency, retry
  logic, timeout tuning, and the serialization overhead a service boundary
  requires, which lowers real cost for chatty cross module interactions.
- A single database connection scope allows genuine ACID transactions
  across module boundaries when the domain needs strong consistency,
  dimension 7, which a distributed system can only approximate with a
  saga pattern and eventual consistency.
- Refactoring a module boundary, moving a piece of logic from one module to
  another, or merging two modules that turned out to be one subdomain, is a
  code change reviewed in one pull request, not a cross team migration
  spanning multiple services and their contracts.
- A developer can step through the entire request path in one debugger
  session, and one stack trace shows the whole call chain, which is
  noticeably easier to reason about than a distributed trace spanning
  several processes.
- The architecture preserves the option to extract any one module into a
  real service later, dimension 14, specifically because the module
  boundary, the public interface, and the data ownership already exist in
  the code, which is the hard part of a service extraction.

Negative consequences.

- The module boundary is enforced by tooling and discipline rather than by
  the operating system's process isolation, so a determined or careless
  change can violate it unless the enforcement tool is run consistently
  and its coverage is genuinely complete, expanded under dimension 11.
- Every module shares the same runtime, so a memory leak, an unbounded
  loop, or a crash in one module can degrade or take down the entire
  process, unlike a service architecture where a failing service can be
  isolated and its blast radius contained.
- All modules must scale together, because they deploy together, so a
  module with a genuinely different load profile cannot be scaled
  independently without over-provisioning the whole process to match its
  peak.
- All modules are, in most implementations, bound to one language runtime
  and one major dependency set, which forecloses the option to write one
  module in a different language suited to its problem, for example a
  numerically heavy module that would benefit from a different runtime.
- Team autonomy is bounded by the shared build and shared release train.
  Multiple teams working in the same monolith must coordinate on
  dependency upgrades, on the deployment schedule, and on any shared
  kernel change, in a way that fully independent services would not
  require.

## 11. Failure modes and misuse

**Symptom.** A dependency graph tool, run retroactively over what was
called a modular monolith, shows cycles between modules that were supposed
to be a strict hierarchy, or a single "utils" or "shared" module that
every other module imports and that has grown to contain a large fraction
of the system's actual logic.
**Cause.** The boundary erodes silently because nothing enforces it. A
team draws module folders, agrees informally that Module A should not
import Module B's internals, and never wires a static analysis tool or a
compiler level boundary into the build. Within a few release cycles, a
deadline pressures someone into a shortcut import, code review misses it
because reviewers are not systematically checking for it.
**Fix.** Wire an enforcement mechanism, a compiler level visibility rule or
a static analysis rule per dimension 8, into CI before adding a second
module, treat any red build from that check as a build breaker on the same
footing as a failing test, and periodically re-run the dependency graph
tool as an audit rather than assuming the CI check alone will surface
every violation.

**Symptom.** Extracting any single module later, dimension 14, turns out to
require a data migration touching most of the schema, because the tables
were never actually owned by a single module.
**Cause.** Data ownership was never actually modularized. A team enforces
the application code boundary but leaves the database as one
undifferentiated schema, with modules freely joining across each other's
tables directly in SQL because it is faster to write a join than to call
another module's public API and assemble the result in application code.
**Fix.** Adopt the database-per-module variant from dimension 8
incrementally, one module at a time, replacing a cross module join with a
call to the owning module's public API and an in-application join,
starting with the module least entangled with the rest of the schema.

**Symptom.** The shared kernel module has more incoming dependencies than
any domain module, and a change to it requires touching or at least
recompiling every module in the system.
**Cause.** The shared kernel grows without limit. A type that genuinely
needs to be shared, for example a `Money` value type or a `RequestContext`,
is placed in the shared kernel, and over time every convenient type gets
added to it because adding to the shared kernel is easier than defining a
proper per-module contract.
**Fix.** Treat every addition to the shared kernel as a design decision
requiring the same review as a new module boundary, and periodically audit
the shared kernel's own dependency count as an observability signal,
dimension 16, moving types back out to the one module that actually owns
them when a type is used by only one caller.

**Symptom.** After extraction of a module into its own service, a
proliferation of synchronous cross service calls appears at the exact call
sites that used to be a local in-process function call and a shared
database transaction, followed by a production incident the first time one
of those calls times out.
**Cause.** Premature extraction of a module that was never actually
cohesive. A team, encouraged by the promise that a module can be extracted
into a service later, extracts a module before confirming that its data
and its transactional needs were actually independent of its neighbours.
**Fix.** Follow the extraction checklist in dimension 14 in order,
particularly confirming the public interface has been stable and the
module already owns its own data before extraction, and revert the
extraction back into the monolith if the resulting call pattern shows the
module was never independent, which is a legitimate and reversible
decision, not a failure.

**Symptom.** A single feature change routinely touches three or four
"modules" in the same pull request.
**Cause.** Using the module boundary as a substitute for actual domain
analysis. A team draws module boundaries along technical layers, for
example "controllers," "services," "repositories," rather than along
subdomains, which produces a system that looks modular in its folder
structure but is in fact a layered architecture with extra folders.
**Fix.** Re-draw module boundaries along business capability rather than
technical role, following the refactoring path in dimension 14 starting
from a domain model rather than from the existing folder names, since the
technical-layer split is the specific misuse this pattern's proponents
draw most sharply against an ordinary layered architecture, dimension 13.

## 12. Trade-off matrix

| Force | Modular Monolith | Big Ball of Mud, no enforced boundaries | Microservices | Layered Architecture only |
|---|---|---|---|---|
| Deployment simplicity | High, one artifact | High, one artifact, but fragile to change | Low, N independently deployed services | High, one artifact |
| Coupling discipline | Enforced at build or compile time, per module | None, coupling grows unchecked | Enforced by the network boundary itself | Enforced only between layers, not between features |
| Cross-boundary transactions | Native ACID across modules in one DB | Native, but boundaries are meaningless anyway | Requires sagas or eventual consistency | Native, no feature-level boundary exists to cross |
| Independent scaling per feature | Not possible, whole process scales together | Not possible | Native, per service | Not possible |
| Independent team deployment schedule | Shared release train | Shared release train | Independent per service | Shared release train |
| Blast radius of a crash | Whole process, isolated only by module discipline in code, not by the OS | Whole process, no isolation at all | Contained to the failing service | Whole process |
| Cost to reorganize a boundary | Low, a code refactor reviewed in one PR | Low in theory, high in practice because nothing marks where boundaries should be | High, a cross-service migration with contract changes | Moderate, layer boundaries rarely track feature boundaries |
| Cognitive load to understand one feature | Moderate, confined to one module plus its declared dependencies | High, unconstrained, could be anywhere | Low within one service, high across the distributed trace | High, spread across every layer for every feature |
| Onboarding a new engineer | Moderate, module structure gives a map | High, no map exists | Moderate per service, high for the system as a whole | High, must learn every layer to change anything |

## 13. Related and incompatible patterns

**Layered Architecture.** A modular monolith is frequently confused with a
layered architecture because both live inside one deployable process, but
they cut the codebase on different axes. Layered architecture organizes
code by technical role, presentation, business logic, data access, so that
a change to one feature crosses every layer. A modular monolith organizes
code by business capability, so that a change to one feature usually stays
inside one module. The two are not mutually exclusive, a well built module
inside a modular monolith commonly has its own small internal layering,
and dimension 11's last failure mode is exactly what happens when a team
mistakes one for the other.

**Hexagonal Architecture and Clean Architecture.** Both of these patterns
describe how to structure the inside of a single bounded unit of code so
that its domain logic does not depend on its infrastructure. A modular
monolith commonly uses hexagonal or clean architecture as the internal
shape of each individual module, so that each module's domain logic is
independent of, for example, which database driver or which web framework
the whole process happens to use. The patterns compose at different
granularities, hexagonal or clean architecture inside a module, modular
monolith across the whole process.

**Microkernel Architecture.** A microkernel separates a small stable core
from plug-in modules that extend it, and the core usually knows nothing
about the specific plug-ins. A modular monolith's modules are usually
peers, not plug-ins to a central core, and the composition root, unlike a
microkernel, is allowed to know about every module by name. The two
patterns can combine when a modular monolith's shared kernel is treated as
a minimal microkernel core and domain modules are treated as its plug-ins,
but this is a specific design choice, not the default shape of either
pattern.

**Event-Driven Architecture.** As covered in dimension 8's message bus
variant, a modular monolith can adopt an internal event bus as its
inter-module communication style without leaving the single process
boundary, which is a common intermediate step for teams planning an
eventual extraction to a real event-driven microservices system.

**Domain-Driven Design's Bounded Context.** A module in a modular monolith
is, in the common and recommended case, implemented as one bounded context
in the Domain-Driven Design sense, described under dimension 5's
structure. The two are not the same thing, bounded context is a modeling
concept about where a model's meaning changes, and module is the code
level unit that implements that boundary. A modular monolith with module
boundaries that do not correspond to bounded contexts is the technical
layering misuse described in dimension 11.

**Microservices Architecture, incompatible in practice, not in theory.** A
system is either deployed as one process or as several. A given piece of
code cannot simultaneously be a module inside a modular monolith and an
independently deployed microservice, the two are alternative endpoints for
the same domain code. They are not marked as formally incompatible in the
frontmatter because a real system commonly contains both, a modular
monolith as the majority of the codebase with one or two genuinely
independent services extracted for the specific reasons named in
dimension 4, which is the pragmatic middle ground most of the production
examples in dimension 9 actually occupy.

## 14. Refactoring path in and out

Introducing modularity into an existing unmodularized monolith.

1. Draw the candidate module boundaries first, on paper or in a diagram,
   using the domain's own vocabulary, not the existing folder structure.
   This step is modeling, not coding, and it is where DDD's event
   storming or a similar domain mapping technique earns its keep.
2. Pick the module with the fewest existing cross-cutting dependencies as
   the first target, because it will be the cheapest to extract and will
   validate the tooling choice before harder modules are attempted.
3. Move that module's code into its own package or folder, including its
   own data access code, and identify every call site outside the new
   folder that currently reaches into what is about to become its
   internals.
4. Design a small public interface for the module, a facade type or a set
   of exported functions, and rewrite every external call site to go
   through that interface instead of the module's internals.
5. Introduce the enforcement mechanism for this module first, either a
   language level visibility boundary or a static analysis rule,
   dimension 8, and get it passing in CI before moving to the next
   module, so that the first module cannot silently regress while later
   modules are still being carved out.
6. Repeat for the next module, using the growing set of enforced module
   boundaries as a forcing function, each new module makes the remaining
   unmodularized code smaller and easier to see clearly.
7. Address data ownership last for each module, moving from "the module's
   code is separate but reads shared tables" to "the module owns its
   tables," because untangling shared table access is usually the hardest
   step and benefits from the code level boundary already being stable.

Extracting a module into a genuine microservice.

1. Confirm the module's public interface has been stable for a
   long stretch, meaning other modules only call it through the
   interface and the interface has not needed frequent changes, which is
   the strongest available evidence the boundary is drawn correctly.
2. Confirm the module already owns its own data, per the database-per-module
   variant in dimension 8, if it does not, do the data ownership work
   inside the monolith first, because doing it during an extraction
   multiplies the risk.
3. Replace the in-process calls to the module's public interface with a
   client that speaks over the network, initially perhaps calling into
   the still in-process module through the same interface signature, to
   isolate the interface change from the deployment change.
4. Stand up the module as its own deployable service, wire the client from
   step 3 to call it over the network instead of in-process, and run both
   paths in parallel behind a feature flag if the risk profile warrants
   it.
5. Decide the consistency model for what was previously a shared
   transaction, dimension 7, this commonly means introducing a saga or
   accepting eventual consistency for the specific cross module operations
   that used to share a transaction, and this decision should be made
   explicitly, not discovered in an incident.
6. Remove the module's code from the monolith's deployable artifact once
   the service is confirmed stable in production, and update the
   composition root to remove the now absent module.

## 15. Testing and verification

A modular monolith makes one class of test dramatically easier and does not
change the difficulty of another class.

Testing gets easier at the module boundary. Because each module exposes a
small public interface, a unit test suite for one module can construct
that module in isolation, using a fake or in-memory implementation of any
dependency it receives from another module's public interface, without
needing to stand up the rest of the system. This is a direct benefit of
the Dependency Inversion discipline described in dimension 5's composition
root, a module that depends on interfaces rather than concrete types from
other modules is a module that can be tested with a test double standing
in for those interfaces, the same testing benefit hexagonal architecture
provides for infrastructure dependencies, here applied module-to-module.

Testing the whole system end to end is not clearly easier or harder
than in an unmodularized monolith, because the whole system still runs as
one process and can be exercised with one integration test suite against
one running instance, which is itself an advantage over microservices,
where an end to end test usually requires standing up several services
together.

The specific verification unique to this pattern is boundary verification,
confirming that the module boundaries drawn in the design are actually
respected in the code. This is not a runtime test, it is a static check,
run either as a compiler error, the language-enforced variant, or as a
dedicated CI step, the Packwerk-style variant described in dimension 8,
and it should run on every pull request rather than periodically, because
the entire value of the pattern depends on the boundary never silently
eroding, which is the failure mode described first under dimension 11.

## 16. Observability signals

Because a modular monolith runs as one process, most conventional
observability, request latency, error rate, resource utilization, applies
at the process level exactly as it would for any single process system,
and does not by itself distinguish a healthy modular monolith from an
unmodularized one.

The observability signals specific to this pattern are structural rather
than runtime, and they should be measured as part of the build or as a
periodic architecture review rather than as a production metric.

- **Boundary violation count.** The number of failures reported by the
  static analysis or compiler level module boundary check, tracked over
  time. A healthy system holds this at zero on the main branch, a rising
  count of suppressed or waived violations is the earliest observable
  sign of the erosion failure mode described under dimension 11.
- **Fan-in on the shared kernel.** The number of modules that depend on
  the shared kernel, and more importantly the rate of growth of the
  shared kernel's own surface area, since an ever growing shared kernel is
  the second failure mode named under dimension 11.
- **Cross-module call graph shape.** A dependency graph between modules,
  generated from the same tooling that enforces the boundary, should form
  a directed acyclic graph, or a graph with a small, deliberate set of
  cycles that the team has explicitly accepted. An unexpected cycle
  appearing in this graph is a direct, usable signal that two modules
  have become mutually dependent, which is the specific condition that
  makes future extraction of either module impossible without extracting
  both together.
- **Per-module test isolation.** Whether a given module's test suite can
  run without booting the rest of the application. A module whose tests
  require the full application context to pass is a module whose
  boundary, regardless of what the static analysis tool reports, has not
  actually achieved behavioural independence.
- **Time to first deploy for a new engineer's first module-scoped
  change.** An informal but genuinely useful signal, if module boundaries
  are real, a new engineer's first change, if scoped to one module,
  should not require understanding the whole system, and the time this
  takes is a proxy for whether the boundaries are serving their stated
  purpose.

## 17. Security and privacy implications

A modular monolith does not, by itself, provide the process level security
isolation that a genuine service boundary provides. All modules share one
process's memory space, one set of environment variables, one set of
credentials available to the process, and one attack surface at the
operating system level. A vulnerability that achieves arbitrary code
execution inside one module's code, for example an insecure
deserialization bug in the Billing module, has the same practical blast
radius as a vulnerability anywhere else in the process, because the module
boundary is a code organization construct, not a memory protection or
privilege boundary, which is a meaningfully different security posture
from a microservices architecture where a compromised service can be, and
in a well designed system is, isolated with its own credentials, its own
network policy, and its own least privilege access to data.

This has a direct consequence for data handling. If one module handles
sensitive data, for example payment details or health information,
placing it inside a modular monolith means that data's confidentiality now
depends on the correctness of every other module in the same process,
because a bug in an unrelated module that achieves memory disclosure or
code execution can, in the worst case, read anything the process can
read, not only the data the vulnerable module owns. A team choosing a
modular monolith for a system that includes a genuinely high sensitivity
subdomain should weigh this specifically, and the honest architectural
answer, where the regulatory or risk profile demands it, is frequently to
keep the bulk of the system as a modular monolith while extracting the
specific high sensitivity module into its own service with its own
credential scope, which is exactly the mixed architecture named as the
practical middle ground under dimension 13.

The module boundary does, positively, reduce the accidental exposure
surface within the process. A well enforced public interface means one
module's code cannot accidentally read another module's database rows
through a stray join, cannot accidentally log another module's internal
state because it never had a reference to it, and cannot accidentally
depend on another module's implementation detail in a way that leaks
sensitive data through an unrelated code path. This is a defense against
accident and against the ordinary erosion of engineering discipline over
time, not a defense against a determined attacker who has already achieved
code execution inside the process.

## 18. References

- Simon Brown, conference talks and *Software Architecture for
  Developers*, self published, referenced for the popularization of the
  term "modular monolith" as distinct from an unstructured monolith, talk
  recordings and slide decks are distributed across multiple conference
  archives rather than one canonical URL, cited here as the widely
  credited origin of the term in industry usage.
- David Heinemeier Hansson, "The Majestic Monolith," Signal v. Noise,
  2015. https://signalvnoise.com/the-majestic-monolith/, verified
  2026-08-02.
- Martin Fowler, "MonolithFirst," martinfowler.com, 2015.
  https://martinfowler.com/bliki/MonolithFirst.html, verified 2026-08-02.
- Shopify Engineering, "Deconstructing the Monolith," shopify.engineering.
  https://shopify.engineering/shopify-monolith, verified 2026-08-02.
- Alexandra Noonan, "Goodbye Microservices. From 100+ Problem Children to
  1 Superstar," originally Segment engineering blog, hosted by Twilio.
  https://www.twilio.com/en-us/blog/developers/best-practices/goodbye-microservices/,
  verified 2026-08-02.
- Eric Evans, *Domain-Driven Design. Tackling Complexity in the Heart of
  Software*, Addison-Wesley, 2003, Part IV, chapters on Bounded Context
  and Shared Kernel.
- Brian Foote and Joseph Yoder, "Big Ball of Mud," in *Pattern Languages
  of Program Design 4*, Addison-Wesley, 2000, originating from the Fourth
  Conference on Pattern Languages of Programs, 1997.
  http://www.laputan.org/mud/mud.html, verified 2026-08-02.
- Melvin E. Conway, "How Do Committees Invent?," Datamation, April 1968.
  http://www.melconway.com/Home/pdf/committees.pdf, verified 2026-08-02.
- The Go Authors, "Go 1.4 Release Notes," golang.org, on the `internal`
  package directory convention enforced by the toolchain.
  https://go.dev/doc/go1.4#internalpackages, verified 2026-08-02.
- Wikipedia, "Monolithic application," listing modular monolith as one of
  the recognized architectural patterns applied to monolithic systems,
  consulted for the general definition, not for any specific factual
  claim attributed to a named source above.
  https://en.wikipedia.org/wiki/Monolithic_application, verified
  2026-08-02.

## Code examples

The pattern is demonstrated the same way in each language. A small
composition root wires three modules together, each module exposes only a
narrow public surface, and a cross module call goes through that surface
rather than through the other module's internals.

### TypeScript

```typescript
// In a real project, each comment marks a separate file under its own
// module folder. inventory/public.ts is the ONLY inventory export other
// modules may import from.
export interface StockApi {
  reserve(sku: string, qty: number): boolean;
}

// inventory/internal.ts. never imported outside the inventory folder
class InMemoryStock implements StockApi {
  private levels = new Map<string, number>([["WIDGET", 10]]);
  reserve(sku: string, qty: number): boolean {
    const have = this.levels.get(sku) ?? 0;
    if (have < qty) return false;
    this.levels.set(sku, have - qty);
    return true;
  }
}
function newStockApi(): StockApi {
  return new InMemoryStock();
}

// ordering/public.ts. depends only on inventory's public StockApi type
class OrderApi {
  constructor(private readonly stock: StockApi) {}
  placeOrder(sku: string, qty: number): string {
    if (!this.stock.reserve(sku, qty)) {
      throw new Error("insufficient stock");
    }
    return `order-${sku}-${qty}`;
  }
}

// composition-root.ts. the only file that knows both modules exist
function main(): void {
  const stock = newStockApi();
  const orders = new OrderApi(stock);
  console.log(orders.placeOrder("WIDGET", 3));
}
main();
```

Compiled and run with `npx tsc` targeting a CommonJS module and executed
under Node, the compile succeeded with no diagnostics and the program
printed `order-WIDGET-3`.

### Python

```python
# inventory.py. module owns its own state, exposes one function
_levels = {"WIDGET": 10}


def reserve(sku: str, qty: int) -> bool:
    have = _levels.get(sku, 0)
    if have < qty:
        return False
    _levels[sku] = have - qty
    return True


# ordering.py. depends on inventory only through reserve()
import inventory


def place_order(sku: str, qty: int) -> str:
    if not inventory.reserve(sku, qty):
        raise ValueError("insufficient stock")
    return f"order-{sku}-{qty}"


# composition_root.py
import ordering

if __name__ == "__main__":
    print(ordering.place_order("WIDGET", 3))
```

Run with `python3 composition_root.py`, printed `order-WIDGET-3`.

### Go

```go
package main

import "fmt"

// inventory package exported surface is the only thing another
// package may call. lowercase fields below are unexported and, in a
// real multi-file layout, would live under an internal/ directory the
// Go toolchain refuses to let other module trees import at all.

type stock struct {
	levels map[string]int
}

func newStock() *stock {
	return &stock{levels: map[string]int{"WIDGET": 10}}
}

func (s *stock) Reserve(sku string, qty int) bool {
	have := s.levels[sku]
	if have < qty {
		return false
	}
	s.levels[sku] = have - qty
	return true
}

type orderApi struct {
	stock *stock
}

func newOrderApi(s *stock) *orderApi {
	return &orderApi{stock: s}
}

func (o *orderApi) PlaceOrder(sku string, qty int) (string, error) {
	if !o.stock.Reserve(sku, qty) {
		return "", fmt.Errorf("insufficient stock")
	}
	return fmt.Sprintf("order-%s-%d", sku, qty), nil
}

func main() {
	s := newStock()
	orders := newOrderApi(s)
	id, err := orders.PlaceOrder("WIDGET", 3)
	if err != nil {
		panic(err)
	}
	fmt.Println(id)
}
```

Run with `go run main.go`, printed `order-WIDGET-3`. In a real project the
`stock` and `orderApi` types would sit in separate packages under
`internal/inventory` and `internal/ordering`, and the Go compiler itself
would refuse to build any package outside that tree that tried to import
`internal/inventory`'s unexported identifiers, which is the language
level enforcement variant described in dimension 8.

A fourth language, Swift, was considered but omitted for this entry. The
pattern's module boundary mechanics map most directly onto Swift's own
module and `internal`/`fileprivate` access levels in a way that would
largely restate the Go example's enforcement story without adding a
distinct implementation technique, so the three languages above were kept
as the ones where the pattern's variants, compiler enforced in Go,
convention plus tooling enforced in TypeScript and Python, are genuinely
different in kind.
