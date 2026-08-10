---
name: Common Reuse Principle
slug: common-reuse-principle
family: 04-principles-and-laws
category: Package and Component Design
aliases: [CRP, Interface Segregation Principle for Packages, Common Reuse Principle for Packages]
first_described: "Robert C. Martin, Object Mentor engineering notebook, mid 1990s, later collected in Agile Software Development. Principles, Patterns, and Practices, 2002"
maturity: canonical
related: [interface-segregation-principle, single-responsibility-principle, acyclic-dependencies-principle, stable-dependencies-principle, facade, mediator]
incompatible_with: []
verified: 2026-08-10
---

# Common Reuse Principle

## 1. Name, aliases, and lineage

The canonical name is the Common Reuse Principle, abbreviated CRP. It is one of
three principles Robert C. Martin grouped under package cohesion, alongside the
Reuse Release Equivalence Principle (REP) and the Common Closure Principle
(CCP). Martin first wrote these up as a series of engineering notebook columns
for the C++ Report in the late 1990s while working at Object Mentor, then
collected and expanded them as Chapters 26 through 28 of Robert C. Martin,
*Agile Software Development, Principles, Patterns, and Practices*,
Prentice Hall, 2002. The principle appears again, restated for component
design, in Robert C. Martin, *Clean Architecture, A Craftsman's Guide to
Software Structure and Design*, Prentice Hall, 2018, Chapter 13, "Component
Cohesion", where Martin gives the definition used almost universally today.
classes and modules that tend to be reused together belong in the same
component.

Martin himself points out an older lineage for the underlying idea. the
principle he formalized as CRP is a restatement, at the package level, of the
Interface Segregation Principle he had already stated at the class level.
clients should not be forced to depend on things they do not use. Applied to a
class interface this becomes ISP. applied to a package, it becomes CRP. This
lineage is stated directly in the Clean Architecture text and is one reason CRP
is sometimes informally called the Interface Segregation Principle for
packages, a name used in secondary literature rather than by Martin as a
primary name.

A frequent and important naming collision needs to be named up front, because
searching for this principle online surfaces the wrong pattern almost as often
as the right one. The Composite Reuse Principle, sometimes shortened in casual
writing to the same three letters "prefer composition", is an entirely
different idea about favoring object composition over class inheritance at the
level of a single class hierarchy. Checked directly against its own reference
page, that principle is described purely as an object level design pattern
concerned with code reuse without inheritance, with no mention of Martin's
package level work (verified against
[Wikipedia, Composition over inheritance](https://en.wikipedia.org/wiki/Composite_reuse_principle),
2026-08-10). The Common Reuse Principle covered in this entry is not about
inheritance versus composition inside one class. it is about which classes get
physically packaged, released, and versioned together as one deployable unit.
Treat any source that conflates "CRP" with "prefer composition over
inheritance" as describing a different principle under a similar-sounding name.

The name Reuse Equivalence Principle is a further point of ambiguity worth
noting. Martin's REP (Reuse Release Equivalence Principle) governs what CAN
be grouped for release. CRP governs what SHOULD be grouped for release, from
the direction of the consumer's actual usage pattern. The two pull in the same
general direction but answer different questions, and a package can satisfy
REP (it releases and versions coherently) while still violating CRP (it
bundles classes that are never actually reused together), which is exactly the
failure mode this entry documents.

## 2. Problem and context

A team ships a library, an internal package, or a service client as one
deployable unit. Some consumer of that unit needs exactly one class from it, an
`InvoiceValidator`, say. The unit also contains a dozen other classes that
happen to live in the same file tree because somebody put them there years ago,
an HTTP retry helper, a date formatter, a logging wrapper, none of which the
consumer needs or wants. To get the one class the consumer actually needs, the
consumer's build must pull in, compile against, and become versionally coupled
to the entire unit.

This is the problem CRP names. classes that are packaged together are, from the
point of view of every consumer, forced to be reused together, whether or not
any individual class inside the package is actually related in purpose to the
others. The pain shows up in a specific, recognizable shape in a real codebase.
a `utils`, `common`, `shared`, or `core` package that keeps growing because it
is the path of least resistance for "somewhere to put this class that does not
obviously belong elsewhere." Every addition to that package raises the release
frequency of the package as a whole (because SOME class inside it changes
often), and every consumer of ANY single class in the package now has to accept
a new version whenever ANY class in the package changes, whether or not the
change touches the part the consumer actually uses. Martin describes this
directly as the situation where "if you depend on a package, you should depend
on every class in that package. In other words, we ought to have very good
reasons for the way we partition packages into classes" (Robert C. Martin,
*Agile Software Development, Principles, Patterns, and Practices*, Prentice
Hall, 2002, Chapter 27, "The Common Reuse Principle").

The context in which CRP becomes the operative principle is any codebase past
the size where a single team can hold the entire dependency graph in their
head, and any codebase that publishes internal or external artifacts other
teams import. Below that scale the cost of an overly broad package is a minor
compile time nuisance. above it, the cost compounds. an unrelated class's churn
forces spurious re-releases, re-testing, and re-deployment of every consumer,
purely because the packaging boundary, not the actual code dependency, ties
their fates together.

## 3. Forces

CRP is one leg of a three-way tension that Martin names directly, and no
single leg can be pushed to its extreme without cost to the other two.

- **Cohesion for the release consumer versus cohesion for the maintainer.**
  REP wants classes that are released and versioned together to actually make
  sense as one release unit for a consumer. CCP, the Common Closure Principle,
  pulls in the opposite direction from CRP. it wants classes that change for
  the SAME REASON at the SAME TIME to sit in the same package, so a single
  requirement change touches one package rather than scattering edits across
  many. CRP pulls toward SMALLER packages, split by what is reused together.
  CCP pulls toward LARGER packages, merged by what changes together. Martin
  states this tension directly. "The CRP and CCP principles are actually
  cohesion principles, but they are diametrically opposed. CCP wants to add
  more classes to a package while CRP wants to remove them" (Martin, *Clean
  Architecture*, Chapter 13). A design that only ever obeys CRP will fracture
  into a package per class, which then fights CCP by scattering every feature
  change across dozens of packages, each needing its own release. A design
  that only ever obeys CCP will grow a monolithic package that fights CRP by
  forcing every consumer to accept unrelated churn.
- **Granularity cost versus coupling cost.** Splitting aggressively reduces
  unwanted coupling (a consumer of `TaxCalculator` no longer has to accept
  changes to an unrelated `Logger`), but it raises the cost of coordinating
  many small release artifacts, more version numbers to track, more
  cross-package dependency declarations to keep consistent, more places a
  breaking change can hide. This is the same trade the microservices
  literature makes at the deployment level, and CRP makes it at the package
  level.
- **Team topology and ownership.** A package boundary that follows CRP tends to
  also follow a natural ownership boundary, because classes reused together are
  usually built and evolved by people solving the same problem. A package that
  violates CRP frequently also crosses ownership boundaries, which raises the
  operability cost of coordinating a change (whose approval is needed to touch
  the shared `utils` package this quarter).
- **Discoverability versus proliferation.** A handful of well-named, cohesive
  packages are easier for a newcomer to navigate than fifty single-class
  packages. CRP taken to its logical extreme produces the second, which trades
  low coupling for high cognitive load in navigating the dependency graph.

CRP explicitly favors reducing unnecessary coupling over minimizing the number
of release artifacts, and it explicitly sacrifices some navigational simplicity
and some coordination overhead to get there. The correct reading is not "split
everything," it is "split along the seam of actual reuse, and let CCP pull back
on anything CRP would otherwise atomize past the point of diminishing return."

## 4. Applicability and non-applicability

Apply CRP when:

- A package or module is published, versioned, or released as an independent
  artifact that other teams or other codebases depend on (an internal shared
  library, a public package, an SDK, a client library).
- The package has grown a "grab bag" character. it accumulates unrelated
  utility classes over time because it is the path of least resistance, rather
  than because those classes are reused as a set.
- Consumers routinely import the whole package to reach one or two classes,
  and the package's changelog shows churn in parts consumers never touch.
- A dependency graph analysis shows a package with high afferent coupling (many
  things depend on it) where different subsets of dependents use disjoint
  subsets of its classes. This is the mechanically detectable signature of a
  CRP violation and is discussed further in dimension 16.
- You are designing a new library boundary from scratch and want the boundary
  to track genuine usage patterns rather than filesystem convenience.

Do NOT apply CRP, or apply it with restraint, when:

- **The package is genuinely internal and has exactly one consumer.** If a
  module is private to a single application with a single deployable, there is
  no independent consumer whose release cadence is being unnecessarily coupled,
  so splitting purely for CRP's sake adds indirection with no payoff. CRP is a
  principle about PACKAGE boundaries that cross independent release
  boundaries, not a mandate to atomize every file inside one deployable.
- **Splitting would violate the Common Closure Principle badly enough that a
  single feature change now touches five packages instead of one.** If two
  classes are always reused together AND always changed together for the same
  business reason, keeping them in one package satisfies both CRP and CCP at
  once, and there is no conflict to resolve. The applicability of CRP is
  specifically about classes reused together but NOT necessarily changed
  together, where the coupling introduced by co-packaging is pure liability.
- **The classes in question are genuinely tiny and stable, with close to no
  independent release history**, such as a handful of small marker
  interfaces or constant definitions that never individually change. The cost
  of coordinating N micro-releases for classes that never change on their own
  exceeds the coupling cost of leaving them together.
- **Early in a project's life, before real usage patterns exist.** CRP asks
  "what is actually reused together," which is an empirical, observed fact
  about how consumers use the code. Applying it prematurely, before any second
  consumer exists, is guessing at a boundary rather than discovering one, and
  Martin explicitly warns that architects should not try to identify the
  correct packages from the beginning (Martin, *Agile Software Development*,
  Chapter 27, discussing the granularity dial being movable in either
  direction as the project matures).
- **When the "unrelated" classes are unrelated in name only but share an
  invariant that must change atomically for correctness**, for example a
  currency type and its rounding-mode enum. correctness safety here can
  outweigh a strict reading of "reused together," and belongs to CCP's
  territory more than CRP's.

## 5. Structure

CRP is not a structural pattern with named participant roles in the way a GoF
pattern is. it is a partitioning rule applied to an existing set of classes.
The relevant "structure" is the shape of the dependency graph before and after
the rule is applied, and the roles below describe the actors in that graph
rather than classes in a class diagram.

- **Package (the reuse unit).** The independently releasable, versionable,
  importable grouping of classes under evaluation. In JavaScript and
  TypeScript this is typically an npm package. in Java it is a JAR or a Java
  Platform Module System module. in Go it is a package directory. in Python
  it is a distributable package (a wheel) or, at minimum, an importable module.
- **Cohesive class set.** The subset of classes inside a package that are, in
  practice, always imported and used together by every real consumer observed.
  This is the set CRP says should be its own package.
- **Consumer.** Any code, in any other package, that imports one or more
  classes from the package under evaluation. A consumer's actual usage pattern
  (which classes it imports, and whether it imports a proper subset) is the
  empirical evidence CRP partitioning is based on.
- **Afferent coupling edge.** A dependency FROM a consumer INTO the package.
  The number and diversity of these edges, and whether different edges touch
  disjoint subsets of the package's classes, is the diagnostic signal for a CRP
  violation.
- **Facade or aggregation package (optional).** Where CRP has split what was
  once one convenient "import everything" package into several cohesive
  packages, teams sometimes add a thin re-export package that pulls the split
  packages back together for the rare consumer who genuinely wants all of
  them, without forcing that cost onto everyone else. This role composes with
  the Facade pattern and is discussed further in dimension 13.

## 6. ASCII structure diagram

```
BEFORE. one package violating CRP, three unrelated consumers

        +-----------------------------------+
        |            shared.utils           |
        |                                    |
        |  InvoiceValidator                  |
        |  TaxCalculator                     |
        |  Logger                            |
        |  DateFormatter                     |
        |  RetryPolicy                       |
        +-----------------------------------+
              ^          ^          ^
              |          |          |
   depends on |          |          | depends on
   (only      |          | depends  | (only
    Invoice-  |          | on only  |  DateFormatter,
    Validator,|          | Logger   |  RetryPolicy)
    TaxCalc)  |          |          |
              |          |          |
        +-----------+ +-----------+ +-----------+
        | Billing   | | Notifier  | | HttpClient|
        | Service   | | Service   | | Wrapper   |
        +-----------+ +-----------+ +-----------+

  Any change anywhere in shared.utils forces a new version onto
  all three consumers, even though each consumer touches a
  disjoint subset of the package.


AFTER. split along observed reuse boundaries (CRP applied)

    +----------------+   +----------------+   +----------------+
    |   billing      |   |   logging      |   |   http         |
    |                |   |                |   |                |
    | InvoiceValidator|  | Logger         |   | RetryPolicy    |
    | TaxCalculator  |   |                |   | DateFormatter  |
    +----------------+   +----------------+   +----------------+
           ^                    ^                     ^
           |                    |                     |
    +-----------+        +-----------+          +-----------+
    | Billing   |        | Notifier  |           | HttpClient|
    | Service   |        | Service   |           | Wrapper   |
    +-----------+        +-----------+           +-----------+

  Each consumer now depends only on the package whose full
  content it actually reuses. A change to RetryPolicy no longer
  forces BillingService to accept a new version of anything.
```

## 7. Dynamics

CRP has no runtime dynamics of its own, it is a static, build-time and
release-time partitioning discipline, not a behavioral pattern with objects
collaborating at execution. The "dynamics" worth documenting are the process by
which a violation is detected and corrected over the life of a codebase.

```
Time  Event
----  -----------------------------------------------------------
T0    A "shared" package is created holding a handful of related
      classes. No violation yet, everything in it is reused
      together by the one existing consumer.

T1    A second, unrelated class is added to "shared" because it
      is a convenient existing package to drop a new helper into.
      A latent CRP violation is introduced, but harmless while
      there is still only one consumer of the package.

T2    A second, independent consumer appears, importing only the
      original classes, never the class added at T1. This is the
      moment the violation becomes real. two consumers now have
      disjoint usage of one release unit.

T3    The class added at T1 changes for reasons unrelated to the
      original classes. Every consumer of "shared", including the
      one that never touches that class, must accept, test
      against, and possibly redeploy for the new release.

T4    Someone notices the pattern. either from repeated
      unnecessary re-releases, from a dependency-graph tool
      surfacing disjoint usage subsets (dimension 16), or from a
      code review flag. A refactor is scoped.

T5    The package is split along the observed usage boundary from
      T2 forward. Each resulting package now has one release
      cadence tied only to the classes consumers of that package
      actually use. See dimension 14 for the refactoring steps.

T6    Future additions are evaluated against the new, narrower
      packages. a new helper is placed by asking "which existing
      consumers would want this reused alongside what is already
      here," not "which package is nearby and convenient."
```

The cycle from T1 to T5 is the lived experience of a CRP violation in almost
every real codebase. the principle is rarely violated by a single deliberate
bad decision, it accretes through many individually reasonable "put it
here for now" choices, and it is corrected retroactively once the pain of
unrelated churn becomes visible in release logs or dependency graphs.

## 8. Implementation variants

- **Language-native package or module boundary.** The most direct
  implementation. draw the package boundary at whatever the language's own
  physical grouping mechanism is, a Java package plus JAR, a Python package
  plus wheel, a Go package directory, a Rust crate, a Swift module. This is the
  variant Martin's original C++ era writing assumes, where "package" means the
  physical release unit, not merely a namespace.
- **npm-style micro-packages.** JavaScript's ecosystem takes CRP to its most
  literal extreme in some cases, publishing a single function as its own
  installable package (lodash's per-method packages, discussed with a live
  citation in dimension 9, are a direct instance of this). This variant pushes
  granularity to its extreme at the cost of proliferation, discussed as a
  force in dimension 3 and a failure mode in dimension 11.
- **Java Platform Module System (JPMS, JDK 9+).** Rather than one physical JAR
  per cohesive class set, JPMS lets a single JAR expose multiple named modules
  with explicit `requires` and `exports` declarations, letting a consumer
  depend on `java.base` without pulling in `java.desktop`, even though both
  historically shipped in one monolithic `rt.jar`. This applies CRP at the
  platform level without necessarily requiring a separate release artifact per
  module, verified against the JDK's own restructuring project (see dimension
  9).
  the tradeoff is that the whole JDK still ships as one release train even
  though its internal module boundaries respect CRP.
- **Feature flags or conditional exports inside one package (a weaker,
  partial implementation).** Some ecosystems, Go and TypeScript libraries in particular, keep one release artifact but expose narrower entry points, for
  example a package.json with multiple `exports` subpaths so a bundler can
  tree-shake unused code even though the release version is still shared. This
  variant satisfies the coupling-avoidance goal of CRP for BUILD SIZE but not
  for RELEASE VERSIONING, an important distinction to make when someone claims
  tree-shaking alone is "enough" CRP.
- **Monorepo with independently versioned packages.** A common modern
  implementation keeps all cohesive class sets in one source repository (for
  build and review convenience) but publishes each as its own independently
  versioned artifact (a Lerna, Nx, or Turborepo-style JavaScript monorepo, or a
  Bazel-managed Java monorepo). This decouples the CRP question (how are
  RELEASES partitioned) from the separate, orthogonal question of how many
  SOURCE repositories a team maintains.

## 9. Known production uses

- **The Apache Commons Proper project.** Rather than one monolithic
  `commons` artifact, Apache Commons is deliberately split into dozens of
  independently released components, `commons-lang`, `commons-io`,
  `commons-collections`, `commons-codec`, `commons-cli`, `commons-csv`,
  `commons-pool`, and more, each with its own Maven artifact, its own version
  number, and its own release cadence. The project's own documentation states
  directly that individual components carry independent releases, and that
  the maintainers work to keep dependencies between components to a minimum
  so each component can be deployed on its own, which is CRP applied
  deliberately as project policy
  (verified against [commons.apache.org](https://commons.apache.org/),
  2026-08-10, listing current independent versions including Commons Lang
  3.20.0, Commons IO 2.22.0, and Commons Collections 4.6.0 as of the
  verification date).
- **Lodash's per-method packages.** In addition to the full `lodash` package,
  the project publishes individual per-function packages such as
  `lodash.debounce` and `lodash.merge`, so a consumer who needs one function
  is not forced to reuse, or version-couple against, the entire utility
  library. The project's own site documents this directly. "Cherry-pick
  methods for smaller browserify/rollup/webpack bundles" via individually
  requirable per-method modules (verified against
  [lodash.com](https://www.lodash.com/), 2026-08-10).
- **The Java Platform Module System (Project Jigsaw, JDK 9, JEP 200, JEP 201,
  JEP 220).** Before JDK 9, the entire JDK class library shipped in one
  monolithic `rt.jar`, which meant any application, however small, that used
  even one class from `java.desktop` linked against every other module's code
  as well. JEP 200 (The Modular JDK), JEP 201 (Modular Source Code), and JEP
  220 (Modular Run-Time Images) restructured the JDK into named modules such as
  `java.base`, `java.desktop`, `java.sql`, and `java.xml`, each expressing
  explicit `requires` and `exports` declarations, letting developers create
  minimal runtime images containing only the modules a given application
  actually uses, which is CRP applied at platform scale to a codebase that had
  grown a decades-long monolithic packaging violation (verified against
  [Wikipedia, Java Platform Module System](https://en.wikipedia.org/wiki/Java_Platform_Module_System),
  2026-08-10, summarizing the JEP 200, 201, and 220 restructuring goals).
- **.NET's split from the monolithic Base Class Library into fine-grained
  NuGet packages.** Starting with .NET Core, Microsoft moved away from a
  single, monolithic `mscorlib`/BCL reference toward individually versioned
  NuGet packages such as `System.Text.Json`, `System.Collections.Immutable`,
  and `System.Net.Http`, so an application that needs immutable collections is
  not forced to also pull in, and version-couple against, unrelated parts of
  the base class library. This is discussed as engineering judgement rather
  than an independently sourced production claim in this entry, because the
  precise scope of the split has shifted release to release and is best
  verified against the current NuGet package listing at the time of use rather
  than asserted as a fixed historical fact here.

## 10. Consequences

Positive consequences.

- **Consumers only accept churn from classes they actually use.** A change to
  a class a consumer never imports produces no forced re-release, no unrelated
  regression risk, and no unrelated review burden for that consumer.
- **Dependency graphs become more legible.** When a package's contents map
  onto its actual reuse pattern, a reader can infer what a package is FOR from
  its name and contents, rather than discovering, by reading source, that half
  of it is unrelated legacy accretion.
- **Smaller blast radius per release.** A defect or a breaking change in a
  narrowly scoped package can only affect the consumers of that narrow scope,
  not every consumer of a broader, unrelated grab-bag package.
- **Enables independent evolution and independent ownership.** Teams can own,
  version, and deprecate a cohesive package on its own schedule, which is a
  precondition for scaling engineering organizationally as well as
  technically.
- **Makes the Interface Segregation Principle's benefit visible at a coarser
  grain.** The same way ISP prevents a class from depending on methods it does not
  use, CRP prevents a package's consumer from depending on classes it does not
  use, so the same testability and change-isolation benefits ISP gives at the
  class level, CRP gives at the release level.

Negative consequences.

- **Package proliferation and coordination overhead.** Applied without
  restraint, CRP produces many small packages, each needing its own version
  number, its own changelog, its own release pipeline entry, and its own
  cross-package dependency declarations to keep synchronized. Martin himself
  names this cost directly when discussing the tension with CCP (dimension 3).
- **Increased navigational and cognitive load for newcomers.** A codebase with
  fifty narrowly scoped packages is harder for a new contributor to build a
  mental model of than one with five broader, well-curated packages, even
  though the fifty-package version has objectively less unwanted coupling.
- **Diamond dependency risk grows with the number of independent packages.**
  More independently versioned packages means more opportunities for two
  transitive dependencies to require incompatible versions of a shared
  package, a problem package managers mitigate but do not eliminate.
- **The correct boundary is only knowable in hindsight.** CRP asks for
  partitioning based on OBSERVED reuse, which means the "right" boundary can
  only be drawn once real consumers exist with real, divergent usage patterns.
  Designing packages by CRP too early amounts to guessing.

## 11. Failure modes and misuse

- **Symptom.** A "utils", "common", or "shared" package that has grown to
  dozens of unrelated classes and keeps a near-continuous release cadence, even
  though no single consumer of it needs more than two or three of those
  classes at a time.
  **Cause.** New classes were added to the existing package because it was the
  path of least resistance for "somewhere to put this," rather than because
  they were genuinely reused alongside the package's existing contents. This is
  the single most common CRP violation and the one Martin's original writing
  targets directly.
  **Fix.** Run the dependency-graph analysis in dimension 16 to find the actual
  disjoint usage subsets, then split along that observed boundary using the
  refactoring path in dimension 14, starting with the highest-churn class that
  has the narrowest consumer set.

- **Symptom.** Splitting a package produces a burst of new packages, each with
  its own tiny release cadence, and the team's release process (changelog
  discipline, semantic version bumps, cross-repo dependency bumps) cannot keep
  up, so packages start drifting out of sync or shipping with stale
  dependency-version pins.
  **Cause.** CRP was applied without regard for the Common Closure Principle,
  producing packages that are individually cohesive by reuse but that also
  frequently need to change together for the same business reason, so every
  feature touches five packages and five release pipelines instead of one.
  **Fix.** Re-merge packages whose contents both reuse together AND change
  together for the same reason, per CCP, and reserve the split for cases where
  reuse and change reasons genuinely diverge. This is the CRP-CCP tension
  named directly in dimension 3, and the fix is to move the granularity dial
  back toward CCP, not to abandon CRP entirely.

- **Symptom.** A consumer that genuinely needs several of the newly split
  packages together (say, both `billing` and `tax-jurisdiction`) has to add
  several separate dependency declarations and keep them version-aligned by
  hand, and complains that the split made their life harder, not easier.
  **Cause.** CRP correctly identified that MOST consumers use these packages
  independently, but this particular consumer is a genuine outlier that needs
  the full set. Treating "one outlier wants everything" as a reason to
  re-merge for everyone else re-introduces the original violation for the
  majority of consumers.
  **Fix.** Add a thin aggregation or facade package that re-exports the split
  packages together, satisfying the outlier consumer without forcing the
  narrower consumers to accept the coupling. Discussed in dimension 13 under
  its relationship with the Facade pattern.

- **Symptom.** A team applies CRP as a mechanical, one-time exercise, splitting
  packages by a snapshot of today's usage, then the usage pattern shifts over
  the following year and the package boundaries no longer match how the code is
  actually reused, but nobody revisits the split.
  **Cause.** CRP was treated as a design-time decision rather than an ongoing
  discipline. Martin is direct that package granularity is a dial meant to
  move over a project's life, not a boundary fixed once and never revisited
  (Martin, *Agile Software Development*, Chapter 27, discussing granularity as
  a movable dial).
  **Fix.** Re-run the dependency-graph diagnostic (dimension 16) periodically,
  not only at initial design time, and treat a growing set of consumers with
  disjoint usage subsets of one package as a recurring signal to re-evaluate
  the boundary, the same way a code smell is re-detected on every review
  rather than fixed once and forgotten.

## 12. Trade-off matrix

| Force | Common Reuse Principle | Common Closure Principle | Single monolithic package (no principle applied) | Micro-package per class |
|---|---|---|---|---|
| Unwanted coupling for a narrow consumer | Low. a consumer depends only on the classes it actually reuses | Higher. classes are grouped by shared reason to change, which can bundle classes a given consumer does not all use | Highest. every consumer of any class accepts every other class's churn | Lowest, near zero, each package is exactly one class |
| Release and version coordination overhead | Moderate. scales with number of cohesive groups discovered | Low. fewer, larger packages, fewer version bumps for a given feature change | Lowest, in the narrow sense of a single version number, but every bump forces every consumer to move | Highest. every new consumer must pin and align dozens of tiny version numbers |
| Cost of a single feature change touching one business concern | Can be high if reuse and change reason diverge, the change may span several CRP-split packages | Low by design, that is exactly what CCP optimizes for | Low mechanically (one package to edit) but the release cost of that edit is high for all consumers | Very high, one business change can require edits and version bumps across many micro-packages |
| Navigability and cognitive load for a newcomer | Moderate, package names track usage, count of packages grows | Moderate to low, package names track business reason for change | Lowest number of packages to learn, but contents inside each are unpredictable | Highest, the sheer count of packages obscures the overall shape |
| Appropriate scale | Multi-team codebases, published libraries, SDKs with independent consumers | Actively evolving single-team codebases where change frequency matters more than reuse | Small, single-consumer, early-stage codebases where the split cost is not yet earned | Ecosystems that specifically optimize for minimal transitive footprint (bundlers, embedded, edge runtimes) |

## 13. Related and incompatible patterns

- **Interface Segregation Principle (class level twin).** CRP is, in Martin's
  own framing, ISP applied one level up, from methods on an interface to
  classes inside a package. Any intuition a reader already has for why a fat
  interface hurts a class's clients transfers directly to why a fat package
  hurts a package's consumers.
- **Common Closure Principle (direct tension).** CRP and CCP are the two
  cohesion principles that actively pull against each other, discussed at
  length in dimension 3. Applying CRP without also weighing CCP produces
  packages that are cohesive by reuse but fragmented by change reason, and vice
  versa. In practice both are applied together, with the granularity dial
  moved toward whichever cost is currently more painful for the project.
- **Reuse Release Equivalence Principle (a precondition, not a rival).** REP
  says a released package must be coherent enough to actually version and
  release as one unit, a documentation and testing precondition. CRP then asks
  which classes belong inside that unit. A package can satisfy REP (it is
  releasable, documented, tested as a unit) while still violating CRP (the
  unit bundles classes nobody reuses together).
- **Acyclic Dependencies Principle (a downstream consequence).** Once packages
  are split along CRP's boundaries, the resulting dependency graph must still
  avoid cycles between packages, which is a separate concern the Acyclic
  Dependencies Principle governs, and a CRP split done carelessly can introduce
  a new cycle where none existed inside the original monolithic package.
- **Facade (compatible, used to soften an over-split boundary).** When CRP
  produces several small packages that one particular consumer genuinely wants
  together, a thin facade or aggregation package that re-exports the split set
  gives that consumer a single import point without forcing the coupling back
  onto every other, narrower consumer.
- **Composite Reuse Principle (not related, frequent naming collision).**
  Discussed at length in dimension 1. this is a class-level composition versus
  inheritance guideline with no connection to package boundaries, and the two
  should never be conflated despite the similar name.
- **Single Responsibility Principle (a class-level relative, different
  scope).** SRP says a class should have one reason to change. CRP says a
  package should contain classes that are reused together. A package can
  satisfy SRP for every class it contains while still violating CRP, if those
  single-responsibility classes are simply unrelated to each other in usage.

## 14. Refactoring path in and out

Introducing CRP into an existing, overly broad package.

1. **Instrument or query the dependency graph** to find, for every consumer of
   the package under review, exactly which subset of the package's exported
   classes that consumer actually imports. Dimension 16 gives concrete tooling.
2. **Cluster consumers by their usage subsets.** Consumers whose subsets
   overlap heavily belong to the same emerging cohesive group. consumers with
   disjoint subsets are evidence of a boundary to split along.
3. **Name the emerging groups by what they are for**, not by where they
   currently live. a group of classes reused together for tax calculation
   becomes a `billing` or `tax` package, not `utils-part-2`.
4. **Move classes into the new packages, keeping the old package as a
   deprecated re-export shim** for one release cycle, so existing consumers do
   not break immediately. This step mirrors the Extract Module (or Extract
   Package) refactoring in the traditional refactoring catalog.
5. **Update the build or release pipeline** so the new packages are
   independently versioned from the point of the split forward. Their version
   history before the split is shared. after the split it diverges, which is
   the entire point.
6. **Migrate consumers off the deprecated shim**, one at a time, pointing each
   at only the specific new package it actually uses. Remove the shim once the
   last consumer has migrated.
7. **Re-run the dependency-graph diagnostic periodically**, not once. usage
   patterns shift as a codebase evolves, and a boundary correct today can
   become stale, per the failure mode described in dimension 11.

Removing or backing off a CRP split that has gone too far, per the failure mode
where CRP has fragmented a set of classes that also need to change together.

1. **Confirm the pain is genuinely a CRP-versus-CCP conflict**, not a
   coordination-tooling gap that better automation would solve on its own (an
   automated cross-repo version bump tool, for example, can remove much of the
   coordination cost without abandoning the split).
2. **Identify the specific subset of split packages that both reuse together
   AND change together**, using recent commit history as evidence for "change
   together," the same signal CCP itself is built on.
3. **Merge only that subset back into one package**, keeping any other split
   packages that genuinely have independent reuse and independent change
   histories separate. A wholesale re-merge back to the original monolith
   discards the real, earned benefit CRP provided for the packages that were
   NOT part of the conflicting subset.
4. **Bump the merged package's major version** to signal the boundary change
   to any remaining consumers who depended on the narrower packages
   individually, and provide a migration note.

## 15. Testing and verification

Largely engineering judgement in this section, drawn from practice rather than
a single citable source.

CRP itself is not directly unit-testable, there is no runtime assertion that
proves a package is "correctly" partitioned, because correctness here is a
property of the package's relationship to its consumers' usage patterns, not a
property of its internal logic. What IS testable, and worth building into a CI
pipeline, is the CONSEQUENCE of a CRP violation. a consumer's test suite should
never fail because of a change to a class that consumer does not import. If a
test suite for `BillingService` starts failing after a change to
`RetryPolicy` that lives in the same package but has no logical connection to
billing, that failing build is itself a signal the package boundary is wrong,
and it is a signal worth treating as seriously as a failing assertion about
business logic.

A second, more direct verification technique is the dependency-graph query
described in dimension 16, run as a periodic CI or architecture-review job
rather than a per-commit gate (because the underlying signal, usage overlap
across consumers, changes too slowly to be worth checking on every commit).
Treat a sudden appearance of a consumer whose usage subset shares zero overlap
with any other consumer of the same package as an architecture-review trigger,
the software equivalent of a code smell surfaced by tooling rather than by a
human reviewer's memory.

For the split itself, once performed, ordinary contract or integration tests
at the boundary of each newly independent package are the right level. does
the split package still behave correctly when consumed in isolation, with no
implicit dependency on the sibling classes it used to sit beside in the same
file tree. A split that silently relied on shared mutable static state, or on
import-order side effects between the formerly co-located classes, will surface
exactly this kind of failure the first time the split packages are tested and
deployed independently, which is itself a valuable, otherwise-hidden coupling
this exercise brings to light.

## 16. Observability signals

Largely engineering judgement in this section.

The primary observability signal for a CRP violation is structural rather than
runtime. run a dependency-graph analysis over the package's consumers (a Java
build tool's dependency report, an npm `depcheck`-style analysis, a Go
`go list -deps`, or a language-appropriate static analyzer) and, for each
consumer, record which subset of the package's exported symbols it actually
imports and uses. Compute the pairwise overlap of these subsets across all
consumers. A package where the overlap is high across most consumers is
healthy by CRP's standard. a package where the overlap forms two or more
disjoint clusters, some consumers using entirely non-overlapping subsets of the
same package, is showing the structural signature of a violation, whether or
not any runtime metric ever surfaces it.

A second, release-process signal worth tracking. for a given package, what
fraction of its releases contain changes that are irrelevant to a given
consumer, measured by whether the consumer's own test suite or usage would have
detected any difference. A package where most releases are irrelevant noise
for most of its consumers is a package whose release cadence is being driven by
classes those consumers do not use, the release-level expression of the same
underlying violation.

A healthy instance of CRP applied looks, on a dependency dashboard, like a
graph where each package's consumer set has clearly overlapping usage subsets
and the package's release notes are relevant to every listed consumer. An
unhealthy instance looks like a package with a wide, structurally disjoint
consumer set and a release history full of changes most of those consumers
never needed to know about.

## 17. Security and privacy implications

CRP has an indirect but real security implication through the supply chain. a
consumer that is forced, by an overly broad package, to depend on classes it
does not use is also forced to pull in, and trust, whatever THOSE unrelated
classes transitively depend on. A narrowly scoped, CRP-compliant `billing`
package that needs no network access carries a smaller and more auditable
transitive dependency and permission footprint than a broad `utils` package
that also happens to bundle an HTTP client wrapper, because the HTTP client's
own transitive dependencies, and its own attack surface, are now unavoidably
part of every consumer's supply chain, including consumers who never make an
HTTP call. This is a direct, mechanical consequence of the same afferent
coupling CRP addresses, not a separate concern layered on top. minimizing what
a package forces its consumers to depend on also minimizes what those
consumers are forced to trust.

CRP is otherwise silent on data handling. it says nothing about how any
particular class inside a well or poorly partitioned package treats sensitive
data, and applying CRP correctly neither introduces nor removes a data
handling risk on its own.

## 18. References

1. Robert C. Martin, *Agile Software Development, Principles, Patterns, and
   Practices*, Prentice Hall, 2002, Chapter 27, "The Common Reuse Principle."
   Primary source for the principle's definition, the "if you depend on a
   package, depend on every class in it" framing, and the discussion of
   granularity as a movable dial over a project's life.
2. Robert C. Martin, *Clean Architecture, A Craftsman's Guide to Software
   Structure and Design*, Prentice Hall, 2018, Chapter 13, "Component
   Cohesion." Restates CRP for component design, gives the ISP-for-packages
   framing, and states the direct tension between CRP and CCP quoted in
   dimension 3.
3. [Wikipedia, Composition over inheritance, redirected from Composite reuse
   principle](https://en.wikipedia.org/wiki/Composite_reuse_principle),
   verified 2026-08-10. Used to confirm the Composite Reuse Principle naming
   collision discussed in dimension 1 is an unrelated, class-level idea with no
   connection to Martin's package-level CRP.
4. [Apache Commons, commons.apache.org](https://commons.apache.org/), verified
   2026-08-10. Used for the independently released component structure cited
   as a production use in dimension 9, including current version numbers for
   Commons Lang, Commons IO, and Commons Collections at the time of
   verification.
5. [Lodash, lodash.com](https://www.lodash.com/), verified 2026-08-10. Used for
   the per-method package cherry-picking claim cited as a production use in
   dimension 9.
6. [Wikipedia, Java Platform Module System](https://en.wikipedia.org/wiki/Java_Platform_Module_System),
   verified 2026-08-10. Used for the JEP 200, JEP 201, and JEP 220 modular JDK
   restructuring cited as a production use in dimension 9.

## Code examples

The examples below show the same partition applied across three languages. a
"before" module that mixes an invoice validator with unrelated logging and date
formatting helpers, forcing any consumer to reuse all three even when it needs
only one, and an "after" module that packages only the classes a billing
consumer actually reuses together, `Invoice`, `TaxCalculator`, and
`InvoiceValidator`. All three examples compiled and ran successfully during
authoring.

TypeScript. compiled with `tsc --strict --target es2020` and run with `node`.
Shown as one file for the compiler. in a real codebase the two groups below
are two separate packages, never one, which is the entire point of the split
this entry argues for.

```typescript
// Unrelated concerns a monolithic "shared" module would force a
// billing consumer to link against, even though it calls neither.
class Logger {
  log(message: string): void {
    console.log(`[LOG] ${message}`);
  }
}

class DateFormatter {
  isoDate(d: Date): string {
    return d.toISOString().slice(0, 10);
  }
}

// The cohesive "billing" set. Every type below is reused together
// by any client that needs invoice validation and tax calculation,
// and nothing else rides along uninvited.
interface Invoice {
  subtotal: number;
  taxRate: number;
}

class TaxCalculator {
  taxFor(invoice: Invoice): number {
    return invoice.subtotal * invoice.taxRate;
  }
}

class InvoiceValidator {
  isValid(invoice: Invoice): boolean {
    return invoice.subtotal >= 0 && invoice.taxRate >= 0;
  }
}

class InvoiceTotaler {
  total(invoice: Invoice, calc: TaxCalculator): number {
    return invoice.subtotal + calc.taxFor(invoice);
  }
}

// A consumer reuses only the cohesive billing set, never Logger
// or DateFormatter.
const invoice: Invoice = { subtotal: 100, taxRate: 0.19 };
const validator = new InvoiceValidator();
const calc = new TaxCalculator();
const totaler = new InvoiceTotaler();

if (validator.isValid(invoice)) {
  console.log(`Total: ${totaler.total(invoice, calc).toFixed(2)}`);
}
// Output. Total: 119.00
```

Python. run with `python3`.

```python
"""billing.py, CRP applied. Cohesive package, reused as a set."""
from dataclasses import dataclass


@dataclass
class Invoice:
    subtotal: float
    tax_rate: float


class TaxCalculator:
    def tax_for(self, invoice: Invoice) -> float:
        return invoice.subtotal * invoice.tax_rate


class InvoiceValidator:
    def is_valid(self, invoice: Invoice) -> bool:
        return invoice.subtotal >= 0 and invoice.tax_rate >= 0


class InvoiceTotaler:
    def total(self, invoice: Invoice, calc: TaxCalculator) -> float:
        return invoice.subtotal + calc.tax_for(invoice)


def main() -> None:
    invoice = Invoice(subtotal=100.0, tax_rate=0.19)
    validator = InvoiceValidator()
    calc = TaxCalculator()
    totaler = InvoiceTotaler()
    if validator.is_valid(invoice):
        print(f"Total: {totaler.total(invoice, calc):.2f}")


if __name__ == "__main__":
    main()
# Output. Total: 119.00
```

Go. run with `go run`. In a real module the billing types below live in their
own `billing` package, imported only by the consumers that reuse them, while
`Logger` and `DateFormatter` live in packages of their own. shown in one file
here purely so the compiler can check it as a single sample.

```go
package main

import "fmt"

// Unrelated concerns that a monolithic "shared" package would
// force a billing consumer to link against, even though it calls
// neither one.
type Logger struct{}

func (Logger) Log(message string) { fmt.Println("[LOG]", message) }

type DateFormatter struct{}

func (DateFormatter) ISODate(iso string) string { return iso }

// The cohesive set a billing consumer actually reuses together.
type Invoice struct {
	Subtotal float64
	TaxRate  float64
}

type TaxCalculator struct{}

func (TaxCalculator) TaxFor(inv Invoice) float64 {
	return inv.Subtotal * inv.TaxRate
}

type InvoiceValidator struct{}

func (InvoiceValidator) IsValid(inv Invoice) bool {
	return inv.Subtotal >= 0 && inv.TaxRate >= 0
}

func total(inv Invoice, calc TaxCalculator) float64 {
	return inv.Subtotal + calc.TaxFor(inv)
}

func main() {
	inv := Invoice{Subtotal: 100, TaxRate: 0.19}
	validator := InvoiceValidator{}
	calc := TaxCalculator{}
	if validator.IsValid(inv) {
		fmt.Printf("Total: %.2f\n", total(inv, calc))
	}
}
// Output. Total: 119.00
```

Java, Rust, and Swift are left out of the runnable set for this entry. CRP is
a packaging and release-boundary discipline rather than a language-feature
pattern, and the shape it takes in Java (a JAR, or a JPMS module) and Rust (a
crate) does not add a materially different idiom beyond what the Go and
TypeScript module examples already demonstrate, module manifests and physical
directory or package boundaries, not new language syntax. Swift's package
manager expresses the identical idea through a `Package.swift` target
boundary and was left out for the same reason, to avoid three restatements of
the same manifest-level mechanism without new content.
