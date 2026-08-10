---
name: Stable Dependencies Principle
slug: stable-dependencies-principle
family: 04-principles-and-laws
category: Principle
aliases: [SDP, Dependency Stability Principle]
first_described: "Martin 1996-2002, restated 2017"
maturity: canonical
related: [stable-abstractions-principle, acyclic-dependencies-principle, dependency-inversion-principle, common-closure-principle, common-reuse-principle, facade, semantic-versioning]
incompatible_with: []
verified: 2026-08-02
---

# Stable Dependencies Principle

## 1. Name, aliases, and lineage

The canonical name is the Stable Dependencies Principle, abbreviated SDP in
almost every source that discusses it. A small number of secondary sources
call it the Dependency Stability Principle, which is the same idea under a
reordered name and never appears in Robert C. Martin's own writing.

SDP is one of three principles Martin grouped under package coupling, the
other two being the Acyclic Dependencies Principle and the Stable
Abstractions Principle. A separate trio, the Reuse or Release Equivalence
Principle, the Common Closure Principle, and the Common Reuse Principle,
governs package cohesion, which classes belong in the same package in the
first place. SDP only makes sense once that cohesion question has already
been answered, because the principle reasons about dependencies between
packages, not about which classes those packages contain.

Martin developed the coupling principles, and the Ca, Ce, and I metrics that
make them checkable, while editing C++ Report in the 1990s, and he restated
them with the same names and the same instability formula in *Agile Software
Development, Principles, Patterns, and Practices*, Prentice Hall, 2002, in
the part of the book devoted to package design principles. He restated them a
third time, largely unchanged, in *Clean Architecture, A Craftsman's Guide to
Software Structure and Design*, Prentice Hall, 2017, chapter 14, "Component
Coupling", which covers the Acyclic Dependencies Principle, the Stable
Dependencies Principle, and the Stable Abstractions Principle together
(confirmed against a public chapter summary at
https://www.letscodethemup.com/clean-architecture-chapter-14-component-coupling-sap-the-stable-abstractions-principle/,
verified 2026-08-02, and against the general chapter outline reported in the
GitHub summary at
https://gist.github.com/ygrenzinger/14812a56b9221c9feca0b3621518635b,
verified 2026-08-02). Martin states the principle in that chapter as
"dependencies should run in the direction of stability", and formalizes
stability as the metric I equals Ce divided by the sum of Ca and Ce, where a
component with zero outgoing dependencies is maximally stable, the same
information those two secondary sources report and that this entry uses
below.

Martin himself is the subject of a short overview at
https://en.wikipedia.org/wiki/Robert_C._Martin (verified 2026-08-02), which
confirms *Agile Software Development, Principles, Patterns, and Practices*
as a 2002 Prentice Hall book and lists his editorship of C++ Report, but does
not itemize his individual C++ Report articles, so the exact 1990s article
title and issue are not independently confirmed here and this entry does not
assert one.

## 2. Problem and context

A system of any real size is built from more than one compilation or
deployment unit, whatever the language calls that unit, a package, a module,
a JAR, a crate, an npm package, an assembly, a component. Those units depend
on each other, and the set of depends-on edges forms a directed graph over
the whole codebase.

Two independent facts are true of every such graph, and neither one is
optional. First, some units change constantly because they are still being
designed, they wrap a fast-moving external integration, or they hold
experimental logic that nobody has committed to. Second, some units are
depended upon by many other units at once, because they define shared types,
core domain rules, or a foundation the rest of the system builds on. The
problem SDP addresses is what happens when those two facts land on the same
unit, or worse, when the unit that changes constantly is the one many other
units depend on.

When a widely depended-upon unit changes, every dependent unit is a
candidate for rework, recompilation, and retesting, and in a language with
static typing that recompilation is not optional, it is forced. The cost of
one change in that unit is multiplied by its number of dependents. A team
that ships a fix to a shared type on a Tuesday can spend the rest of the week
fielding build failures in a dozen other teams' code, work that produced no
new value for anyone, only friction absorbed because the change landed in
the wrong place in the dependency graph.

The context in which this problem is visible has a recognizable shape in a
real codebase, a "core", "common", or "shared" package that started small and
grew a large number of importers over time, alongside newer, still-evolving
packages nearby in the same codebase. Nobody planned for core to become
fragile. It became fragile because the dependency graph around it was never
audited for direction, so a change made for a legitimate reason in a
volatile neighbor kept reaching back into core through an import that should
never have existed.

SDP names the fix directly. Arrange the dependency graph so that stability
increases as you follow edges outward, in other words, a package should only
depend on packages that are at least as unlikely to change as itself. A
volatile package is free to depend on a stable one, because the volatile
package absorbs the pain of its own churn and imposes none on its neighbor.
The reverse relationship, a stable package depending on a volatile one, is
exactly what the principle forbids, because it imports somebody else's
instability into the one place that was supposed to be dependable.

## 3. Forces

The two metrics behind the principle. Afferent coupling, written Ca, is the
count of packages outside a given package that depend on classes inside it.
Efferent coupling, written Ce, is the count of packages outside a given
package that the package depends on. Both counts are drawn from
https://en.wikipedia.org/wiki/Software_package_metrics (verified 2026-08-02),
which states Ca as "the number of classes in other packages that depend upon
classes within the package" and Ce as "the number of classes in other
packages that the classes in a package depend upon". The instability metric
is I equals Ce divided by the sum of Ce and Ca, ranging from 0, a completely
stable package, to 1, a completely unstable package, per the same source.
SDP requires that instability never increase along a dependency edge. For an
edge from package A to package B, I of B must be no larger than I of A.

- Blast radius versus cost of change. Favored, and the whole point of the
  principle. A change to a package with I close to 0 threatens many
  dependents, so the principle pushes toward making that package the one
  that changes least often, matching risk to the place best able to absorb
  it. This is a real cost trade, not a free lunch. The price of a low I
  package is that the team owning it must accept a slower, more deliberate
  rate of change than they would otherwise choose.
- Team autonomy versus shared foundation. Favored for the teams sitting on
  the volatile edges of the graph. They can iterate without asking anyone's
  permission, because nothing important depends on their output yet. The
  cost lands on whoever owns the stable core, who inherits an obligation to
  review changes carefully, maintain backward compatibility, and coordinate
  releases, which is slower and more process-heavy work than volatile-side
  development.
- Discoverability versus indirection. Sacrificed to some degree. A dependency
  graph that respects SDP often needs an interface defined in the stable
  package and implemented in the volatile one, rather than a direct call,
  because that is the only way to let a volatile detail live behind a stable
  seam (this is the territory the companion Stable Abstractions Principle
  and Dependency Inversion Principle cover, see dimension 13). That
  indirection costs a reader an extra hop when tracing who actually runs
  this code.
- Measurement cost versus intuition. A judgement call, not a sourced fact.
  Computing Ca and Ce accurately across a real codebase needs either a
  language-aware static analysis tool or disciplined, easily stale manual
  bookkeeping, and languages with dynamic imports or reflection undercount
  real coupling in ways the raw metric cannot see. A team can apply the
  underlying idea of the principle by intuition and code review without ever
  running a tool, and many do, at the cost of losing the objective threshold
  a tool would have given them.
- Speed of initial design versus long-term stability. Sacrificed early,
  recovered later. Deciding in advance which packages are meant to become
  the stable core and holding that discipline from day one slows early
  velocity, because that discipline requires more interface design up front
  than a codebase where anyone can import anything. Skipping that discipline
  is faster at first and produces exactly the tangled, direction-blind graph
  the principle exists to prevent.

## 4. Applicability and non-applicability

Reach for SDP, and for the tooling that measures it, when the following hold.

- The system is decomposed into more than a handful of packages or modules,
  owned by more than one person or more than one team, so that a badly
  directed dependency imposes a real coordination cost rather than being a
  private inconvenience one developer can fix in five minutes.
- There is a genuine "shared foundation" in the codebase, domain types,
  cross-cutting utilities, an internal SDK, or a platform layer that other
  parts of the system are expected to build on for years, not weeks.
- The codebase includes an experimental, plugin, or integration surface that
  is expected to churn, and the goal is to make sure that churn cannot reach
  back into the parts of the system that are not supposed to churn.
- A build system or dependency manager already gives per-package visibility
  or import rules (Bazel visibility, Nx module boundaries, Go's internal
  package convention, npm's package.json dependency graph), so enforcing a
  stability direction costs configuration rather than new tooling.
- A public API or SDK surface is consumed by parties the maintaining team
  cannot coordinate with directly, so every unplanned dependency on a
  volatile internal detail becomes a support burden later.

Do NOT apply the principle, or apply the underlying discipline without the
formal metric, in the following situations, each with the reason attached.

- A small, single-team codebase with one or two packages and no meaningful
  fan-in difference between them. There is no direction to measure, because
  there is no depth to the graph, and running a static analysis tool for a
  ten-file script produces a number nobody will act on.
- Early-stage, pre product-market-fit code where the team expects most of the
  codebase to be rewritten within weeks regardless of which package it lives
  in. Formalizing a stability hierarchy commits the team to defending
  boundaries that have not yet earned the right to be defended, and that
  defense is time better spent validating whether the product should exist
  at all.
- A situation where high fan-in and real volatility are BOTH accepted on
  purpose, such as a schema registry, a feature-flag service, or a
  configuration store that legitimately must change often even though many
  services call it. The correct mitigation there is a versioned, backward
  compatible contract at the boundary (see dimension 8's semantic versioning
  variant), not a restructuring of source-level import direction, because
  the coupling in question is a runtime contract, not a compile-time class
  dependency.
- Independently deployed services communicating over the network. Martin's
  Ca, Ce, and I metrics are defined over classes and packages inside one
  compiled or interpreted codebase (see https://en.wikipedia.org/wiki/Software_package_metrics,
  verified 2026-08-02). A call from Service A to Service B across an HTTP or
  message-queue boundary is not the kind of dependency the formula measures,
  even though the same underlying intuition, do not let a volatile service
  become a hard dependency of a stable one, still applies and is better
  served by contract testing and versioned wire formats than by a source-code
  metric. Treating a microservice call graph as if it were a package
  dependency graph and applying the formula literally is a category error.
- A single package that both consumes and produces highly volatile data
  shapes by design, for example a raw ingestion layer at the edge of a data
  pipeline. Its instability is a correct reflection of its job, and forcing
  it toward I near zero would only misclassify a package that is supposed to
  be a leaf.

## 5. Structure

- Package (also called a component or module depending on the ecosystem). A
  unit of source that is compiled, versioned, or released as a whole, and
  that groups a set of classes or types decided by the cohesion principles
  (REP, CCP, CRP) rather than by SDP itself.
- Depends-on edge. A directed relationship recorded when a class in one
  package imports, references, or otherwise requires a class in another
  package. The set of these edges across the whole codebase forms the
  dependency graph SDP reasons about.
- Afferent coupling, Ca. For a given package, the count of distinct other
  packages that hold at least one class depending on a class inside the
  given package. A rising Ca means the package is becoming more relied upon.
- Efferent coupling, Ce. For a given package, the count of distinct other
  packages that the given package's own classes depend on. A rising Ce means
  the package is becoming more dependent on the rest of the world, and by
  extension more exposed to change originating elsewhere.
- Instability, I. The derived metric I equals Ce divided by the sum of Ca and
  Ce, per https://en.wikipedia.org/wiki/Software_package_metrics (verified
  2026-08-02). A package with I at 0 depends on nothing and is depended upon
  by everything reachable, the most stable position possible. A package with
  I at 1 depends on everything it needs and is depended upon by nothing, the
  most volatile position possible, and the safest place in the graph to
  absorb frequent change.
- Main Sequence, and the distance metric D. These belong properly to the
  companion Stable Abstractions Principle, which plots Abstractness, the
  ratio of abstract types to total types in a package, against I, and states
  that a well-designed package sits near the diagonal line from
  (Abstractness 0, I 1) to (Abstractness 1, I 0), with distance D equals the
  absolute value of Abstractness plus I minus 1 (per the same Wikipedia
  source, verified 2026-08-02). SDP alone only reasons about I and the
  direction of edges. D is included here because most real static-analysis
  tools compute both metrics together and most production discussions of SDP
  reference D in the same breath.

## 6. ASCII structure diagram

```
                        depends on (Ce, outgoing)
                 -------------------------------------->

  +----------------------+       +---------------------------+
  |  app                 |       |  reporting                |
  |  Ca=0  Ce=1  I=1.00  |       |  Ca=0  Ce=1  I=1.00       |
  +----------+-----------+       +-------------+-------------+
             |                                 |
             |                                 |
             v                                 v
        +----+---------------------------------+----+
        |            billing-core                    |
        |            Ca=2  Ce=2  I=0.50               |
        +----+--------------------------------+-------+
             |                                |
             v                                v (SDP violation, see 11)
  +----------+-----------+       +------------+--------------------+
  |  money-types         |       |  notifications-experimental     |
  |  Ca=1  Ce=0  I=0.00  |       |  Ca=1  Ce=2  I=0.67             |
  +----------------------+       +------+---------------------+----+
                                        |                      |
                                        v                      v
                            +-----------+---+      +-----------+---+
                            | email-provider |      | sms-provider  |
                            | Ca=1 Ce=0 I=0  |      | Ca=1 Ce=0 I=0 |
                            +----------------+      +---------------+
```

The two arrows from app and reporting into billing-core are correct SDP
edges, because billing-core (I equals 0.50) is more stable than either
caller (I equals 1.00 each). The arrow from billing-core into
notifications-experimental is the violation this entry's code samples
detect. billing-core, at I equals 0.50, points at a package that is less
stable than itself, at I equals 0.67, so a change inside
notifications-experimental can now force a rebuild of the very core the rest
of the graph depends on.

## 7. Dynamics

SDP is applied at three distinct moments, and the principle only holds
meaning as an ongoing discipline across all three, not as a one-time audit.

At design time, before code exists, an architect or a lead engineer decides
which packages are meant to sit near the stable end of the graph, because
they encode decisions the team is genuinely willing to commit to (domain
types, core contracts, foundational utilities), and which packages are
meant to sit near the volatile end, because they are expected to keep
changing (plugins, integrations with fast-moving external APIs,
experiments). This decision is a design choice, not something a metric can
make for you. The metric can only confirm or contradict a design after code
starts to exist.

At change time, a developer about to add a new import faces a concrete
question, does adding this edge point toward increasing stability or away
from it. In a codebase with a tool computing Ca, Ce, and I continuously, the
developer can check the numbers directly. In a codebase without such
tooling, the practical proxy question is simpler and almost as reliable,
"if I had to choose, which of these two packages would I rather change,
this one or the one I am about to depend on." If the answer is "the one I am
about to depend on", the edge points the wrong way, and the developer should
either invert the dependency through an interface owned by the more stable
package, or accept the coupling deliberately and record why.

At verification time, typically inside continuous integration, an automated
check recomputes the whole graph on every change and fails the build, or at
minimum flags a warning, on any edge from a lower-I package to a
higher-I package, or on any package whose I has drifted below a declared
threshold for a package meant to stay volatile, or above a threshold for a
package meant to stay stable but is now absorbing changes it should not.
This closes the loop. Design sets the intent, change-time review applies the
intent locally, and CI-time measurement catches the cases where local
judgement missed a global consequence.

## 8. Implementation variants

- Manual review discipline. The earliest and still the most common form in
  small teams. A senior reviewer rejects a pull request that adds an import
  running the wrong direction, using judgement rather than a computed
  metric. This scales poorly past a handful of packages because the reviewer
  has to hold the whole graph in their head.
- Static-analysis tooling that computes Ca, Ce, I, and Abstractness directly
  from compiled bytecode or source, and reports or gates on violations.
  JDepend, written by Mike Clark, implements exactly Martin's Ca, Ce, I, A,
  and D formulas for Java bytecode, which is the most direct tooling
  lineage from the principle's original formulation to a piece of shipped
  software. Equivalent tools exist per ecosystem. NDepend for .NET,
  dependency-cruiser for JavaScript and TypeScript, ArchUnit for Java
  architecture assertions written as executable tests, and Deptrac for PHP.
- Build-system-level enforcement, where the constraint is expressed as
  visibility or boundary configuration rather than as a computed metric.
  Bazel's `visibility` attribute on a build target, and Nx's
  `enforce-module-boundaries` ESLint rule, both let a team declare "only
  these callers may depend on this package" directly, which caps Ca by
  policy rather than measuring it after the fact.
- Language-level structural enforcement. Go's `internal/` directory
  convention makes any package under a path segment named `internal`
  unimportable from outside the module tree that contains it, which is a
  compiler-enforced way to keep Ca at zero for a package that has not yet
  earned external dependents, sidestepping the need to measure instability
  for packages that structurally cannot be depended upon from outside.
- Contractual stabilization through Semantic Versioning rather than
  structural stabilization through the dependency graph. A package can
  promise, via its version number, that its PUBLIC surface will not change
  incompatibly within a major version, per semver.org (verified 2026-08-02),
  which states "MAJOR version when you make incompatible API changes" and
  that incompatible changes "should not be introduced lightly to software
  that has a lot of dependent code." This lets the package's internal
  implementation keep evolving quickly, high real Ce inside the
  implementation, while its externally visible I stays effectively 0 from
  the point of view of every dependent, because the CONTRACT is what is held
  stable, not the code behind it.
- Eliminating Ca rather than raising stability, the Linux kernel's variant.
  The kernel deliberately refuses to guarantee a stable internal API for
  out-of-tree drivers, stating at
  https://kernel.org/doc/html/latest/process/stable-api-nonsense.html
  (verified 2026-08-02) that kernel development "is continuous and at a
  rapid pace, never stopping to slow down" and that when an internal
  interface changes, "all of the instances of where this interface is used
  within the kernel are fixed up at the same time." Rather than pay the cost
  of making that interface stable for external consumers, the documented
  policy asks driver authors to merge into the main tree, where "if a kernel
  interface changes, it will be fixed up by the person who did the kernel
  change in the first place." This is SDP satisfied by a different route.
  Instead of raising the stability of a widely depended-upon interface, the
  project keeps the set of external dependents at zero by definition, so
  there is no Ca to protect in the first place.
- Anti-corruption layer, from Domain-Driven Design. When a stable domain core
  legitimately needs data or behavior from a volatile external system, the
  team introduces a translation layer owned by the stable side that depends
  outward only through an interface it defines itself, so the volatile
  system's churn is absorbed at the boundary and never crosses into the
  core's own types. This is a tactical, per-boundary instance of the same
  Dependency Inversion move used more generally in dimension 14.

## 9. Known production uses

- The .NET Runtime team's public breaking-changes policy, documented at
  https://github.com/dotnet/runtime/blob/main/docs/coding-guidelines/breaking-changes.md
  (verified 2026-08-02), states that the team takes compatibility "extremely
  seriously" and sorts every proposed change into a four-bucket severity
  classification, from changes to the "Public Contract" that are generally
  rejected outright, down to changes in code the document calls "Clearly
  Non-Public", which are usually accepted. The document notes that even
  changes in the least-visible bucket can still cause real pain "through a
  popular app or library." This is SDP's logic made explicit as governance.
  The runtime is the single most depended-upon package in the entire .NET
  ecosystem, its I is effectively 0 by design, and the team's process cost
  scales directly with how many other packages point at it.
- Node.js's own documentation formalizes a graded Stability Index for every
  API surface it ships, described at
  https://nodejs.org/api/documentation.html (verified 2026-08-02). The
  levels run from Stability 0, Deprecated, where "backward compatibility is
  not guaranteed", through Stability 1, Experimental, which is "not subject
  to semantic versioning rules" and where breaking changes "may occur in any
  future release", up to Stability 2, Stable, where "compatibility with the
  npm ecosystem is a high priority", and Stability 3, Legacy, which is
  "still covered by semantic versioning guarantees" but no longer actively
  developed. This is a direct, labelled instance of the principle. The
  project tells every consumer, per API, roughly where that piece of surface
  sits on the instability spectrum, rather than leaving consumers to infer
  it.
- Semantic Versioning itself, at https://semver.org/ (verified 2026-08-02),
  is an industry-wide formalization of the same discipline projected onto
  package registries. Its central rule, "Major version X (X.y.z, X greater
  than 0) MUST be incremented if any backward incompatible changes are
  introduced to the public API", exists because package managers such as
  npm, cargo, and pip resolve dependency graphs automatically and need a
  machine-checkable signal for exactly the situation SDP describes in prose,
  a widely depended-upon package changing in a way its dependents did not
  expect.
- The Linux kernel's stable-api-nonsense policy, cited in full in dimension
  8, is a genuine counter-illustration rather than a straightforward
  positive example, and it earns its place here precisely because of that.
  The kernel does not raise the stability of its internal interfaces the way
  SDP would normally recommend for a heavily depended-upon layer. Instead it
  restructures the graph so that the dependents in question, out-of-tree
  drivers, are not permitted to exist as external Ca contributors in the
  first place, which satisfies the underlying goal of the principle, protect
  the core from paying for change it did not choose, through a different
  mechanism than the one the metric formula suggests.
- JDepend, the direct tooling lineage from Martin's own formulas to shipped
  software, computes Ca, Ce, I, Abstractness, and the Main Sequence distance
  D from compiled Java bytecode, matching the exact formulas given at
  https://en.wikipedia.org/wiki/Software_package_metrics (verified
  2026-08-02) and putting them into a runnable checker rather than leaving
  them as a description in a book.

## 10. Consequences

Positive consequences.

- The cost of a breaking change is localized to the packages best able to
  absorb it, which are, by construction, the packages fewer other things
  depend on, so the system as a whole absorbs less total pain per unit of
  necessary change.
- The principle turns a vague code-review complaint, "this feels like it
  imports the wrong direction", into a number that can be computed,
  trended, and gated in CI, which makes the conversation about architecture
  concrete instead of a matter of individual taste.
- A codebase that follows the principle tends to grow a visible "stable
  core, volatile shell" shape, which supports parallel team ownership,
  because a team working near the volatile edge of the graph can iterate
  without coordinating with every other team, while only the smaller group
  owning the core needs to run a heavier review process.
- It gives architects an early warning signal. A package whose I is trending
  toward 0 over time, because more and more things depend on it, is a
  package that is quietly becoming load-bearing, and that trend is visible
  in the metric well before the first painful breaking change actually
  happens.

Negative consequences.

- A package with a low I, high Ca, inevitably becomes hard to change, which
  Martin calls rigid. SDP by itself offers no remedy for that rigidity, only
  a diagnosis of where it will occur. The companion Stable Abstractions
  Principle is what turns "hard to change" into "hard to change but easy to
  extend" by requiring that a stable package also be an abstract one.
  Applying SDP alone, without SAP, can calcify a design decision that
  deserved to keep evolving.
- Accurate Ca and Ce numbers depend on a language-aware analysis tool, and
  in a language with dynamic imports, reflection, dependency injection
  wired through configuration, or duck typing, static analysis
  systematically undercounts real coupling, so the metric can report a
  package as more stable, or more isolated, than it actually behaves in
  production.
- Applying the principle too early, before a package's design has proven
  itself, can freeze an interface into "stable core" status prematurely,
  which fights against a general instinct to defer commitment (the same
  instinct behind You Aren't Gonna Need It) from a different angle. The
  metric rewards low churn, but low churn achieved by declaring something
  off-limits before it deserved that status is not the same as low churn
  earned through a genuinely settled design.
- Ca measures who happens to depend on a package, not whether those
  dependents chose well. A package can accumulate a high Ca purely because
  it was the path of least resistance to import from, not because anyone
  deliberately decided it should anchor the system, and the metric alone
  cannot distinguish earned centrality from accidental centrality, which
  means a team can be misled into treating an accidentally popular package
  as architecturally important when it should instead be split or replaced.

## 11. Failure modes and misuse

Symptom. A single "utils", "common", or "shared" package keeps breaking
builds across the codebase every time it is touched, and every team has
learned to dread a pull request that lists it in the diff.
Cause. The package absorbed a high Ca gradually through convenience imports
over months or years, without anyone deciding on purpose that it should be
the system's most stable node, so its actual rate of change never adjusted
to match the coupling load it had quietly accumulated.
Fix. Apply the Common Closure Principle to split the package along the
reasons different parts of it change, move the pieces that are still
volatile into their own low-Ca packages, and treat only what remains as a
deliberately governed, versioned, review-gated stable core.

Symptom. A "core domain" package that is supposed to be the settled center
of the system keeps importing from an "experiments" or "plugins" package
nearby, and every experimental change now forces a rebuild and a re-test of
core.
Cause. A dependency edge was added pointing in the direction of decreasing
stability, most often because the fastest way to reach a needed function was
a direct import rather than defining an abstraction inside the stable
package and letting the volatile package implement it.
Fix. Invert the dependency. Define the interface, or abstract type, inside
the stable package, have the volatile package depend on that interface and
implement it, and remove the direct import. This is the concrete refactoring
that dimension 14 walks through step by step, and it is what SDP and the
Stable Abstractions Principle together amount to at the component level.

Symptom. A widely used, heavily depended-upon library becomes something no
one wants to touch even to fix an acknowledged bug, because "everything
depends on it" and any change forces a large, coordinated, multi-team
release.
Cause. SDP was followed correctly, the package genuinely has a low I, but
the Stable Abstractions Principle was not, so the package is not only stable
but also concrete, and "stable" quietly became a synonym for "frozen" rather
than "abstract and safely extensible."
Fix. Extract the parts of the public surface that genuinely must stay fixed
into interfaces or abstract types, and push the still-evolving concrete
implementation detail down into lower-Ca packages that implement those
interfaces, so future change can happen behind the stable seam instead of
through it.

Symptom. An automated dependency-graph check runs in CI, flags violations
constantly, and within a few months the team stops respecting it, either
disabling it outright or routinely clicking through an override.
Cause. The package granularity chosen for the check does not match how the
team actually thinks about the system. Either the packages are too
coarse-grained, so nearly every edge in the graph looks like a violation
because everything imports everything else at that granularity, or the
check treats every violation as equally severe when some, a small internal
tool importing another small internal tool, genuinely carry no consequence.
Fix. Recompute the package boundaries first, using the Common Closure and
Common Reuse Principles to decide what belongs together, and then gate only
the edges that cross a small, deliberately declared set of "stable core"
boundaries, rather than gating the whole graph indiscriminately.

## 12. Trade-off matrix

| Approach | Controls dependency direction | Blast radius on change | Enforcement cost | Works across a network boundary | Notes |
|---|---|---|---|---|---|
| No discipline, imports added ad hoc (Big Ball of Mud) | No | Unbounded, grows with codebase age | None, and that is the problem | N/A, no structure to speak of | The baseline SDP exists to move a team away from |
| Acyclic Dependencies Principle alone, no direction rule | Removes cycles, not direction | Reduced versus ad hoc, still unpredictable | Low, a cycle detector is cheap | No | Necessary precondition for SDP's I metric to be well-defined, insufficient by itself |
| Stable Dependencies Principle | Yes, explicitly | Localized to high-I, low-Ca packages | Medium, needs a metrics tool or disciplined review | No, source-level metric | Diagnoses rigidity, does not cure it without SAP |
| Strict layered architecture (each layer depends only on the layer below) | Yes, by convention rather than by measurement | Localized by layer, but a bottom "god layer" can still accumulate excess Ca | Low to medium, often just an import-linter rule | No | Simpler mental model than SDP, less precise, can misclassify a thin bottom layer as safe when it is actually load-bearing |
| Hexagonal or Ports and Adapters architecture | Yes, and pairs SDP with SAP by construction, since ports are abstract by definition | Localized to adapters at the edge | Medium to high, requires disciplined interface design up front | Partially, ports can sit at a network boundary too | Operationalizes SDP plus SAP as a whole-system shape rather than a per-package metric |
| Semantic Versioning at the package-manager boundary | Controls the CONTRACT's direction, not the source graph | Localized to major-version bumps, visible to every dependent through the version number | Low per release, requires ongoing discipline from maintainers | Yes, this is its main advantage over SDP | Complements rather than replaces SDP inside a single codebase, the natural fit for public libraries and cross-service contracts |

## 13. Related and incompatible patterns

The Stable Abstractions Principle is SDP's direct companion and the two are
usually discussed as a pair. SDP says dependencies should point toward
increasing stability. SAP says stability should imply abstraction, so that
the packages depending edges are forced to point at are also the packages
easiest to extend without modifying. Applied together they amount to the
Dependency Inversion Principle projected up from the class level to the
component level. High-level, stable policy depends on abstractions, and
low-level, volatile detail implements those abstractions, per the summary at
the same source cited in dimension 1.

The Acyclic Dependencies Principle is a precondition, not an alternative. The
instability formula divides by the sum of Ca and Ce for a single package
considered in isolation, and reasoning about the direction of stability
across an edge only makes sense if the graph has no cycles. A cycle would
let two packages each treat the other as more stable than itself, which is
incoherent. A dependency graph is checked for cycles first, and only then is
it meaningful to check it for direction.

The Common Closure Principle and the Common Reuse Principle decide package
cohesion before SDP is ever applied, because SDP's Ca and Ce counts are only
as meaningful as the package boundaries they are measured across. Badly
grouped packages produce badly informative metrics regardless of dependency
direction.

The Facade pattern and the Anti-Corruption Layer concept from Domain-Driven
Design are tactical tools that make a specific SDP-compliant edge possible
where a naive implementation would otherwise violate the principle, by
letting a stable package define the shape of its own interaction with a
volatile neighbor rather than reaching directly into that neighbor's
internals.

Semantic Versioning is related but operates one level up, at the package
registry and network boundary rather than inside a single compiled codebase,
and the two disciplines reinforce each other in a system that has both an
internal package graph and a published public surface.

Big Ball of Mud, an anti-pattern rather than a pattern, is the direct
incompatible case. It is precisely the absence of any dependency direction
discipline, and SDP has no meaning inside a codebase where import edges are
added with no attention to what depends on what.

## 14. Refactoring path in and out

Introducing SDP into an existing codebase that does not yet respect it.

1. Establish package boundaries first, using the Common Closure and Common
   Reuse Principles, so that Ca and Ce will be measured across boundaries
   that actually mean something to the team.
2. Build or configure the dependency graph, using a static-analysis tool
   appropriate to the language (JDepend, NDepend, dependency-cruiser,
   ArchUnit, or a small custom script over `go list` or an equivalent import
   lister for languages without an off-the-shelf tool).
3. Compute Ca, Ce, and I for every package, and list every edge where the
   target's I exceeds the source's I, the concrete definition of a
   violation used throughout this entry and demonstrated in the code
   samples below.
4. For each violating edge, choose one of three responses. Invert the
   dependency, per the Extract Interface refactoring, define an abstraction
   inside the more stable package, have the volatile package implement it,
   and remove the direct import in the other direction. Absorb the edge
   deliberately, when the coupling is judged acceptable, and record that
   decision so a future reviewer does not treat it as an accident. Or split
   the package that is triggering the violation, when the real problem is
   that two responsibilities with different natural stability were grouped
   into one unit, using Extract Package along Common Closure lines.
5. Recompute the graph after the change and confirm the violation is gone,
   then repeat for the next violation, working from the highest-impact edges
   (those touching the packages with the largest Ca) first.
6. Add a continuous check at the small number of boundaries the team has
   deliberately declared as "must stay stable", per the failure mode in
   dimension 11 about over-broad gating, rather than gating the entire
   graph.

Retiring or relaxing SDP as a discipline.

Once a formerly monolithic set of packages has been decomposed into
independently deployed services communicating over the network, source-level
compile-time coupling between those units no longer exists, and the classic
Ca, Ce, I metric has nothing left to measure across that particular
boundary. At that point the meaningful discipline shifts to the network
contract, versioned APIs, contract tests, and backward-compatible schema
evolution, and continuing to enforce the source-level SDP metric across a
boundary that no longer has source-level coupling produces noise rather than
signal. The underlying intuition, do not let something volatile become a
hard dependency of something stable, survives the transition and is worth
keeping in mind, but the specific metric and the specific tooling built
around it can be retired at that boundary once the migration is complete.

## 15. Testing and verification

SDP compliance is a property of the dependency graph's topology, not of
runtime behavior, so unit tests, which exercise behavior, do not verify it.
Verification happens through static analysis run either on demand or as a
continuous check.

The direct approach is a dedicated package-metrics tool. JDepend for Java
bytecode, NDepend for .NET assemblies, dependency-cruiser for JavaScript and
TypeScript module graphs, or a hand-rolled script over the language's own
import listing facility (`go list -deps`, Python's `ast` module walking
import statements, `cargo metadata` for Rust crate graphs). Each of these can
compute Ca, Ce, and I directly and can be scripted to fail a build on a
violating edge, matching the check demonstrated in this entry's code
samples.

The architecture-fitness-function approach, from Neal Ford, Rebecca Parsons,
and Patrick Kua's *Building Evolutionary Architectures*, treats an SDP check
as one example of a broader class of automated, executable checks against
architectural properties, run continuously alongside the regular test suite
rather than as a one-off audit. ArchUnit for Java is the most direct
implementation of this idea specifically for dependency-direction rules,
letting a team write an assertion such as "no class in the domain package
may depend on a class in the infrastructure package" as an ordinary,
continuously running test.

Where the boundary in question is a network boundary rather than a
source-level import, contract testing (consumer-driven contracts, schema
compatibility checks in a schema registry) replaces the static-analysis
approach, verifying the equivalent property, a volatile producer cannot
break a stable consumer's assumptions, without a source-level dependency
graph to measure.

## 16. Observability signals

A healthy dependency graph shows a small number of packages with high Ca and
low I, each one under visible, deliberate release discipline (a changelog, a
tagged version, a slower commit cadence relative to its size), and a larger
number of packages with low Ca and high I, showing a comparatively high
commit frequency, which is expected and not a warning sign for those
packages specifically.

The signal worth trending over time, per release or per sprint, is the count
of SDP-violating edges in the graph. A healthy trend line sits at or near
zero and stays there. A rising trend line means the team is accumulating
architectural debt in the dependency graph faster than it is paying it down,
even if no single violation looks alarming on its own.

The signal that indicates trouble already forming is a package whose Ca is
rising over successive releases while its commit frequency is also rising
in the same window. That combination, more code depending on a thing at the
same time that thing is itself changing more, is the leading indicator of
the exact failure mode described first in dimension 11, and it is visible in
ordinary version-control history well before the first painful breaking
change actually occurs, which makes it the most actionable single number to
watch on a dashboard tracking this principle.

A failing instance, once the problem has already arrived rather than being
merely predicted, looks like a package everyone recognizes informally as
"scary to touch", where a git blame or commit-frequency query for that
package shows both a high recent change rate and, cross-referenced against
the dependency graph, a high Ca, confirming numerically what the team
already suspected qualitatively.

## 17. Security and privacy implications

SDP itself carries no direct data-handling implication. It says nothing
about what a package does with data, only about how packages depend on one
another. Its indirect security relevance runs through the same blast-radius
logic the principle is built on, applied to a different kind of harm than
the one it was designed to prevent.

A package chosen, deliberately or accidentally, to sit at a low-I, high-Ca
position in a system's dependency graph is exactly the highest-value target
for a supply-chain compromise, because the same property that makes an
ordinary change to that package expensive, many things depend on it, makes a
malicious change to that package expensive in the opposite direction. A
single compromise propagates to every dependent automatically, with no
additional attacker effort required per victim.

CVE-2021-44228, Log4Shell, documented at
https://nvd.nist.gov/vuln/detail/CVE-2021-44228 (verified 2026-08-02) with a
CVSS 3.1 base score of 10.0, is a real, sourced illustration of this
reversal. Apache Log4j2 is a logging library embedded, often as a transitive
dependency several layers removed from any direct developer choice, across
an extremely large number of Java applications, which the NVD entry's own
summary attributes the vulnerability's severity to directly, noting that
"vulnerable versions propagated through software supply chains, affecting
organizations that never directly used the library but included it
transitively." A package occupying a low-I position earns exactly the kind
of reach a logging utility has here, and that reach is a liability the
moment the package itself is compromised rather than merely changed.

The judgement this entry draws from that case, stated plainly as judgement
rather than as a further sourced fact. A package that a team has
deliberately engineered into a low-I, high-Ca position, because SDP says
that is where stability belongs, should also receive the highest level of
supply-chain scrutiny available to the team, dependency pinning, signature
verification where the ecosystem supports it, and the fastest practical
patch cycle, because the architectural property that makes ordinary change
expensive there is the identical property that makes a security compromise
expensive there.

## 18. References

- Martin, Robert C. *Agile Software Development, Principles, Patterns, and
  Practices*. Prentice Hall, 2002. Part IV, package design principles, the
  chapter covering the coupling trio (Acyclic Dependencies Principle, Stable
  Dependencies Principle, Stable Abstractions Principle). Cited here for the
  origin of the Ca, Ce, and I formulas and the principle's original naming.
  No specific page number is asserted because it was not independently
  confirmed against a verifiable digital source during authoring.
- Martin, Robert C. *Clean Architecture, A Craftsman's Guide to Software
  Structure and Design*. Prentice Hall, 2017. Chapter 14, "Component
  Coupling". Confirmed to cover the Acyclic Dependencies Principle, the
  Stable Dependencies Principle, and the Stable Abstractions Principle
  together, and to state the instability formula, via the secondary summary
  at https://www.letscodethemup.com/clean-architecture-chapter-14-component-coupling-sap-the-stable-abstractions-principle/
  and https://gist.github.com/ygrenzinger/14812a56b9221c9feca0b3621518635b,
  both verified 2026-08-02.
- "Software package metrics." Wikipedia. https://en.wikipedia.org/wiki/Software_package_metrics
  Verified 2026-08-02. Source for the exact Ca, Ce, I, Abstractness, and
  Main Sequence Distance formulas used throughout this entry.
- "Robert C. Martin." Wikipedia. https://en.wikipedia.org/wiki/Robert_C._Martin
  Verified 2026-08-02. Source for Martin's bibliography, confirming the 2002
  publication date and publisher of *Agile Software Development, Principles,
  Patterns, and Practices* and his editorship of C++ Report.
- ".NET breaking changes." dotnet/runtime repository documentation.
  https://github.com/dotnet/runtime/blob/main/docs/coding-guidelines/breaking-changes.md
  Verified 2026-08-02. Source for the four-bucket breaking-change
  classification cited as a named production use.
- "Documentation, Stability Index." Node.js API documentation.
  https://nodejs.org/api/documentation.html Verified 2026-08-02. Source for
  the Stability 0 through Stability 3 levels cited as a named production use.
- "Semantic Versioning 2.0.0." https://semver.org/ Verified 2026-08-02.
  Source for the MAJOR-version-on-incompatible-change rule cited both as an
  implementation variant and as a named production use.
- "Stable API Nonsense." Linux kernel documentation.
  https://kernel.org/doc/html/latest/process/stable-api-nonsense.html
  Verified 2026-08-02. Source for the kernel's documented policy of not
  guaranteeing a stable internal driver API and its recommendation to merge
  drivers into the main kernel tree, cited as a counter-illustration
  production use.
- "CVE-2021-44228 Detail." National Vulnerability Database.
  https://nvd.nist.gov/vuln/detail/CVE-2021-44228 Verified 2026-08-02.
  Source for the Log4Shell vulnerability's severity score and its
  supply-chain propagation, cited in the security implications dimension.

## Code examples

Each sample builds a small package graph, computes Ca, Ce, and I for every
package using the formula from https://en.wikipedia.org/wiki/Software_package_metrics
(verified 2026-08-02), and reports any edge where the target package is less
stable than the source package, the direct, checkable definition of an SDP
violation. All four samples were compiled or run during authoring and
produced identical output, reproduced once below.

```
app                          Ca=0 Ce=1 I=1.00
billing-core                 Ca=2 Ce=2 I=0.50
email-provider-sdk           Ca=1 Ce=0 I=0.00
money-types                  Ca=1 Ce=0 I=0.00
notifications-experimental   Ca=1 Ce=2 I=0.67
reporting                    Ca=0 Ce=1 I=1.00
sms-provider-sdk             Ca=1 Ce=0 I=0.00

SDP VIOLATION: billing-core (I=0.50) depends on notifications-experimental (I=0.67), which is less stable
```

### Python

Ran with `python3 sdp.py` against Python 3.14.6, produced the output above.

```python
"""
Computes the Stable Dependencies Principle instability metric for a small
package graph and reports every edge that violates the principle.

I(package) = Ce / (Ca + Ce)
  Ca = afferent coupling, the number of external packages depending on this one
  Ce = efferent coupling, the number of external packages this one depends on

SDP requires: for every edge A -> B, I(B) <= I(A)
"""
from dataclasses import dataclass, field


@dataclass
class Graph:
    edges: dict[str, set[str]] = field(default_factory=dict)

    def depend(self, source: str, target: str) -> None:
        self.edges.setdefault(source, set()).add(target)
        self.edges.setdefault(target, set())

    def packages(self) -> list[str]:
        return sorted(self.edges.keys())

    def efferent(self, pkg: str) -> int:
        return len(self.edges.get(pkg, set()))

    def afferent(self, pkg: str) -> int:
        return sum(1 for src, targets in self.edges.items() if pkg in targets)

    def instability(self, pkg: str) -> float:
        ca, ce = self.afferent(pkg), self.efferent(pkg)
        return 1.0 if ca + ce == 0 else ce / (ca + ce)

    def violations(self) -> list[tuple[str, str, float, float]]:
        bad = []
        for source, targets in self.edges.items():
            i_source = self.instability(source)
            for target in targets:
                i_target = self.instability(target)
                if i_target > i_source + 1e-9:
                    bad.append((source, target, i_source, i_target))
        return bad


def main() -> None:
    g = Graph()
    g.depend("app", "billing-core")
    g.depend("reporting", "billing-core")
    g.depend("billing-core", "money-types")
    g.depend("notifications-experimental", "email-provider-sdk")
    g.depend("notifications-experimental", "sms-provider-sdk")
    # violation: a stable core package reaching into a volatile shell package
    g.depend("billing-core", "notifications-experimental")

    for pkg in g.packages():
        ca, ce = g.afferent(pkg), g.efferent(pkg)
        i = g.instability(pkg)
        print(f"{pkg:28s} Ca={ca} Ce={ce} I={i:.2f}")

    print()
    violations = g.violations()
    if not violations:
        print("No SDP violations.")
    else:
        for source, target, i_source, i_target in violations:
            print(
                f"SDP VIOLATION: {source} (I={i_source:.2f}) depends on "
                f"{target} (I={i_target:.2f}), which is less stable"
            )


if __name__ == "__main__":
    main()
```

### Go

Ran with `go run sdp.go` against go1.26.4 darwin/arm64, produced the output
above and passes `gofmt -l`.

```go
// Computes the Stable Dependencies Principle instability metric for a small
// package graph and reports every edge that violates the principle.
//
// I(package) = Ce / (Ca + Ce)
// SDP requires: for every edge A -> B, I(B) <= I(A)
package main

import (
	"fmt"
	"sort"
)

type graph struct {
	edges map[string]map[string]bool
}

func newGraph() *graph {
	return &graph{edges: make(map[string]map[string]bool)}
}

func (g *graph) depend(source, target string) {
	if g.edges[source] == nil {
		g.edges[source] = make(map[string]bool)
	}
	g.edges[source][target] = true
	if g.edges[target] == nil {
		g.edges[target] = make(map[string]bool)
	}
}

func (g *graph) packages() []string {
	names := make([]string, 0, len(g.edges))
	for name := range g.edges {
		names = append(names, name)
	}
	sort.Strings(names)
	return names
}

func (g *graph) efferent(pkg string) int {
	return len(g.edges[pkg])
}

func (g *graph) afferent(pkg string) int {
	count := 0
	for _, targets := range g.edges {
		if targets[pkg] {
			count++
		}
	}
	return count
}

func (g *graph) instability(pkg string) float64 {
	ca, ce := g.afferent(pkg), g.efferent(pkg)
	if ca+ce == 0 {
		return 1.0
	}
	return float64(ce) / float64(ca+ce)
}

type violation struct {
	source, target   string
	iSource, iTarget float64
}

func (g *graph) violations() []violation {
	var bad []violation
	for _, source := range g.packages() {
		iSource := g.instability(source)
		targets := make([]string, 0, len(g.edges[source]))
		for target := range g.edges[source] {
			targets = append(targets, target)
		}
		sort.Strings(targets)
		for _, target := range targets {
			iTarget := g.instability(target)
			if iTarget > iSource+1e-9 {
				bad = append(bad, violation{source, target, iSource, iTarget})
			}
		}
	}
	return bad
}

func main() {
	g := newGraph()
	g.depend("app", "billing-core")
	g.depend("reporting", "billing-core")
	g.depend("billing-core", "money-types")
	g.depend("notifications-experimental", "email-provider-sdk")
	g.depend("notifications-experimental", "sms-provider-sdk")
	// violation: a stable core package reaching into a volatile shell package
	g.depend("billing-core", "notifications-experimental")

	for _, pkg := range g.packages() {
		ca, ce := g.afferent(pkg), g.efferent(pkg)
		fmt.Printf("%-28s Ca=%d Ce=%d I=%.2f\n", pkg, ca, ce, g.instability(pkg))
	}

	fmt.Println()
	bad := g.violations()
	if len(bad) == 0 {
		fmt.Println("No SDP violations.")
		return
	}
	for _, v := range bad {
		fmt.Printf(
			"SDP VIOLATION: %s (I=%.2f) depends on %s (I=%.2f), which is less stable\n",
			v.source, v.iSource, v.target, v.iTarget,
		)
	}
}
```

### TypeScript

Ran with `npx tsc --target es2020 --module commonjs --strict sdp.ts` against
TypeScript's compiler with no errors, then `node sdp.js` against Node.js
v23.11.0, produced the output above.

```typescript
/**
 * Computes the Stable Dependencies Principle instability metric for a small
 * package graph and reports every edge that violates the principle.
 *
 * I(package) = Ce / (Ca + Ce)
 * SDP requires: for every edge A -> B, I(B) <= I(A)
 */

class Graph {
  private edges = new Map<string, Set<string>>();

  depend(source: string, target: string): void {
    if (!this.edges.has(source)) this.edges.set(source, new Set());
    this.edges.get(source)!.add(target);
    if (!this.edges.has(target)) this.edges.set(target, new Set());
  }

  packages(): string[] {
    return [...this.edges.keys()].sort();
  }

  efferent(pkg: string): number {
    return this.edges.get(pkg)?.size ?? 0;
  }

  afferent(pkg: string): number {
    let count = 0;
    for (const targets of this.edges.values()) {
      if (targets.has(pkg)) count++;
    }
    return count;
  }

  instability(pkg: string): number {
    const ca = this.afferent(pkg);
    const ce = this.efferent(pkg);
    return ca + ce === 0 ? 1 : ce / (ca + ce);
  }

  violations(): { source: string; target: string; iSource: number; iTarget: number }[] {
    const bad = [];
    for (const source of this.packages()) {
      const iSource = this.instability(source);
      for (const target of [...(this.edges.get(source) ?? [])].sort()) {
        const iTarget = this.instability(target);
        if (iTarget > iSource + 1e-9) {
          bad.push({ source, target, iSource, iTarget });
        }
      }
    }
    return bad;
  }
}

function main(): void {
  const g = new Graph();
  g.depend("app", "billing-core");
  g.depend("reporting", "billing-core");
  g.depend("billing-core", "money-types");
  g.depend("notifications-experimental", "email-provider-sdk");
  g.depend("notifications-experimental", "sms-provider-sdk");
  // violation: a stable core package reaching into a volatile shell package
  g.depend("billing-core", "notifications-experimental");

  for (const pkg of g.packages()) {
    const ca = g.afferent(pkg);
    const ce = g.efferent(pkg);
    console.log(
      `${pkg.padEnd(28)} Ca=${ca} Ce=${ce} I=${g.instability(pkg).toFixed(2)}`
    );
  }

  console.log();
  const bad = g.violations();
  if (bad.length === 0) {
    console.log("No SDP violations.");
    return;
  }
  for (const v of bad) {
    console.log(
      `SDP VIOLATION: ${v.source} (I=${v.iSource.toFixed(2)}) depends on ` +
        `${v.target} (I=${v.iTarget.toFixed(2)}), which is less stable`
    );
  }
}

main();
```

### Rust

Ran with `rustc -O sdp.rs -o sdp_bin` against a local rustc install with no
warnings, then `./sdp_bin`, produced the output above.

```rust
// Computes the Stable Dependencies Principle instability metric for a small
// package graph and reports every edge that violates the principle.
//
// I(package) = Ce / (Ca + Ce)
// SDP requires: for every edge A -> B, I(B) <= I(A)

use std::collections::{BTreeMap, BTreeSet};

struct Graph {
    edges: BTreeMap<String, BTreeSet<String>>,
}

impl Graph {
    fn new() -> Self {
        Graph { edges: BTreeMap::new() }
    }

    fn depend(&mut self, source: &str, target: &str) {
        self.edges.entry(source.to_string()).or_default().insert(target.to_string());
        self.edges.entry(target.to_string()).or_default();
    }

    fn packages(&self) -> Vec<String> {
        self.edges.keys().cloned().collect()
    }

    fn efferent(&self, pkg: &str) -> usize {
        self.edges.get(pkg).map_or(0, |t| t.len())
    }

    fn afferent(&self, pkg: &str) -> usize {
        self.edges.values().filter(|targets| targets.contains(pkg)).count()
    }

    fn instability(&self, pkg: &str) -> f64 {
        let ca = self.afferent(pkg) as f64;
        let ce = self.efferent(pkg) as f64;
        if ca + ce == 0.0 { 1.0 } else { ce / (ca + ce) }
    }

    fn violations(&self) -> Vec<(String, String, f64, f64)> {
        let mut bad = Vec::new();
        for source in self.packages() {
            let i_source = self.instability(&source);
            if let Some(targets) = self.edges.get(&source) {
                for target in targets {
                    let i_target = self.instability(target);
                    if i_target > i_source + 1e-9 {
                        bad.push((source.clone(), target.clone(), i_source, i_target));
                    }
                }
            }
        }
        bad
    }
}

fn main() {
    let mut g = Graph::new();
    g.depend("app", "billing-core");
    g.depend("reporting", "billing-core");
    g.depend("billing-core", "money-types");
    g.depend("notifications-experimental", "email-provider-sdk");
    g.depend("notifications-experimental", "sms-provider-sdk");
    // violation: a stable core package reaching into a volatile shell package
    g.depend("billing-core", "notifications-experimental");

    for pkg in g.packages() {
        let ca = g.afferent(&pkg);
        let ce = g.efferent(&pkg);
        println!("{:<28} Ca={} Ce={} I={:.2}", pkg, ca, ce, g.instability(&pkg));
    }

    println!();
    let bad = g.violations();
    if bad.is_empty() {
        println!("No SDP violations.");
        return;
    }
    for (source, target, i_source, i_target) in bad {
        println!(
            "SDP VIOLATION: {} (I={:.2}) depends on {} (I={:.2}), which is less stable",
            source, i_source, target, i_target
        );
    }
}
```

Java and Swift are omitted from the runnable set for this entry. The
principle is a package-level metric rather than a class-level pattern with
an idiomatic single-class shape, and the four samples above already cover
both a garbage-collected dynamic language, two statically typed
garbage-collected languages, and a non-garbage-collected systems language,
which is enough coverage of the pattern's actual variation, computing the
same formula over a graph, without the fifth and sixth samples adding a
materially different implementation shape.
