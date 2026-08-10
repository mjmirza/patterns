---
name: Common Closure Principle
slug: common-closure-principle
family: 04-principles-and-laws
category: Principle
aliases: [CCP, Package Closure Principle, Component Closure Principle]
first_described: "Robert C. Martin, 1996, \"Granularity\", C++ Report; restated as CCP in Agile Software Development: Principles, Patterns, and Practices, 2002, and in Clean Architecture, 2018"
maturity: canonical
related: [release-reuse-equivalence, common-reuse-principle, single-responsibility-principle, open-closed-principle, separation-of-concerns, dependency-inversion-principle]
incompatible_with: []
verified: 2026-08-10
---

# Common Closure Principle

## 1. Name, aliases, and lineage

The canonical name in this catalog is Common Closure Principle, abbreviated
CCP everywhere in the literature that discusses it. Robert C. Martin
introduced it under this exact name in "Granularity," the fifth of his
Engineering Notebook columns for The C++ Report, published in the
November/December 1996 issue by SIGS Publications Group. A PDF mirror of
that column carries the original wording verbatim (Martin, "Granularity,"
C++ Report, Nov/Dec 1996, PDF mirror, verified 2026-08-10).
https://condor.depaul.edu/dmumaugh/OOT/Design-Principles/granularity.pdf
The column states the principle in capitals, its house style for a
definition, as "THE CLASSES IN A PACKAGE SHOULD BE CLOSED TOGETHER AGAINST
THE SAME KINDS OF CHANGES. A CHANGE THAT AFFECTS A PACKAGE AFFECTS ALL THE
CLASSES IN THAT PACKAGE." That 1996 column also introduced the CCP's two
siblings in the same breath, the Reuse/Release Equivalence Principle and the
Common Reuse Principle, and named all three the granularity principles.

Martin restated CCP six years later as one of three package cohesion
principles in Chapter 28 of *Agile Software Development, Principles,
Patterns, and Practices* (Prentice Hall, 2002), a chapter mapping confirmed
by the book's own table of contents listing (Prentice Hall / Alan Apt Series
listing, verified 2026-08-10).
https://www.amazon.com/Software-Development-Principles-Patterns-Practices/dp/0135974445
Sixteen years after that he restated it a third time, essentially unchanged
in substance though sharpened in wording, in Chapter 13, "Component
Cohesion," of *Clean Architecture, A Craftsman's Guide to Software Structure
and Design* (Prentice Hall, 2018). A secondary source that walks that
chapter section by section quotes the 2018 phrasing directly, "Gather into
components those classes that change for the same reasons at the same time.
Separate into different components those classes that change at different
times and for different reasons," and explicitly draws the parallel Martin
draws in the book, that CCP is the Single Responsibility Principle
relocated from the class level to the component level (Lets Code Them Up,
"Clean Architecture Chapter 13, Component Cohesion," verified 2026-08-10).
https://www.letscodethemup.com/clean-architecture-chapter-13-component-cohesion/
The chapter's existence and its three-principle structure, REP, CCP, CRP,
under the collective name component cohesion principles, is independently
corroborated by a second summary of the same chapter (GitHub Gist summary
of Clean Architecture, verified 2026-08-10).
https://gist.github.com/markstachowski/a7fab6397ee1a3488fa79c43cf1bd079

No source contests the attribution or the wording across the three
restatements. The word "package" in the 1996 column and the word
"component" in the 2018 book name the same unit, a deployable, releasable
group of classes or modules, and this entry uses "component" as the modern
default term while noting that "module," "package," and "assembly" are the
same unit under a different language's vocabulary, a Java package, a Python
package, a Rust crate, a Go module, a .NET assembly, an npm package.

## 2. Problem and context

A codebase reaches the size where a single flat namespace of classes stops
being a unit anyone can reason about, and the team splits it into smaller
compilation and deployment units, packages, modules, crates, whatever the
platform calls them. That split creates a new design decision that did not
exist when everything lived in one namespace, which classes go in which
unit. Get that decision wrong and every subsequent requirement change
becomes a scavenger hunt across units that were never meant to move
together.

The concrete failure looks like this. A product manager asks for a change
to how tax is calculated on an invoice. The engineer who picks up the
ticket finds that the tax rate lives in a `Rates` module, the tax
calculation logic lives in a `Calculations` module organized by
mathematical operation rather than by business concern, the tax line item
rendering lives in a `Formatting` module, and the tax-exempt customer flag
lives in a `Customers` module that half a dozen unrelated features also
touch. One requirement, five modules, five sets of tests to rerun, five
pull requests to review, and a release train that now has to synchronize
five teams because none of those modules can ship the fix alone without
carrying unrelated in-flight changes from the other four.

Contrast that with a codebase organized by axis of change. If tax handling
sits in one `TaxCalculation` module, the same requirement touches one
module, and every other module is provably unaffected because nothing in
them imports from `TaxCalculation` for reasons connected to this change.
The problem CCP names is exactly this, that grouping classes by reason for
change is a design decision as consequential as grouping methods inside a
class, and that most teams make the grouping decision by accident,
following organizational conventions such as grouping by architectural
layer, alphabetically, or by the type of object, all entities together, all
services together, rather than by the axis along which requirements
actually arrive.

The context in which CCP becomes the load-bearing decision is a system with
more than one deployable or releasable unit, where a change to a
requirement should be assessable as touching some measurable number of
units, and the answer matters to real people, a release manager scheduling
a deploy window, a reviewer who has to context-switch across unrelated
code, a CI pipeline that revalidates every unit that changed. In a
single-file script or a small application with no internal module
boundaries, CCP has nothing to say, because there is no boundary to draw
yet.

## 3. Forces

- **Change locality against uniform organization.** A codebase organized
  uniformly, by object type, by architectural layer, by alphabet, is easy
  to browse and predict where a class lives. CCP asks the organizer to give
  that predictability up in favor of grouping by an axis that is invisible
  in the code itself, the historical and expected future reason a class
  changes. The two forces pull directly against each other, and CCP takes
  the side of change locality because Martin's argument is that
  maintainability outranks browsability once a system has more than a
  handful of components.
- **Package count against package size.** Taken to an extreme, CCP argues
  for one component per distinct reason for change, which can mean dozens
  or hundreds of very small components. Each additional component is a
  build unit, a version to track, a dependency edge to manage, and a
  cognitive unit for a newcomer to learn. CCP's sibling principle, the
  Common Reuse Principle, pulls in the opposite direction by penalizing
  components that are too fine-grained for a consumer that wants only part
  of what a component offers. The two principles are in Martin's own words
  in tension by design, and a team is expected to sit somewhere on the
  spectrum between them rather than maximize either one.
- **Stability against volatility.** A component built for CCP-driven
  change locality is, almost by definition, a volatile component, one
  expected to change often because a whole class of requirement lands
  there. Volatile components should sit low in a dependency graph, depended
  upon by little, per the Stable Dependencies Principle. CCP tells you
  where to draw a boundary, not where that boundary should sit in the
  dependency graph, and getting the second question wrong, a volatile,
  CCP-correct component with many stable dependents, recreates the exact
  fragility CCP was meant to prevent.
- **Team topology against technical grouping.** A component boundary drawn
  along reason-for-change often lines up with a team boundary, because a
  team that owns a business capability is also the team that receives the
  requirements that change it. When the org chart and the CCP boundary
  disagree, either the org chart is fighting the codebase, a Conway's Law
  friction, or the CCP grouping is wrong for this organization, and the two
  should be reconciled rather than left to drift apart silently.
- **Cost of premature closure.** Grouping by anticipated reason for change
  requires guessing what will change together before the requirements that
  prove or disprove the guess have arrived. A wrong guess produces a
  component boundary that looks tidy on day one and turns into exactly the
  scattered-change problem CCP exists to prevent once real requirements
  land differently than predicted. This is the same risk YAGNI names for
  features, applied to structural boundaries instead.

## 4. Applicability and non-applicability

Reach for CCP explicitly when the following hold.

- The codebase has crossed into more than one independently buildable,
  testable, or releasable unit, and a person now has to decide which unit a
  new class belongs to.
- A recurring pattern of tickets or requirement types is visible in the
  backlog or in git history, business rule changes, regulatory changes,
  a specific integration's API surface, a specific report's formatting,
  and those recurring patterns do not currently map to component
  boundaries.
- A release or deploy process has real friction from unrelated changes
  landing together, a hotfix to one feature forces revalidation of an
  unrelated feature because they share a component.
- Multiple teams work on the same codebase and want to minimize how often
  they collide inside the same file or the same pull request review queue.
- A monolith is being decomposed toward services or a modular monolith, and
  the seam has to be chosen deliberately rather than by which files
  happened to be adjacent in the folder tree.

Do NOT reach for CCP when the following hold instead.

- The system is a single deployable unit with no internal module or package
  boundary yet, and introducing boundaries purely to satisfy CCP before any
  real change-locality pain exists is premature structure, the same
  mistake YAGNI warns against for features.
- The reason for change is genuinely unknown or evenly distributed across
  every class, which is common in a young greenfield system still finding
  its shape. Applying CCP here means guessing, and a wrong guess is more
  expensive to undo than the disorganization it was meant to fix, because
  undoing a component boundary means moving code across build and
  dependency edges, not editing a file in place alone.
- The unit under consideration is reused, published, or consumed by many
  independent parties who each want a small, precise dependency footprint.
  Here the Common Reuse Principle should be weighed first, because a
  component drawn purely for change locality can bundle in classes a
  consumer never uses, forcing every consumer to accept updates and
  transitive dependencies unrelated to what they actually needed.
- The team has fewer than a handful of people and no plan to grow, where
  the coordination cost CCP reduces, cross-team collisions on shared
  files, does not exist yet to be reduced.
- The boundary in question is a security or trust boundary rather than a
  change-reason boundary. CCP is silent on which classes must be isolated
  because they handle secrets or run with elevated privilege, that is a
  separate, security-driven decomposition, and conflating the two produces
  a component that is neither cohesive by change reason nor safe by
  isolation.

## 5. Structure

CCP has no runtime participants in the sense a Gang of Four pattern does,
because it is a rule about how a design-time artifact, the mapping from
classes to components, should be shaped rather than a set of collaborating
objects. Its participants are the artifacts a static analysis or a
dependency graph would reveal.

- **Class or module.** The smallest unit CCP reasons about, whatever unit
  the language treats as independently compilable inside a component, a
  Java class, a Python module, a Go file, a Rust struct plus its impl
  block, a TypeScript exported symbol.
- **Component.** The unit CCP is deciding the contents of, the smallest
  thing that is independently built, versioned, tested, or released, a Java
  or Kotlin package compiled into a JAR, a Python package published to
  PyPI, a Go module, a Rust crate, a .NET assembly, an npm package, or a
  microservice repository.
- **Axis of change.** Not a code artifact but the organizing criterion, the
  named recurring reason requirements arrive, a business rule, a
  regulatory regime, a specific third-party integration, a specific
  presentation format. CCP says the mapping from classes to components
  should be chosen so that each axis of change maps to as few components as
  possible, ideally one.
- **Dependency edge.** The relationship between two components that CCP's
  outcome is measured against. A well-applied CCP reduces the number of
  components a given change touches, and by extension the number of
  dependency edges that must be walked and revalidated when a component
  releases a new version.

## 6. ASCII structure diagram

```
BEFORE CCP: classes grouped by object type, not by reason for change

  +------------------+   +------------------+   +------------------+
  |    Entities      |   |    Services      |   |   Formatters     |
  |------------------|   |------------------|   |------------------|
  | Invoice          |   | TaxService       |   | TaxLineFormatter |
  | Customer         |   | ShippingService  |   | ShipLineFormatter|
  | ShipmentRecord   |   | DiscountService  |   | InvoicePDF       |
  +------------------+   +------------------+   +------------------+
         ^                       ^                       ^
         |                       |                       |
     a "tax rule" requirement touches all three components

AFTER CCP: classes grouped by axis of change

  +--------------------+   +---------------------+   +---------------------+
  |   TaxCalculation    |   |   ShippingRules      |   |   DiscountEngine    |
  |----------------------|   |-----------------------|   |-----------------------|
  | TaxService            |  | ShippingService       |  | DiscountService       |
  | TaxLineFormatter       |  | ShipLineFormatter     |  | DiscountFormatter     |
  | TaxRateSource          |  | ShipZoneSource        |  | PromoCodeSource       |
  +--------------------+   +---------------------+   +---------------------+
         ^
         |
     a "tax rule" requirement now touches exactly one component
```

## 7. Dynamics

CCP has no runtime dynamics, since it is a static organizing rule, but it
has a clear before-and-after dynamic across the change and release process,
which is where its effect is actually observed.

```
REQUIREMENT ARRIVES
       |
       v
IDENTIFY the axis of change the requirement belongs to
(e.g. "this is a tax-rule change")
       |
       v
LOCATE the component(s) currently associated with that axis
       |
   +---+---------------------------+
   |                               |
ONE component found         MULTIPLE components found
   |                               |
   v                               v
edit that component        this is the CCP signal.
   |                        the axis is scattered.
   v                        plan a refactor to merge
run that component's        the scattered classes into
tests only                  one component before, or
   |                        as part of, this change
   v
release/version that
component only
   |
   v
DEPENDENTS of the changed component
decide, independently and on their
own schedule, whether to adopt the
new release (per the Reuse/Release
Equivalence Principle)
```

The dynamic that CCP is judged on is the width of the blast radius in the
middle box. A codebase where every incoming requirement maps to exactly one
component is exhibiting CCP. A codebase where requirements routinely fan
out across three, four, five components is exhibiting the absence of CCP,
regardless of how clean any individual class looks in isolation.

## 8. Implementation variants

- **Package-by-feature, the common name for CCP applied at the source
  layer.** Instead of `controllers/`, `services/`, `repositories/` folders
  each containing every feature's classes, group by feature,
  `checkout/CheckoutController.java`, `checkout/CheckoutService.java`,
  `checkout/CheckoutRepository.java`. This is CCP applied without yet
  introducing a separate build or release unit, useful as a stepping stone
  inside a single module before a real component boundary is justified.
- **Package-by-feature with a build boundary.** The same grouping, but each
  feature package becomes its own Maven module, Gradle subproject, Go
  module, or npm workspace package, so the CCP grouping is enforced by the
  build tool, not merely by folder convention that a careless import can
  violate.
- **Vertical slice architecture.** A more thorough version of
  package-by-feature that also duplicates or scopes shared infrastructure
  per slice rather than centralizing it, trading some duplication for
  maximal change locality, commonly discussed in the .NET community
  alongside CQRS-style handlers, one folder per use case containing its
  request, handler, and validator together.
- **Bounded context as component, the Domain-Driven Design alignment.** In
  DDD terms, a bounded context is very often the correct unit for a CCP
  component, because a bounded context is, by DDD's own definition, the
  scope inside which a model and its ubiquitous language stay consistent,
  which tends to be the same scope inside which requirement changes stay
  contained. This is a natural pairing rather than a formal equivalence.
  DDD arrives at the boundary from the modeling side, CCP arrives at the
  same kind of boundary from the change-frequency side.
- **Modular monolith with enforced module boundaries.** A single deployable
  binary internally partitioned into modules, Java's Platform Module
  System with `module-info.java` exports, Go's internal packages, or a
  linter-enforced convention in languages with no native module system,
  where CCP drives which classes live in which module even though all
  modules ship together in one release. This variant gets CCP's
  change-locality reasoning benefit without the operational cost of many
  small releasable artifacts, and is the usual first step before splitting
  a monolith into services.
- **Microservice ownership boundary.** At the extreme end, each CCP
  component is a full microservice with its own deployment pipeline, and
  the "component" of the 1990s column becomes a network-separated service.
  This variant adds an entire distributed-systems cost, network latency,
  partial failure, eventual consistency, that Martin's original 1996
  column, written for statically-linked and dynamically-linked C++
  libraries, never had to weigh, so applying CCP to justify a
  microservices split needs the additional forces from distributed
  computing weighed alongside it, not CCP reasoning alone.

## 9. Known production uses

- **The Kubernetes API, organized into API groups.** Kubernetes intentionally
  structures its API surface into named API groups such as `apps`,
  `batch`, `rbac.authorization.k8s.io`, and the unnamed core group, each
  independently versioned and each independently enabled or disabled. The
  official documentation states this is done explicitly to make it easier
  to evolve and to extend its API, and Kubernetes distinguishes resources
  by their API group, resource type, namespace, and name, meaning the
  cluster of resource types that are administratively and semantically
  related, workloads in `apps`, jobs and cron jobs in `batch`, changes
  together on one release schedule rather than forcing an unrelated group
  to bump versions when only one area's API evolves (Kubernetes
  documentation, "The Kubernetes API," kubernetes.io, verified 2026-08-10).
  https://kubernetes.io/docs/concepts/overview/kubernetes-api/
- **HashiCorp's Terraform providers, one repository per cloud or service.**
  `terraform-provider-aws` and `terraform-provider-google` are maintained
  as two entirely separate GitHub repositories under the `hashicorp`
  organization, each with its own changelog, its own release cadence, and
  its own dependency set. A change to AWS's API surface produces a release
  of `terraform-provider-aws` alone, an outcome that is only possible
  because every resource type whose implementation changes together with
  AWS's API, `aws_instance`, `aws_s3_bucket`, `aws_iam_role`, and the rest,
  lives together in that one component rather than being scattered across
  a repository shared with Google Cloud or Azure resource types (GitHub
  repository listings, `hashicorp/terraform-provider-aws` and
  `hashicorp/terraform-provider-google`, verified live via the GitHub API,
  2026-08-10).
  https://github.com/hashicorp/terraform-provider-aws
  https://github.com/hashicorp/terraform-provider-google
- **The Java Platform Module System's decomposition of the JDK.** JEP 200,
  "The Modular JDK," which shipped as the design basis for Project Jigsaw
  in JDK 9, reorganizes what had been one large, flatly-visible standard
  library into named modules, `java.base`, `java.sql`, `java.xml`, and
  dozens more, each of which groups the packages that are specified,
  developed, and released as a single JCP-governed unit rather than the
  entire JDK moving as one undifferentiated block. Public secondary
  documentation of the JEP describes its purpose as reorganizing the JDK
  source code into modules and enforcing module boundaries at build time,
  which is a platform-scale application of grouping classes that specify
  and evolve together, `java.sql`'s JDBC types change together because
  they are specified together, into one closed unit distinct from
  `java.xml` or `java.desktop` (OpenJDK, "JEP 200, The Modular JDK,"
  openjdk.org, content corroborated via public technical summaries because
  the JEP page itself returns a client-side access restriction to
  automated fetches, verified 2026-08-10).
  https://openjdk.org/jeps/200

## 10. Consequences

Positive.

- A requirement that belongs to one axis of change touches one component,
  which shrinks the blast radius of a pull request, the scope of a code
  review, and the set of tests that must rerun before a release.
- Components that do not depend on a changed component are provably
  unaffected by that change, which lets teams schedule releases
  independently rather than synchronizing a release train around a single
  shared artifact.
- The mapping from a support ticket or a requirement to which team or
  which part of the codebase owns this becomes close to mechanical, which
  reduces the coordination overhead described by Conway's Law when
  component boundaries and team boundaries are kept aligned.
- CCP gives a concrete, checkable criterion, whether a change touched more
  than one component, that turns a vague complaint like the code feels
  disorganized into a measurable signal a team can track over a quarter of
  releases.

Negative.

- CCP actively fights the Common Reuse Principle. A component drawn purely
  for change locality can end up containing classes a given consumer never
  needs, forcing that consumer to accept a larger dependency, and a larger
  set of transitively pulled-in updates, than the small slice they
  actually wanted.
- Getting the axis of change wrong is expensive to undo, because undoing it
  means moving classes across a real build and dependency boundary, not
  editing a file in a folder. A wrong CCP boundary drawn early, before the
  real shape of future requirements is known, can leave a codebase worse
  organized than if no boundary had been drawn yet.
- Applied without also applying the Stable Dependencies Principle, CCP can
  place a highly volatile, change-locality-optimized component underneath
  many stable dependents, which recreates fragility, every legitimate small
  change to the volatile component now forces a revalidation of everything
  above it.
- At the microservice end of the implementation spectrum, applying CCP's
  reasoning to justify a service split introduces network calls, partial
  failure, and data consistency problems that the original single-process
  Martin column never accounted for, and CCP alone provides no guidance on
  managing those new costs.
- A codebase organized strictly by axis of change can be harder to browse
  for someone used to organizing by object type, because where a class such
  as `Invoice` lives no longer has a single, type-based answer. It depends
  on which axis of change currently owns invoice-related behavior.

## 11. Failure modes and misuse

- **Symptom.** A single ticket routinely requires touching four or five
  different modules, each owned by a different team, and the release for a
  small fix keeps slipping because it is blocked on approvals from
  unrelated teams.
  **Cause.** Components were drawn along a technical axis, entities,
  services, controllers, DTOs, rather than along the business or
  regulatory axis that requirements actually arrive on. This is CCP simply
  not having been applied.
  **Fix.** Trace the last dozen or so requirement tickets, group them by
  the axis they actually touched, a specific business rule, a specific
  integration, a specific report, and refactor the components so each
  observed axis maps to one component, moving classes across the existing
  layer folders to do it.
- **Symptom.** One component has ballooned to contain most of the
  codebase, because everything related to billing changes together was
  applied without any further subdivision, and now unrelated billing
  changes, invoicing format, tax calculation, payment gateway integration,
  all force a shared, oversized component to rebuild and revalidate.
  **Cause.** CCP was applied at too coarse a granularity, treating an
  entire broad business domain as one axis of change instead of noticing
  that it actually contains several independent sub-axes that rarely
  change together in practice.
  **Fix.** Look at git history for the co-change signal, which files
  actually change in the same commit over the last several months or years,
  and split the oversized component along the boundaries that signal
  reveals, rather than the boundary that seemed obvious from the domain
  name alone.
- **Symptom.** A tiny, focused component, drawn correctly by CCP, is
  depended on directly by a dozen other components, and every legitimate
  small change to it, adding one new tax jurisdiction, triggers a wave of
  revalidation across all twelve dependents even though most of them never
  touch the new jurisdiction's code path.
  **Cause.** CCP correctly identified where to draw the boundary, but the
  Stable Dependencies Principle was not applied alongside it, so a volatile
  component ended up with many stable dependents instead of few.
  **Fix.** Introduce an interface or abstraction layer between the
  volatile component and its dependents, the Dependency Inversion
  Principle, so most dependents depend on a stable abstraction rather than
  the volatile implementation directly, and only the small number of
  consumers that genuinely need the new behavior depend on the concrete,
  frequently changing component.
- **Symptom.** A team splits a monolith into microservices along what
  looks like a CCP-correct boundary, on paper each service owns one axis
  of change, but the resulting system is slower, harder to debug, and
  requires distributed tracing to answer questions that used to be a
  single stack trace.
  **Cause.** CCP was used as the sole justification for a service split
  without weighing the additional, service-specific costs, network calls
  replacing in-process calls, eventual consistency replacing transactional
  consistency, that CCP itself says nothing about.
  **Fix.** Re-evaluate whether the same change-locality benefit can be had
  with a modular monolith, enforced module boundaries inside one
  deployable process, before paying the distributed-systems cost, and
  reserve an actual service split for axes of change that also need
  independent scaling, independent deployment cadence, or independent
  technology choices, not change locality alone.

## 12. Trade-off matrix

| Force | Common Closure Principle | Common Reuse Principle | Package-by-layer, no CCP |
|---|---|---|---|
| Blast radius of one requirement | Minimized, ideally one component | Not its concern directly, can be wide if reuse-optimal grouping splits an axis of change | Often wide, one requirement fans out across layers |
| Dependency footprint for a consumer | Not optimized, a consumer may pull in unused classes bundled by change reason | Minimized, a consumer pulls only what it actually uses | Depends on layer granularity, often broad |
| Ease of undoing a wrong grouping | Expensive, requires moving classes across a build boundary | Expensive, same reason | Cheap to reorganize inside a layer, but the underlying problem, scattered change, persists |
| Alignment with team ownership | Strong, when axes of change map to team responsibilities | Weak, reuse groupings often cut across team lines | Weak, layers rarely map to a single team's full responsibility |
| Risk from getting the boundary wrong early | High, because the wrong axis is easy to guess before real requirements arrive | High, same reason | Low structural risk, but chronic scattered-change pain instead |

## 13. Related and incompatible patterns

- **Reuse/Release Equivalence Principle, REP.** CCP's direct sibling from
  the same 1996 column. REP says the unit you release must be the unit you
  reuse. CCP says which classes belong inside that unit. They answer two
  different questions about the same artifact, one names the granule, the
  other fills it.
- **Common Reuse Principle, CRP.** CCP's other sibling, and its direct
  counterweight. CRP groups classes that are always reused together. CCP
  groups classes that always change together. A class can belong with a
  different set of neighbors under each principle, and real component
  design is the ongoing negotiation between the two, not a mechanical
  application of either alone.
- **Single Responsibility Principle, SRP.** The book Clean Architecture
  explicitly frames CCP as SRP relocated from the class level to the
  component level, gather what changes for one reason, separate what
  changes for different reasons, applied one level of granularity up.
- **Stable Dependencies Principle.** Governs where in the dependency graph
  a CCP-drawn component should sit once it exists, volatile components
  low, depended upon by few. The two principles are complementary and
  incomplete without each other, as the failure mode above illustrates.
- **Open-Closed Principle.** CCP is, in Martin's own 1996 words, closely
  associated with OCP, because the closure CCP names is the same closure
  OCP asks for at the class level, extension without forcing modification
  of code that should be stable. CCP is the recognition that total closure
  is unattainable and that closure must be applied strategically, grouped
  around the changes a system actually expects.
- **Separation of Concerns.** CCP is a specific, measurable operationalization
  of the broader separation-of-concerns idea, applied specifically to the
  question of how classes are grouped into releasable units rather than to
  concerns in the abstract.
- **Bounded Context, Domain-Driven Design.** Not formally the same
  concept, but frequently the same boundary in practice, since a bounded
  context's scope of model consistency very often coincides with the scope
  inside which a given kind of requirement stays contained.
- **Incompatible in tension, not in principle.** CCP is not incompatible
  with any other pattern in the formal sense of producing broken behavior
  when combined. Its tension with CRP is a design trade-off to be balanced,
  not a conflict to be resolved by picking one and discarding the other.

## 14. Refactoring path in and out

Introducing CCP into an existing codebase that does not have it.

1. Gather evidence before moving anything. Mine version control history for
   co-change, which files were modified together in the same commit or the
   same pull request, over a window long enough to be representative,
   commonly the last six to twelve months of history. This turns which
   classes change together from a guess into a measured fact.
2. Cluster the co-change data into candidate axes of change. Tooling
   ranging from a simple script over `git log --name-only` to dedicated
   code-change-coupling analysis can surface these clusters. The output is
   a proposed grouping, not a final answer, and should be reviewed against
   the team's own knowledge of the domain.
3. Pick the first, highest-friction axis to extract, typically the one
   generating the most cross-cutting pull requests or the most release
   coordination overhead, rather than attempting a system-wide
   reorganization in one pass.
4. Introduce the new component boundary, whether that is a new package, a
   new build module, or a new repository, and move the classes belonging
   to that axis into it, keeping the public surface, interfaces, exported
   symbols, stable for existing callers during the move where the language
   and build tooling allow it.
5. Verify the move by re-running the co-change measurement after a few
   release cycles. If the newly drawn component boundary is correct,
   subsequent commits touching that axis should now be scoped almost
   entirely inside the new component.
6. Repeat for the next highest-friction axis, treating the whole effort as
   incremental restructuring rather than a single large-scale rewrite,
   consistent with the general discipline that structural refactoring
   should proceed in small, independently verifiable steps.

Removing or relaxing CCP when it stops earning its place.

1. Recognize the signal that CCP has been over-applied, an explosion of
   very small components each with a tiny number of classes, where the
   overhead of tracking versions and dependency edges between them now
   exceeds the coordination cost they were meant to reduce.
2. Measure which of those small components are consistently released
   together, sharing the same version bump in practice even though they
   are structurally separate. This is evidence that CRP, not CCP, is the
   more relevant force at this stage, since these components are reused
   and released as a unit even though they were split by change reason.
3. Merge the components that are consistently released together back into
   one, re-running the same co-change measurement from the introduction
   path to confirm the merge does not reintroduce the original scattered-
   change problem for a distinct axis.
4. Where the original split was justified by an axis of change that has
   since stopped occurring, for example a regulatory regime that no longer
   applies, fold that component's remaining classes back into the closest
   related component rather than leaving an orphaned, effectively frozen
   unit in the dependency graph.

## 15. Testing and verification

CCP is a structural principle, not a runtime behavior, so it cannot be unit
tested in the ordinary sense. It is verified by measurement of the
codebase's structure and by observing the effect of real changes over time.

- **Co-change coupling measurement.** The primary verification technique.
  Mine version control for files that are modified together across
  commits, then check whether that measured coupling is contained inside
  single components or scattered across several. A healthy CCP application
  shows most co-change clusters mapping to one component each. A violation
  shows a co-change cluster spanning several.
- **Blast-radius tracking per pull request.** A lightweight, ongoing check.
  Count how many components a given pull request touches and track that
  metric over time. A rising trend, or a sustained average above roughly
  one to two components per change, is the practical signal that CCP has
  eroded, whether from initial misapplication or from drift as new
  requirement types arrived that were not anticipated when the boundaries
  were drawn.
- **Dependency-cycle and fan-in analysis.** Not a direct CCP check, but a
  necessary companion check, because a CCP-correct component with an
  unexpectedly large fan-in, many dependents, is a signal to revisit the
  Stable Dependencies Principle alongside CCP, per the failure mode above.
  Standard dependency-analysis tooling for the platform in use, `go mod
  graph`, `jdeps` for the Java Platform Module System, `cargo tree`,
  surfaces this.
- **Release-independence smoke test.** Verify in practice, not only in
  theory, that a component can be released without forcing a rebuild or
  revalidation of components that do not depend on it. If the CI pipeline
  or the release process still rebuilds the entire system on every change
  regardless of which component changed, CCP's benefit is not actually
  being realized even if the source-level grouping is correct, and the
  build and release tooling itself needs to change to take advantage of
  the boundary.
- **What CCP makes easier and what it makes harder to test in the
  ordinary unit-test sense.** Easier, because a component whose classes
  all serve one axis of change tends to have a narrower, more coherent set
  of collaborators, which makes constructing a focused test fixture for
  that component simpler than fixturing a component that mixes unrelated
  concerns. Harder, because integration tests that exercise a full user
  scenario spanning multiple axes of change now necessarily cross
  component boundaries, and those tests need to account for each
  component's own versioning and release state rather than assuming
  everything is always built from the same commit.

## 16. Observability signals

- **Files-changed-per-commit histogram, bucketed by component.** A healthy
  system shows most commits touching a single component. A system where
  the histogram has a long tail of commits touching three or more
  components is exhibiting CCP violation in real time, not hypothetically.
- **Component release cadence and correlation.** If two components are
  observed to be released within the same short window on nearly every
  occasion, that correlation is itself a signal, either they belong
  together under CCP and CRP, and the split should be reconsidered, or
  there is a hidden coupling, a shared mutable dependency or a shared
  database table, that is forcing them to move together despite being
  structurally separate.
- **Pull request review latency by number of components touched.** Since
  more components touched typically means more reviewers from more teams,
  tracking review latency against component count gives an operational,
  human-facing metric for whether CCP boundaries are reducing coordination
  cost in practice, not only on a dependency diagram.
- **Dependency graph fan-in per component over time.** A dashboard tracking
  how many other components depend on each component, watched for drift.
  A component originally drawn for change locality that gradually
  accumulates dependents is drifting toward needing the Stable Dependencies
  Principle's treatment, and the observability signal is a rising fan-in
  count on a component whose churn rate, commit frequency, is also high.
- **What a healthy instance looks like.** A component dashboard where
  each component has a small, well-understood set of recent changes that
  map to a single recognizable axis, low cross-component blast radius per
  change, and dependents concentrated on components with low, not high,
  churn.
- **What a failing instance looks like.** A dashboard where the same
  handful of components appear in nearly every recent release, where
  blast radius per requirement is consistently more than one component,
  and where the co-change measurement shows tight coupling between files
  that formally live in different components.

## 17. Security and privacy implications

CCP is largely silent on security and privacy in the sense that it names no
attack surface of its own. It is a maintainability and release-management
principle, and the reasoning above about engineering judgement applies
fully here. There are two indirect implications worth stating plainly, as
judgement rather than sourced fact.

- **A component boundary drawn purely by CCP can accidentally colocate
  sensitive data handling with unrelated logic**, if the axis of change
  that groups classes together happens to also include a class that
  processes personal data, secrets, or payment information, simply because
  that class's business logic changes for the same reason as its
  neighbors. CCP gives no signal that this has happened, because change
  frequency and data sensitivity are orthogonal properties. A team applying
  CCP should apply a separate, security-driven review of the resulting
  component boundaries, checking whether any component now mixes
  sensitive-data-handling code with code that has no legitimate reason to
  be near it, rather than assuming a change-locality-correct boundary is
  automatically a security-correct boundary.
- **Independent release cadence, CCP's main structural benefit, has a
  favorable side effect for patch management.** When a security fix is
  scoped to one axis of change, a CCP-correct grouping means that fix can
  be released, and consumers can adopt it, without forcing an unrelated
  component through the same release cycle, which reduces the coordination
  friction that sometimes delays a security patch in a tightly coupled
  monolith. This is a consequence of the same release-independence property
  discussed under Consequences, applied specifically to the case where the
  triggering change is a vulnerability fix, and it is judgement about a
  likely operational effect, not a sourced claim about any specific
  incident.

## 18. References

1. Robert C. Martin, "Granularity," The C++ Report, Nov/Dec 1996, SIGS
   Publications Group. PDF mirror,
   https://condor.depaul.edu/dmumaugh/OOT/Design-Principles/granularity.pdf,
   verified 2026-08-10, fetched directly and text-extracted, contains the
   original capitalized statements of REP, CRP, CCP, and ADP.
2. Robert C. Martin, *Agile Software Development, Principles, Patterns, and
   Practices*, Prentice Hall, 2002, Chapter 28, "Package Cohesion
   Principles." Publisher listing confirming chapter structure,
   https://www.amazon.com/Software-Development-Principles-Patterns-Practices/dp/0135974445,
   verified 2026-08-10.
3. Robert C. Martin, *Clean Architecture, A Craftsman's Guide to Software
   Structure and Design*, Prentice Hall, 2018, Chapter 13, "Component
   Cohesion." Chapter content and the direct quote of the 2018 wording of
   CCP corroborated via "Clean Architecture Chapter 13, Component
   Cohesion," Lets Code Them Up,
   https://www.letscodethemup.com/clean-architecture-chapter-13-component-cohesion/,
   verified 2026-08-10, and via "Summary of book Clean Architecture by
   Robert C. Martin," GitHub Gist,
   https://gist.github.com/markstachowski/a7fab6397ee1a3488fa79c43cf1bd079,
   verified 2026-08-10.
4. Kubernetes documentation, "The Kubernetes API,"
   https://kubernetes.io/docs/concepts/overview/kubernetes-api/, verified
   2026-08-10, for the description of API groups as a mechanism to evolve
   and extend the API in independently versioned units.
5. GitHub repository, `hashicorp/terraform-provider-aws`,
   https://github.com/hashicorp/terraform-provider-aws, and
   `hashicorp/terraform-provider-google`,
   https://github.com/hashicorp/terraform-provider-google, both verified
   live via the GitHub API 2026-08-10, for the example of independently
   released, per-cloud provider components.
6. OpenJDK, JEP 200, "The Modular JDK," https://openjdk.org/jeps/200,
   existence and scope corroborated via public technical summaries because
   the source page itself returns an access restriction to automated
   fetches, verified 2026-08-10.
7. This catalog's own entry on the Reuse/Release Equivalence Principle,
   `patterns/04-principles-and-laws/release-reuse-equivalence.md`, for the
   sibling principle from the same 1996 source.

## Code examples

The following three implementations each illustrate the same before-and-
after CCP refactor from the structure diagram in section 6, an invoice
system whose tax-handling classes start out scattered across type-based
modules and end up gathered into one component. Each sample was compiled or
run in this environment. Results are stated after each block.

### TypeScript

```typescript
// tax_calculation.ts
// A single module gathering everything that changes when a tax
// rule changes: rate lookup, calculation, and line formatting.

interface TaxRateSource {
  rateFor(jurisdiction: string): number;
}

class StaticTaxRateSource implements TaxRateSource {
  private readonly rates: Record<string, number> = {
    DE: 0.19,
    US_CA: 0.0725,
  };

  rateFor(jurisdiction: string): number {
    const rate = this.rates[jurisdiction];
    if (rate === undefined) {
      throw new Error(`no tax rate configured for ${jurisdiction}`);
    }
    return rate;
  }
}

class TaxCalculator {
  constructor(private readonly rates: TaxRateSource) {}

  taxFor(subtotalCents: number, jurisdiction: string): number {
    const rate = this.rates.rateFor(jurisdiction);
    return Math.round(subtotalCents * rate);
  }
}

class TaxLineFormatter {
  format(taxCents: number, jurisdiction: string): string {
    const amount = (taxCents / 100).toFixed(2);
    return `Tax (${jurisdiction}): $${amount}`;
  }
}

function renderInvoiceTaxLine(
  subtotalCents: number,
  jurisdiction: string,
): string {
  const calculator = new TaxCalculator(new StaticTaxRateSource());
  const formatter = new TaxLineFormatter();
  const taxCents = calculator.taxFor(subtotalCents, jurisdiction);
  return formatter.format(taxCents, jurisdiction);
}

const line = renderInvoiceTaxLine(10000, "DE");
console.log(line);
if (line !== "Tax (DE): $19.00") {
  throw new Error(`unexpected output: ${line}`);
}
console.log("TypeScript CCP example passed");
```

Compiled and run with `npx tsc --noEmit tax_calculation.ts` for type
checking, clean, no errors, and then transpiled and executed with `node`
via `npx tsc tax_calculation.ts --target es2020 --module commonjs && node tax_calculation.js`.
The output was two lines, `Tax (DE): $19.00` and `TypeScript CCP example passed`.

### Python

```python
"""tax_calculation.py

A single module gathering everything that changes when a tax
rule changes: rate lookup, calculation, and line formatting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class TaxRateSource(Protocol):
    def rate_for(self, jurisdiction: str) -> float: ...


@dataclass
class StaticTaxRateSource:
    rates: dict[str, float]

    def rate_for(self, jurisdiction: str) -> float:
        try:
            return self.rates[jurisdiction]
        except KeyError as exc:
            raise ValueError(
                f"no tax rate configured for {jurisdiction}"
            ) from exc


class TaxCalculator:
    def __init__(self, rates: TaxRateSource) -> None:
        self._rates = rates

    def tax_for(self, subtotal_cents: int, jurisdiction: str) -> int:
        rate = self._rates.rate_for(jurisdiction)
        return round(subtotal_cents * rate)


class TaxLineFormatter:
    def format(self, tax_cents: int, jurisdiction: str) -> str:
        amount = tax_cents / 100
        return f"Tax ({jurisdiction}): ${amount:.2f}"


def render_invoice_tax_line(subtotal_cents: int, jurisdiction: str) -> str:
    rates = StaticTaxRateSource({"DE": 0.19, "US_CA": 0.0725})
    calculator = TaxCalculator(rates)
    formatter = TaxLineFormatter()
    tax_cents = calculator.tax_for(subtotal_cents, jurisdiction)
    return formatter.format(tax_cents, jurisdiction)


if __name__ == "__main__":
    line = render_invoice_tax_line(10000, "DE")
    print(line)
    assert line == "Tax (DE): $19.00", f"unexpected output: {line}"
    print("Python CCP example passed")
```

Run with `python3 tax_calculation.py`.
The output was two lines, `Tax (DE): $19.00` and `Python CCP example passed`, exit code 0.

### Go

```go
// A single file gathering everything that changes when a tax
// rule changes: rate lookup, calculation, and line formatting.
// In Go, the package boundary IS the component boundary CCP targets;
// this whole file is one package because a real CCP-drawn component
// would ship as its own Go module, taxcalculation, imported by callers.
package main

import (
	"fmt"
	"os"
)

// RateSource looks up a jurisdiction's tax rate.
type RateSource interface {
	RateFor(jurisdiction string) (float64, error)
}

// StaticRateSource is a fixed, in-memory RateSource.
type StaticRateSource struct {
	rates map[string]float64
}

// NewStaticRateSource builds a StaticRateSource from a rate table.
func NewStaticRateSource(rates map[string]float64) *StaticRateSource {
	return &StaticRateSource{rates: rates}
}

// RateFor returns the configured rate or an error if none exists.
func (s *StaticRateSource) RateFor(jurisdiction string) (float64, error) {
	rate, ok := s.rates[jurisdiction]
	if !ok {
		return 0, fmt.Errorf("no tax rate configured for %s", jurisdiction)
	}
	return rate, nil
}

// Calculator computes tax owed given a subtotal and jurisdiction.
type Calculator struct {
	rates RateSource
}

// NewCalculator builds a Calculator over the given RateSource.
func NewCalculator(rates RateSource) *Calculator {
	return &Calculator{rates: rates}
}

// TaxFor returns the tax owed, in cents, on subtotalCents.
func (c *Calculator) TaxFor(subtotalCents int64, jurisdiction string) (int64, error) {
	rate, err := c.rates.RateFor(jurisdiction)
	if err != nil {
		return 0, err
	}
	return int64(float64(subtotalCents)*rate + 0.5), nil
}

// LineFormatter renders a tax line for display on an invoice.
type LineFormatter struct{}

// Format renders taxCents as a human readable invoice line.
func (LineFormatter) Format(taxCents int64, jurisdiction string) string {
	return fmt.Sprintf("Tax (%s): $%.2f", jurisdiction, float64(taxCents)/100)
}

// RenderInvoiceTaxLine wires the three collaborators together.
func RenderInvoiceTaxLine(subtotalCents int64, jurisdiction string) (string, error) {
	rates := NewStaticRateSource(map[string]float64{
		"DE":    0.19,
		"US_CA": 0.0725,
	})
	calc := NewCalculator(rates)
	var fmtr LineFormatter
	taxCents, err := calc.TaxFor(subtotalCents, jurisdiction)
	if err != nil {
		return "", err
	}
	return fmtr.Format(taxCents, jurisdiction), nil
}

func main() {
	line, err := RenderInvoiceTaxLine(10000, "DE")
	if err != nil {
		fmt.Println("error:", err)
		os.Exit(1)
	}
	fmt.Println(line)
	if line != "Tax (DE): $19.00" {
		fmt.Println("unexpected output:", line)
		os.Exit(1)
	}
	fmt.Println("Go CCP example passed")
}
```

Built and run as a single file with `go run main.go` (a real CCP-drawn component would ship this as its own
module, `taxcalculation`, imported by callers, per the implementation variants section).
The output was two lines, `Tax (DE): $19.00` and `Go CCP example passed`, exit code 0.

Java and Rust were not written for this entry. Both toolchains are present
in this environment, but the pattern's core content, that a component
boundary should gather classes by reason for change, is fully demonstrated
by the three languages above, and a fourth and fifth translation would add
length without adding a new idea. The implementation variants section
already covers how CCP maps onto Java's Platform Module System and Rust's
crate system in the abstract.

## Testing and verification, code

```python
"""test_tax_calculation.py, exercising the Python example above
to demonstrate what CCP makes easy to test: a component whose
classes all serve one axis of change constructs cleanly in
isolation from unrelated concerns such as shipping or discounts.
"""

import unittest

from tax_calculation import (
    StaticTaxRateSource,
    TaxCalculator,
    TaxLineFormatter,
    render_invoice_tax_line,
)


class TaxCalculationTests(unittest.TestCase):
    def test_known_rate(self) -> None:
        rates = StaticTaxRateSource({"DE": 0.19})
        calc = TaxCalculator(rates)
        self.assertEqual(calc.tax_for(10000, "DE"), 1900)

    def test_unknown_rate_raises(self) -> None:
        rates = StaticTaxRateSource({})
        calc = TaxCalculator(rates)
        with self.assertRaises(ValueError):
            calc.tax_for(10000, "FR")

    def test_formatter(self) -> None:
        formatter = TaxLineFormatter()
        self.assertEqual(formatter.format(1900, "DE"), "Tax (DE): $19.00")

    def test_full_pipeline(self) -> None:
        self.assertEqual(
            render_invoice_tax_line(10000, "DE"), "Tax (DE): $19.00"
        )


if __name__ == "__main__":
    unittest.main()
```

Run with `python3 -m unittest test_tax_calculation.py -v` in the same
directory as `tax_calculation.py`. All four tests passed. Each test
constructs only the tax-related collaborators, `StaticTaxRateSource`,
`TaxCalculator`, `TaxLineFormatter`, with no need to stand up an unrelated
shipping or discount component, which is the concrete testing benefit CCP
grouping produces, named in section 15.
