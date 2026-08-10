---
name: Release Reuse Equivalence
slug: release-reuse-equivalence
family: 04-principles-and-laws
category: Principle
aliases: [Reuse/Release Equivalence Principle, REP, Reuse-Release Equivalency Principle]
first_described: "Robert C. Martin, 1996, \"Granularity\", C++ Report; restated as REP in Agile Software Development: Principles, Patterns, and Practices, 2002, and in Clean Architecture, 2018"
maturity: canonical
related: [common-closure-principle, common-reuse-principle, single-responsibility-principle, dependency-inversion-principle, semantic-versioning]
incompatible_with: []
verified: 2026-08-02
---

# Release Reuse Equivalence

## 1. Name, aliases, and lineage

The canonical name in this catalog is Release Reuse Equivalence, matched
almost everywhere else in the literature by its usual short form, the
Reuse/Release Equivalence Principle, abbreviated REP. Robert C. Martin
introduced the idea in "Granularity," the fifth of his Engineering Notebook
columns for The C++ Report, published in the November/December 1996 issue by
SIGS Publications Group (Martin, "Granularity," C++ Report, Nov/Dec 1996, PDF
mirror verified 2026-08-02).
https://condor.depaul.edu/dmumaugh/OOT/Design-Principles/granularity.pdf
Martin restated the principle six years later as one of three package
cohesion principles in Chapter 28 of *Agile Software Development, Principles,
Patterns, and Practices* (Prentice Hall, 2002), alongside the Common Closure
Principle and the Common Reuse Principle, a chapter mapping confirmed by the
book's own table of contents (Prentice Hall / Alan Apt Series listing,
verified 2026-08-02).
https://www.amazon.com/Software-Development-Principles-Patterns-Practices/dp/0135974445
Sixteen years after that, Martin restated it a third time, essentially
unchanged, in Chapter 13, "Component Cohesion," of *Clean Architecture: A
Craftsman's Guide to Software Structure and Design* (Prentice Hall, 2018),
where it appears alongside the same two companions under the collective name
the component cohesion principles (chapter title and content confirmed via
the O'Reilly online table of contents for the book, verified 2026-08-02).
https://www.oreilly.com/library/view/clean-architecture-a/9780134494272/ch13.xhtml

Martin's own one-line statement of the principle, in his 1996 original coinage
of REP, is "the granule of reuse is the granule of release," restated
unchanged in Clean Architecture two decades later (quoted directly from
Martin's original article, verified 2026-08-10; the secondary commentary
source formerly cited here has since gone dark, connection refused on the
live host, checked directly, via curl, and against the Wayback Machine, no
snapshot exists).
https://objectmentor.com/resources/articles/granularity.pdf
No other name for the principle competes with REP in practice. Some authors
write it as the Reuse-Release Equivalency Principle, transposing "reuse" and
"release," which is the same idea under a re-ordered name rather than a
distinct concept, and this entry treats the two orderings as identical. The
two sibling principles Martin always presents alongside REP, the Common
Closure Principle, which groups classes that change together, and the Common
Reuse Principle, which groups classes that are used together, are covered as
their own entries in this catalog and referenced throughout this one, because
none of the three principles is fully legible without the other two in view
(Wikipedia contributors, "Package principles," verified 2026-08-02).
https://en.wikipedia.org/wiki/Package_principles

The word "granule" is doing real work in Martin's phrasing and is worth
pausing on before anything else. A granule, in this vocabulary, is not a
class, a file, or a function. It is whatever unit a consumer of your code
actually points a dependency declaration at, a package name in a
`package.json`, a module path in a `go.mod`, a coordinate in a Maven POM, a
bundle symbolic name in an OSGi manifest. REP is the observation that this
unit, the reuse granule, is only ever as trustworthy as the release process
behind it. If the granule is not independently versioned, tagged, and shipped
on its own schedule, then reusing it means reusing a moving target, and no
amount of good class design inside the granule can compensate for that.

## 2. Problem and context

The problem REP addresses shows up the moment more than one piece of software
wants to depend on the same piece of source code. Two teams inside one
company both need a currency-formatting routine. A library author publishes
an HTTP client that three unrelated open-source projects adopt. A monorepo
grows a `shared/` directory that half a dozen services import from. In every
one of these situations, the code that is being shared has to answer a
question that a single-application codebase never has to answer, when a
change lands, who else is affected, and how do they find out.

Inside one application under one deployment, the answer is trivial. You
change the code, you run the tests, you deploy, and every caller in the
system is running the new behavior together, because there was never more
than one build to begin with. The moment a second, independently deployed
consumer enters the picture, that trivial answer disappears. The
currency-formatting routine now has, at minimum, two copies of itself in the
world at any point in time, the version team A is running and the version
team B is running, and those two versions can and will diverge, because team
A deploys on Tuesdays and team B deploys whenever its quarterly release train
departs. If there is no mechanism that lets team B ask which version of the
formatting code it is actually running, whether a newer one is available, and
whether it is safe to move to, then team B is reusing code by accident rather
than by design, and every future change to the formatting routine becomes a
small act of faith that nobody downstream will be surprised by it.

REP names the fix. Package code for reuse and package code for release as the
same act, at the same granularity, using the same versioning discipline. The
context in which this problem is acute is any codebase, single-repository or
multi-repository, where source is intentionally shared across more than one
independently built or independently deployed consumer. It is not a problem
inside a single deployable unit with a single build pipeline, because there
the release and the consumption happen atomically together every time, so
there is no gap for REP to close. This is the same distinction Martin draws
when he separates the concerns of class design, which is a statement about
correctness and cohesion inside one build, from the concerns of component
design, which are additionally about how that build gets distributed and
consumed by other builds (Martin, restated via chapter summary, "Clean
Architecture Chapter 13, Component Cohesion," verified 2026-08-02).
https://www.letscodethemup.com/clean-architecture-chapter-13-component-cohesion/

## 3. Forces

Several pressures pull against each other whenever a team decides where the
boundary of a releasable, reusable unit should sit, and REP is only one voice
in that argument, not a rule that settles it alone. The following weighting
is engineering judgement drawn from how the principle is actually applied in
package ecosystems, not a claim any single source states in these exact
terms.

**Granularity of blast radius versus granularity of overhead.** Every
component you carve out and version independently gains a real benefit,
consumers can pin to a known-good version and upgrade on their own schedule,
but it also gains a real cost. Someone has to run a release process for it,
someone has to write and maintain a changelog for it, and consumers now have
one more dependency line to track and one more compatibility matrix cell to
worry about. REP pushes toward more components, because an unversioned
grab-bag cannot be trusted, but the Common Reuse Principle and ordinary
operational sanity push back toward fewer, because ten one-class npm packages
each with its own release cadence is its own kind of chaos. The tension
between REP and CCP pulling a design toward more, larger, inclusive
components and CRP pulling toward more, smaller, exclusive ones is exactly
the tension diagram Martin draws in Clean Architecture, and he is explicit
that no fixed answer exists, only a balance an architect revisits as the
concerns of the team change (chapter summary confirming the tension diagram
and the "no fixed answer" framing, verified 2026-08-02).
https://groups.google.com/g/clean-code-discussion/c/1qSCb_EDYYU

**Consistency across consumers versus autonomy of consumers.** A tightly
version-pinned, aggressively synchronized set of consumers gets the benefit
that everyone is always running the same code, which simplifies debugging and
eliminates a whole class of works-on-my-version bugs. But it costs autonomy.
No consumer can upgrade at its own pace, and a single breaking change forces
a coordinated migration across every team that depends on the component. REP
does not by itself resolve this. It only guarantees that when a consumer
chooses to depend on a particular release, that dependency is a concrete,
checkable, reproducible fact rather than an implicit assumption about
whatever the source tree currently contains.

**Cost of the release mechanism itself.** REP presupposes a tracking system,
in Martin's own words, only components that are released through a tracking
system can be effectively reused (quoted directly from Martin's original
1996 article, verified 2026-08-10).
https://objectmentor.com/resources/articles/granularity.pdf
Standing up and maintaining that tracking system, a package registry, a
changelog discipline, a version-numbering policy, a compatibility contract,
is real, ongoing organizational cost. In a small team building one product
this cost can dwarf the benefit, which is exactly why REP is a principle for
reusable components and not a blanket instruction to version every internal
module.

**Cognitive load of the versioning contract.** A consumer who depends on a
REP-honoring component has to understand semantic versioning, or whatever
compatibility contract the component publishes, in order to safely choose a
version range. This is a real tax on every developer who consumes shared
code, and it is a tax REP happily imposes in exchange for the much larger
cost it prevents, silent, undetected breakage from an upstream change nobody
agreed to.

**Team topology.** A component owned and consumed entirely within one team
can get away with a much looser interpretation of REP, because the tracking
can be as informal as a shared understanding of the code's current state. A
component crossing a team boundary, and especially a component crossing an
organizational boundary into the open-source ecosystem, has no such luxury.
The only trustworthy channel between the maintaining team and the consuming
team is the version number and the changelog behind it. REP's weight in a
design decision should scale directly with how far the component travels
from the people who wrote it.

## 4. Applicability and non-applicability

Reach for the discipline REP describes when the following hold.

- Two or more independently built or independently deployed consumers depend
  on the same source code, whether that is two microservices, two mobile
  apps, or an internal team and an external open-source community.
- The source code is expected to change over time in ways that are not
  always backward compatible, so consumers need an explicit signal for when
  it is safe to upgrade and when it is not.
- The component is intended to outlive any single consumer, meaning new
  consumers will start depending on it after the ones that exist today have
  moved on or been replaced.
- The team maintaining the component is different from, or has different
  release cadence needs than, at least one team consuming it.
- The organization already has, or is willing to stand up, a real release
  and tracking mechanism, a package registry, a version-control tag
  discipline, a changelog, a compatibility policy. REP is not achievable by
  wishing a component were versioned. It requires the mechanism to exist.

Do NOT apply REP's full discipline in the following situations, and treat
doing so as premature process overhead rather than good design.

- **A single deployable application with one build pipeline.** If every
  consumer of a piece of code is compiled, tested, and deployed together in
  one atomic release, there is no gap between release and reuse for the
  principle to close, and wrapping an internal module in its own semantic
  version, changelog, and release process adds pure ceremony with no
  corresponding safety gain. This is the single most common REP
  over-application seen in monoliths that decide, for organizational reasons
  rather than technical ones, to version every internal folder as though it
  were a public library.
- **Code that is explicitly, deliberately, and permanently coupled to one
  consumer.** A view model that exists only to serve one specific screen in
  one specific app gains nothing from being carved into its own versioned
  package. There is exactly one reuse site and it is compiled in lockstep
  with the code that defines the version.
- **Early-stage, pre-product-market-fit code where the interface is still
  actively being discovered.** Locking an unstable API behind a formal
  release process before the shape of that API has stabilized tends to slow
  down the very iteration that stabilizes it. Martin's own advice on this,
  echoed by the way semantic versioning treats major version zero as
  explicitly exempt from compatibility promises, is to defer strict
  versioning until the boundary has proven itself stable (Preston-Werner,
  Semantic Versioning 2.0.0, item 4, "major version zero is for initial
  development," verified 2026-08-02).
  https://semver.org/
- **Very small, purely internal helper code with no plausible second
  consumer on the horizon.** REP's cost, a release process and a
  compatibility contract, should be paid only where a second, independently
  scheduled consumer genuinely exists or is genuinely expected. Speculative
  application, versioning something in case someone else needs it someday,
  produces the grab-bag utility library anti-pattern this principle is meant
  to prevent, not the thing it is meant to encourage.
- **Contexts where the Common Reuse Principle dominates.** If splitting a
  cohesive-looking group of classes along REP lines would force every
  consumer to also pull in classes it does not use, CRP's pull toward
  smaller, more exclusive components should win that particular argument.
  REP describes how a chosen granule should be released, it does not by
  itself dictate where that granule's boundary should be drawn.

## 5. Structure

REP is a relationship between three participants rather than a shape you draw
inside one class diagram, so the structure here is the set of roles that have
to exist and cooperate for the principle to hold.

**The release unit** is the component itself, a named, coherent group of
classes, functions, or modules that a maintainer has decided will be
versioned and shipped as one thing. It is the granule in Martin's phrase. Its
defining property, per REP, is that the group of things inside it is exactly
the group of things that get versioned, tagged, and published together, no
more and no less.

**The tracking system** is the mechanism that makes a specific state of the
release unit addressable, discoverable, and comparable to other states, a
version-control tag, an entry in a package registry, a build artifact with a
manifest. Martin is explicit that REP is not satisfied merely by having
cohesive code. It additionally requires this tracking mechanism to exist,
because without it there is no way for a consumer to name, or reason about,
which state of the code it depends on (definition sourced from Martin's
original 1996 article, verified 2026-08-10).
https://objectmentor.com/resources/articles/granularity.pdf

**The compatibility contract** is the promise the release unit's version
number encodes about what changed. Semantic versioning is the dominant
concrete implementation of this contract in the ecosystems examined for this
entry. A MAJOR increment signals an incompatible API change, a MINOR
increment signals backward-compatible new functionality, and a PATCH
increment signals a backward-compatible bug fix (Preston-Werner, Semantic
Versioning 2.0.0, items 4 through 8, verified 2026-08-02).
https://semver.org/
REP does not mandate semver specifically, and older component ecosystems used
other numbering conventions, but every workable implementation of REP
requires some contract of this shape, because without one a version number is
just an opaque label rather than a piece of information a consumer can act
on.

**The consumer** is any independently built or independently deployed unit
that declares a dependency on a specific version, or version range, of the
release unit. The consumer's half of the bargain is to express that
dependency explicitly, typically as a range with a floor and sometimes a
ceiling, rather than by simply copying source or pointing at a moving branch
tip.

The relationship between these four roles is what REP actually describes.
The release unit's boundary determines what gets versioned together, the
tracking system makes that version addressable, the compatibility contract
gives the version number meaning, and the consumer's declared dependency is
the only trustworthy channel through which the maintainer's changes reach the
people relying on them.

## 6. ASCII structure diagram

```text
+-----------------------------------------------------------+
|                    RELEASE UNIT ("granule")                |
|  notifications  (a cohesive, independently-versioned group) |
|                                                             |
|   +-------------+   +-------------+   +-------------+      |
|   | EmailSender |   |  SmsSender  |   | PushSender  |      |
|   +-------------+   +-------------+   +-------------+      |
|                                                             |
|   version: 2.3.1        exports: [Email, Sms, Push]        |
+-----------------------------------------------------------+
              |
              | published through
              v
+-----------------------------------------------------------+
|                    TRACKING SYSTEM                          |
|   package registry / VCS tag / build artifact manifest      |
|   e.g. npm registry entry "notifications@2.3.1"             |
+-----------------------------------------------------------+
              |
              | referenced under a
              v
+-----------------------------------------------------------+
|                 COMPATIBILITY CONTRACT                      |
|         MAJOR . MINOR . PATCH  (Semantic Versioning)        |
|   MAJOR = breaking     MINOR = additive     PATCH = fix     |
+-----------------------------------------------------------+
              |
              | consulted by a declared range from
              v
+---------------------------+   +---------------------------+
|        CONSUMER A          |   |        CONSUMER B          |
|  depends on ^2.1.0         |   |  depends on ^2.1.0         |
|  resolves to  2.3.1  (OK)  |   |  deploys later, resolves   |
|  ships on its own cadence  |   |  to  2.4.0 when it ships   |
+---------------------------+   +---------------------------+
```

## 7. Dynamics

The runtime behavior REP describes is really a release-time and build-time
behavior, so this section traces the sequence of events across time rather
than across a single request.

```text
t0  Maintainer team finishes a cohesive change to the release unit's
    source (one or more classes that change together for the same
    reason, per the Common Closure Principle).

t1  Maintainer team decides the change's compatibility class.
      - if any existing exported behavior changed incompatibly -> MAJOR
      - if new, backward-compatible behavior was added         -> MINOR
      - if only internals changed with no visible effect        -> PATCH

t2  Maintainer team cuts a release. Tags the exact source state in
    version control, builds the artifact, publishes it to the
    tracking system under the new version number, and records the
    change in a changelog addressed to consumers, not to the
    maintainers themselves.

t3  Consumer A, already depending on a version range such as
    "^2.1.0", asks the tracking system to resolve that range the
    next time it builds. If the new release satisfies the range
    (same MAJOR, MINOR.PATCH at or above the floor), Consumer A's
    build silently picks it up on its own schedule, with no
    coordination step required from the maintainer team.

t4  Consumer B, depending on the same range but building on a
    different day, resolves the range independently and may end up
    on a different, equally valid, version of the release unit than
    Consumer A. Both are correct. REP's contract is that both are
    also SAFE, precisely because the version number encodes what
    changed.

t5  If the maintainer team's change had instead been a MAJOR
    increment, resolution against the SAME "^2.1.0" range would
    correctly fail to pick it up, forcing an explicit,
    human-reviewed range bump in each consumer before the
    incompatible change reaches them. This refusal to resolve is
    the mechanism, not a defect in it.
```

The critical property visible in this trace is that steps t3 and t4 happen
with zero communication between the maintainer team and either consumer
team, and that this silence is safe rather than risky, because the version
number carried all of the information a coordination meeting would otherwise
have had to convey. This is the entire practical payoff of REP. It converts a
social coordination problem, who needs to know about this change and how do
I tell them, into a mechanical one, what number did I put on the release, and
does the consumer's declared range accept it.

## 8. Implementation variants

**Package registry with semantic versioning (npm, PyPI, crates.io, Maven
Central, RubyGems).** The dominant modern implementation. A release unit is
published under a name and a semver-shaped version to a central or
organization-internal registry. Consumers declare a range, npm's caret,
Python's comparison operators, Cargo's default caret-like behavior, in a
manifest file, and tooling resolves the highest version in the tracking
system that satisfies every consumer's range. npm's own documentation states
that the caret operator is the default range written by `npm install --save`
and is described as allowing changes that do not modify the left-most
non-zero digit of the version, which is exactly the same-MAJOR,
minor-patch-at-or-above-the-floor rule traced above (behavior confirmed via
independent developer documentation, verified 2026-08-02).
https://bytearcher.com/articles/semver-explained-why-theres-a-caret-in-my-package-json/

**Semantic import versioning (Go modules).** Go takes an unusual and
instructive variant. Rather than letting a version range silently resolve to
different source at build time, Go encodes the MAJOR version directly into
the module's import path once that version reaches 2 or higher, so
`example.com/mod` and `example.com/mod/v2` are, from the Go compiler's point
of view, entirely different packages that can be imported side by side in the
same build. The Go module reference documentation states this plainly. Since
the module path is a prefix of the import path for each package within the
module, adding the major version suffix to the module path provides a
distinct import path for each incompatible version (Go documentation,
"Modules reference, Versions," verified 2026-08-02).
https://go.dev/ref/mod#versions
This is REP taken to its logical extreme. Rather than trusting a version
range to keep an incompatible release out, the incompatible release is given
a structurally different identity so it cannot even be confused with the
compatible one.

**Version-ranged module wiring (OSGi bundles).** In OSGi, a bundle declares
which packages it exports, each carrying a semantic version, and which
packages it imports, each carrying an acceptable version range using
interval notation, for example `Import-Package: com.acme.bar;
version="[1,2)"`, meaning any exported version at or above 1.0.0 up to but
excluding 2.0.0 is acceptable (OSGi Alliance, "Semantic Versioning"
whitepaper, verified 2026-08-02).
https://docs.osgi.org/whitepaper/semantic-versioning/040-semantic-versions.html
The OSGi specification additionally distinguishes an importer's floor from an
exporter's ceiling with a named importer policy, recommending a consumer
compiled against 2.1.4 declare an import range of `[2.1,3)`, again the same
same-MAJOR-at-or-above-the-MINOR-floor shape seen in npm and Go (OSGi
Alliance, "Semantic Versioning, Importer Policy," verified 2026-08-02).
https://docs.osgi.org/whitepaper/semantic-versioning/060-importer-policy.html

**Monorepo internal package boundaries without a public registry.** A large
codebase can honor REP without ever publishing to an external registry, by
treating a directory boundary plus a build-tool dependency graph as the
release unit and using build-time versioning, a content hash, a git commit, an
internal semver bumped by a release script, as the tracking system. This
variant trades the discoverability benefit of a public registry for lower
operational overhead, and is common inside single organizations where every
consumer is internal.

**Vendoring with a pinned, tracked copy.** In ecosystems or eras without a
dependable dependency resolver, teams have implemented REP's spirit by copying a
specific, tagged release of a dependency's source directly into their own
tree, alongside a record of exactly which upstream version was copied. This
satisfies the granule-of-reuse-is-the-granule-of-release requirement, because
the copy is still tied to an addressable, versioned upstream state, even
though the automated resolution step from the registry variants is missing
and updates require a manual re-vendoring step.

## 9. Known production uses

**npm, the default package manager for Node.js and the JavaScript
ecosystem.** Every published npm package is a REP release unit, a name, a
semver version, and a manifest declaring what it exports, resolved by every
consumer against a caret or tilde range in that consumer's own
`package.json`, with `package-lock.json` additionally freezing the exact
resolved graph for reproducible builds (behavior and default caret range
confirmed via independent developer documentation, verified 2026-08-02).
https://bytearcher.com/articles/semver-explained-why-theres-a-caret-in-my-package-json/

**The Go module system, part of the standard Go toolchain since Go 1.11 and
the default dependency mechanism since Go 1.16.** Every Go module is a REP
release unit whose version is not merely metadata but is load-bearing for the
import path itself once the module crosses MAJOR version 2, as detailed in
implementation variants above (Go documentation, "Modules reference,
Versions," verified 2026-08-02).
https://go.dev/ref/mod#versions

**The OSGi component model, used across enterprise Java application servers
and the Eclipse IDE's plugin architecture.** Every OSGi bundle exporting a
package publishes a version for it, and every bundle importing a package
declares an acceptable range, with the OSGi Alliance's own semantic
versioning whitepaper stating the rule that the version of a bundle must
semantically aggregate the semantics of all its constituent packages, an
explicit, specification-level statement of REP's granule-equals-release-unit
requirement (OSGi Alliance, "Semantic Versioning, Bundles and Fragments,"
verified 2026-08-02).
https://docs.osgi.org/whitepaper/semantic-versioning/070-bundles-and-fragments.html

## 10. Consequences

**Positive.**

- A consumer gains a mechanical, automatable way to decide whether upgrading
  a dependency is safe, replacing a manual review of the maintainer's source
  diff with a check against a declared range.
- Independent teams can move at independent speeds. A slow-moving consumer
  is not forced onto every change the moment it lands, and a fast-moving
  consumer is not blocked waiting for every other consumer to catch up.
- Bugs become far easier to localize across an organization, because which
  version of the shared component is running in production becomes an
  answerable question rather than an open one, which shrinks the search
  space when a defect appears in one deployment but not another.
- The discipline forces the maintaining team to think explicitly about
  compatibility every time they change the release unit, which tends to
  surface accidental breaking changes before they ship rather than after a
  consumer reports them.
- A well-versioned release unit becomes genuinely reusable by parties the
  original author never anticipated, which is the entire economic case for
  open-source package ecosystems existing at all.

**Negative.**

- Every release unit is an ongoing maintenance liability. Someone has to run
  the release process, write the changelog, and answer the question of what
  compatibility class a given change belongs to, forever, for as long as the
  component has consumers.
- Version resolution introduces an entire class of failures that a
  single-build application never faces, dependency conflicts where two
  transitive consumers require incompatible ranges of the same package, the
  diamond dependency problem, which the OSGi and Go documentation both
  discuss as a real operational cost their respective mechanisms have to
  manage rather than eliminate (OSGi Alliance, "Semantic Versioning,
  Importer Policy," verified 2026-08-02).
  https://docs.osgi.org/whitepaper/semantic-versioning/060-importer-policy.html
  (Go documentation, "Modules reference, Versions," verified 2026-08-02).
  https://go.dev/ref/mod#versions
- Consumers who pin an overly narrow range, or who never revisit an
  aggressively wide range, accumulate technical debt in the form of stale,
  unpatched dependencies, a cost REP's mechanism makes visible but does not
  by itself prevent anyone from ignoring.
- A codebase that applies REP's full discipline too aggressively, inside a
  single application with no independent consumers, pays every one of the
  costs above for zero corresponding benefit, and tends to accumulate a
  large number of internally-versioned packages that exist purely to satisfy
  a process rather than to solve the coordination problem REP was invented
  for.

## 11. Failure modes and misuse

**The grab-bag "common" or "utils" component, the anti-pattern REP is most
often invoked against.** Symptom. A consumer needs a one-line bug fix to a
string-formatting helper, and to get it, has to accept a new release that
also silently changes the database access layer, the logging configuration,
and three other unrelated concerns bundled into the same package, because
everything the organization ever wanted to share ended up in one
undifferentiated component. Cause. The release unit's boundary was drawn
around things the team might want to reuse someday rather than around things
that genuinely change together and are genuinely used together, violating
REP in spirit even while technically having a version number, because the
version number no longer conveys meaningful information about what actually
changed for a given consumer. Fix. Split the grab-bag along the Common
Closure Principle, group by what changes together, and the Common Reuse
Principle, group by what is used together, instead of along everything
shareable, producing several smaller, independently versioned release units
each of which a consumer can adopt without also inheriting unrelated churn
(this specific failure mode and fix are described directly in Martin's
original article, verified 2026-08-10).
https://objectmentor.com/resources/articles/granularity.pdf

**Reuse by copy-paste, or reuse by pointing at a branch tip.** Symptom. Two
teams' copies of the same formatting logic have quietly diverged, and nobody
can say when or why, because there was never a version number to compare
against. Cause. Source code was shared without ever being released through a
tracking system, satisfying only the reuse half of REP's name and none of
the release half. Fix. Introduce an actual tracking mechanism, even an
internal, unpublished one such as a tagged commit plus a manifest entry, so
that which version a consumer is on becomes an answerable question again.

**Version-number theater.** Symptom. A component's PATCH number increments
constantly, MINOR increments occasionally, and MAJOR has never once
incremented in the component's multi-year history despite the component
having clearly broken consumers at least twice along the way. Cause. The
compatibility contract behind the version number is not actually being
honored. The numbers move but do not encode the truth about what changed,
which strips consumers of the exact safety REP exists to provide while
giving the false appearance that the safety is present. Fix. Treat any
observable, backward-incompatible change to exported behavior as a MAJOR
bump without exception, and hold the maintaining team to that rule with
automated compatibility checking where the ecosystem supports it, rather
than relying on discipline alone.

**The overly narrow range, or the overly wide one.** Symptom, narrow case. A
consumer pinned to an exact version never receives security or bug-fix
patches because upgrading requires a manual, and therefore rarely performed,
edit to the manifest. Symptom, wide case. A consumer's range is wide enough
to silently accept a version the maintainer marked as a MAJOR, incompatible
release, because the range was written carelessly or copied from an example
without understanding its ceiling. Cause. The consumer half of REP's
bargain, expressing a range that genuinely reflects what has actually been
tested against, was not honored. Fix. Default to the ecosystem's standard
range convention, a caret range against the last known-good version is the
common default across npm, Go, and OSGi's importer policy alike, and revisit
it deliberately at each upgrade rather than leaving it static indefinitely or
widening it without re-testing.

**Applying REP where no second consumer exists.** Symptom. A team spends
real engineering time standing up a release process, a changelog, and a
semver policy for an internal module that has exactly one consumer, compiled
in the same build, and the process adds friction to every change with no
corresponding safety benefit anyone can point to. Cause. REP was applied as
a blanket policy rather than as a response to an actual coordination problem
between independently-scheduled consumers. Fix. Fold the module back into
its single consumer's own release unit and revisit the decision only when a
genuine second, independently deployed consumer actually appears.

## 12. Trade-off matrix

The alternatives compared here are not strawmen. They are the concrete,
named approaches a team reaches for instead of, or in addition to, applying
REP.

| Approach | Consumer safety on upstream change | Coordination cost per change | Operational overhead | Suits independently-deployed consumers |
|---|---|---|---|---|
| Release Reuse Equivalence (versioned release unit + range) | High. A version bump the consumer's range rejects is caught by tooling before the change reaches production. | Low, ongoing. The version number itself is the coordination channel, no meeting required per change. | Moderate, ongoing. Requires a real tracking system, a changelog discipline, and a compatibility policy for as long as the component lives. | Yes, this is the case REP is built for. |
| Direct source sharing (copy-paste, or a shared source folder with no version) | None. Divergence between copies is silent and can only be found by manual diffing. | High, sporadic. Coordination happens only when someone notices a bug, after the fact. | Low up front, but hidden cost accumulates as copies drift and someone eventually has to reconcile them. | Poorly. Works only while consumers stay in lockstep by coincidence. |
| Vendoring a pinned, tagged copy | High for the pinned version, but stale until someone manually re-vendors. | Low per change, but the re-vendoring step itself is manual and easily deferred indefinitely. | Low ongoing, no registry required, but no automated notification of new releases either. | Adequately, in ecosystems or contexts where an automated registry is unavailable or undesirable. |
| Single monorepo with one atomic build and no internal versioning | High, because there is only ever one build state. Incompatibility is caught at compile time, not resolved at dependency-resolution time. | Very low for a single team, but scales poorly once independent deploy cadences are actually needed. | Very low, no release process to maintain. | No. This approach is only appropriate when the consumers are not, in fact, independently deployed, which is exactly REP's stated non-applicability case. |
| Common Reuse Principle applied without REP (small, cohesive, but unversioned components) | Low to moderate. Cohesion at the class level reduces accidental coupling, but with no version contract a consumer still cannot mechanically detect a breaking change. | Moderate. Smaller components mean smaller blast radius per change, but the lack of a version signal still forces manual investigation of what changed. | Low, since there is no release machinery to run. | Weakly. Solves the problem of dragging in unused capability that CRP addresses, but leaves REP's coordination problem unsolved. |

## 13. Related and incompatible patterns

**Common Closure Principle (CCP) and Common Reuse Principle (CRP).** These
three principles form Martin's tension diagram and are never fully
understood in isolation from each other. REP and CCP both pull a design
toward larger, more inclusive components, REP because grouping related,
independently-versioned things reduces the number of release processes a
team has to run, and CCP because things that change for the same reason
belong together so a single reason-for-change touches a single component.
CRP pulls in the opposite direction, toward smaller, more exclusive
components, because a consumer should never be forced to depend on
capabilities it does not actually use just because those capabilities
happened to live in the same release unit. An architect draws the component
boundary somewhere inside this three-way tension, and Martin is explicit
that the correct answer moves over the life of a project as the dominant
concern shifts from ease of development toward ease of reuse (tension
diagram and its evolution over a project's life confirmed via independent
chapter summary, verified 2026-08-02).
https://groups.google.com/g/clean-code-discussion/c/1qSCb_EDYYU

**Semantic versioning.** REP states that a release unit must be versioned
and tracked. Semantic versioning is the specific, dominant contract that
gives the version number a shared, checkable meaning. The two compose
directly. REP without a real compatibility contract behind its version
numbers degenerates into the version-number-theater failure mode described
above.

**Single Responsibility Principle, applied one level up.** SRP, at the class
level, states a class should have one reason to change. REP is best
understood as the same underlying instinct, applied one level of granularity
up. A release unit should have one release story, not several unrelated
reasons for a consumer to need a new version of it.

**Dependency Inversion Principle.** DIP and REP address different axes of
the same overall problem of managing dependencies between independently
evolving pieces of software. DIP is about the direction a dependency points,
toward an abstraction rather than a concretion. REP is about the granularity
and trustworthiness of the concrete artifact that gets depended on, whichever
direction the dependency points. A component can honor DIP internally while
still failing REP externally, by exposing a beautifully abstracted interface
through an unversioned, untracked source tree.

**Incompatible with, in the sense of actively working against.** Nothing in
this catalog is REP's opposite in the way that, for instance, tight coupling
opposes low coupling. The closest thing to an incompatible stance is the
deliberate choice to keep a piece of code as an unreleased, unversioned,
single-consumer implementation detail, which is not a competing principle so
much as REP's own stated non-applicability case. Some code should not be
promoted to a release unit at all, and treating it as one anyway is the
misapplication described in section 11, not a rival design philosophy.

## 14. Refactoring path in and out

**Introducing REP into code that does not yet have it.** Start from the
observation that a piece of source code now has, or will soon have, a second
consumer on a different deployment schedule than the first. First, identify
the smallest cohesive group of classes that changes together for the same
reasons, apply CCP, and that a consumer would actually want all of, not just
part of, apply CRP. This group, not the whole shared folder it currently
lives inside, is the candidate release unit. Second, extract that group into
its own buildable, independently testable module, with its own manifest
file. Third, stand up the tracking mechanism appropriate to the ecosystem, a
private or public package registry entry, a Go module path, an OSGi bundle
manifest, or at minimum a disciplined git tag convention plus a changelog
file addressed to consumers. Fourth, cut an initial release, typically
`0.1.0` or `1.0.0` depending on how stable the interface already is, and
update every existing consumer to declare an explicit dependency on that
release rather than continuing to reference the source directly. Fifth,
adopt and document a compatibility policy, almost always semantic
versioning, and hold every future change to it before that change is
released. The single largest risk in this refactoring is drawing the release
unit's boundary too widely on the first attempt, recreating the grab-bag
failure mode from section 11 with a version number bolted on. Keep the first
extraction as narrow as the current, real consumers actually need, and widen
it later only in response to an actual second use case, not a speculative
one.

**Removing REP once it has stopped earning its place.** This happens most
often when a release unit's consumer count drops back to one, typically
because sibling consumers were retired or merged, and the ongoing cost of
running a release process for a single-consumer module stops being justified
by any coordination benefit it is providing. The path out is the mirror of
the path in. Confirm no second consumer is expected to appear in the
foreseeable future, fold the module's source directly back into its one
remaining consumer's own build, remove the standalone manifest and release
tracking, and archive rather than delete the old release history so that if
a second consumer does appear later, the prior versioning discipline and
compatibility record are not lost. Watch for the same signal this catalog's
Common Closure and Common Reuse entries flag. If the module's version
history shows long stretches with no releases at all, that is often a sign
the release unit outlived its second consumer well before anyone noticed,
and the versioning ceremony has been pure overhead for some time.

## 15. Testing and verification

REP itself is not directly unit-testable in the way a class's behavior is,
because it is a statement about process and packaging rather than about
runtime logic, but it produces several concretely verifiable properties that
should be checked as part of a release unit's own build and release
pipeline.

Verify that the release unit's declared version genuinely matches the
compatibility class of the change it accompanies. This is best done with an
automated API-compatibility checker specific to the language ecosystem,
examples include `api-extractor` reports diffed across releases for
TypeScript, `pkgsite`'s API diff tooling or a `golangci-lint` compatibility
check for Go, and OSGi's own `bnd` tool, which computes and enforces semantic
version bumps directly from binary compatibility analysis, as documented in
the bnd project's own versioning chapter, verified 2026-08-02.
https://bnd.bndtools.org/chapters/170-versioning.html
A test suite that merely exercises the release unit's own functionality,
without also checking that its version number is consistent with what
changed, verifies the component but not the release contract REP depends on.

Verify that every consumer's declared dependency range actually resolves to
a version the consumer has been tested against, not merely a version the
range happens to permit. A wide range that has never been exercised against
the newest version it technically allows is an untested assumption, not a
verified compatibility, and should be caught in continuous integration by
building and testing each consumer against the actual resolved version on
every run rather than against a stale, locally cached one.

Verify, at the release-unit level, that a PATCH release changes no exported
behavior at all, that a MINOR release changes exported behavior only
additively, and that a MAJOR release is the only category permitted to
remove or alter existing exported behavior. Contract tests written against
the release unit's public surface, run before every release is tagged, are
the standard technique here. A failing contract test on what was intended to
be a PATCH or MINOR release is a signal that the compatibility class was
mis-declared, not that the test is wrong.

Test doubles are of limited use for verifying REP itself, since the
principle concerns the relationship between real, released artifacts rather
than in-process collaborators, but a fake registry or fake package resolver
used in integration tests of the consumer's build tooling can usefully
simulate a range of upstream release scenarios, including a simulated MAJOR
bump, to confirm the consumer's own tooling correctly refuses to silently
absorb an incompatible change.

## 16. Observability signals

A healthy release unit shows a steady, low-drama cadence of PATCH and MINOR
releases, with MAJOR releases rare, deliberate, and each accompanied by a
migration note in the changelog. The version history reads as a legible
narrative of the component's evolution rather than an erratic sequence of
unexplained jumps.

A failing or unhealthy instance of the pattern shows one or more of these
signals. A version number that has not moved in a very long time while the
underlying source has continued to change, which indicates the release
process has silently stopped running even though development has not. A
sudden cluster of downstream consumer incidents immediately following a
release that was tagged as a MINOR or PATCH bump, which indicates the
compatibility class was mis-declared for that release. A dependency graph in
which many consumers are pinned to versions several MAJOR releases behind
current, which indicates the upgrade cost has grown large enough that
consumers are avoiding it, itself often a sign that past MAJOR releases were
not accompanied by adequate migration guidance. And a release unit whose
changelog entries describe internal refactoring detail rather than the
externally visible effect of each change, which indicates the changelog is
being written for the maintainers rather than for the consumers it exists to
inform.

Concretely, dashboards or reports worth building around a release unit
include a distribution of which version each known consumer currently
resolves to, to spot version fragmentation, the elapsed time between a
release being tagged and its adoption by each consumer, to spot upgrade
friction, and a count of incidents or rollbacks correlated against which
compatibility class the triggering release was tagged with, to spot
mis-declared compatibility classes before they recur.

## 17. Security and privacy implications

REP's central mechanism, resolving a consumer's declared range against
whatever the tracking system currently offers as the highest satisfying
version, is also the mechanism behind one of the more consequential classes
of software supply-chain attack. An attacker who compromises a package
registry account can publish a malicious release under a version number a
huge number of existing consumers will silently and automatically resolve
to, precisely because REP's design goal is for that resolution to happen
without any human review at the consumer end. This is not a flaw unique to
REP as a design principle. It is the direct, mechanical cost of the exact
automatic-adoption benefit the principle provides, and it means any
organization relying on REP-style automatic version resolution needs a
complementary control, such as lockfile pinning combined with deliberate,
reviewed upgrades, or provenance and signature verification on published
releases, layered on top of the bare version-range mechanism rather than
relying on the range alone as a security boundary.

A second, quieter implication concerns the changelog and version history
themselves. Because REP treats the version history as a communication
channel to external consumers, that history is also externally visible by
design, which means it is generally the wrong place to record internal
details, such as which internal system or client triggered a particular fix,
that were not intended for a public or cross-team audience. A changelog
entry written carelessly for an internal audience can leak organizational or
client information to every downstream consumer of a public release unit.

REP carries no direct data-handling implication beyond these two. It is a
principle about packaging and versioning, not about what data a component
processes, and this entry does not invent a privacy concern where the
principle itself is silent on one.

## 18. References

- Martin, Robert C. "Granularity." C++ Report, Nov/Dec 1996, SIGS
  Publications Group. PDF mirror verified 2026-08-02.
  https://condor.depaul.edu/dmumaugh/OOT/Design-Principles/granularity.pdf
- Martin, Robert C. *Agile Software Development, Principles, Patterns, and
  Practices*. Prentice Hall (Alan Apt Series), 2002. Chapter 28, "Principles
  of Package and Component Design." Listing verified 2026-08-02.
  https://www.amazon.com/Software-Development-Principles-Patterns-Practices/dp/0135974445
- Martin, Robert C. *Clean Architecture, A Craftsman's Guide to Software
  Structure and Design*. Prentice Hall, 2018. Chapter 13, "Component
  Cohesion." Table of contents verified 2026-08-02.
  https://www.oreilly.com/library/view/clean-architecture-a/9780134494272/ch13.xhtml
- "Clean Architecture Chapter 13, Component Cohesion" (chapter summary
  including the REP, CCP, CRP tension diagram). Verified 2026-08-02.
  https://groups.google.com/g/clean-code-discussion/c/1qSCb_EDYYU
- "Clean Architecture, Chapter 13, Component Cohesion" (chapter summary and
  quoted definitions of REP, CCP, and CRP). Verified 2026-08-02.
  https://www.letscodethemup.com/clean-architecture-chapter-13-component-cohesion/
- Robert C. Martin. "Granularity." Original 1996 article coining REP, CCP,
  and CRP. Verified 2026-08-10 (the secondary "Reuse/Release Equivalence
  Principle" commentary on Code Coach formerly cited here has since gone
  dark, connection refused on the live host, checked directly, via curl,
  and against the Wayback Machine, no snapshot exists; this primary source
  replaces it).
  https://objectmentor.com/resources/articles/granularity.pdf
- Wikipedia contributors. "Package principles." Verified 2026-08-02.
  https://en.wikipedia.org/wiki/Package_principles
- Preston-Werner, Tom. "Semantic Versioning 2.0.0." Verified 2026-08-02.
  https://semver.org/
- "Semver explained, why is there a caret in my package.json." Verified
  2026-08-02.
  https://bytearcher.com/articles/semver-explained-why-theres-a-caret-in-my-package-json/
- Go documentation. "Modules reference, Versions." Verified 2026-08-02.
  https://go.dev/ref/mod#versions
- OSGi Alliance. "Semantic Versioning, Semantic Versions." Verified
  2026-08-02.
  https://docs.osgi.org/whitepaper/semantic-versioning/040-semantic-versions.html
- OSGi Alliance. "Semantic Versioning, Importer Policy." Verified 2026-08-02.
  https://docs.osgi.org/whitepaper/semantic-versioning/060-importer-policy.html
- OSGi Alliance. "Semantic Versioning, Bundles and Fragments." Verified
  2026-08-02.
  https://docs.osgi.org/whitepaper/semantic-versioning/070-bundles-and-fragments.html
- bnd project documentation. "Versioning." Verified 2026-08-02.
  https://bnd.bndtools.org/chapters/170-versioning.html

## Code examples

Each example models a release unit's compatibility check. Given a candidate
version and the floor of a consumer's declared caret range, decide whether
the candidate is safe to resolve to, mirroring the rule npm's caret range,
Go's semantic import versioning, and OSGi's importer policy all implement.
All three were compiled or run directly against the toolchains listed in the
template. None needed a workaround.

### TypeScript

```typescript
interface ReleaseUnit {
  name: string;
  version: string;
  exports: string[];
}

function parseVersion(v: string): [number, number, number] {
  const parts = v.split(".").map(Number);
  if (parts.length !== 3 || parts.some((n) => Number.isNaN(n))) {
    throw new Error(`not a semantic version: ${v}`);
  }
  return [parts[0], parts[1], parts[2]];
}

function satisfiesCaretRange(version: string, floor: string): boolean {
  const [vMajor, vMinor, vPatch] = parseVersion(version);
  const [fMajor, fMinor, fPatch] = parseVersion(floor);
  if (vMajor !== fMajor) return false;
  if (vMinor !== fMinor) return vMinor > fMinor;
  return vPatch >= fPatch;
}

const notifications: ReleaseUnit = {
  name: "notifications",
  version: "2.3.1",
  exports: ["EmailSender", "SmsSender", "PushSender"],
};

const consumerFloor = "2.1.0";
console.log(
  `consumer built against ^${consumerFloor} can reuse ${notifications.name}@${notifications.version}: ` +
    satisfiesCaretRange(notifications.version, consumerFloor),
);

const breaking = "3.0.0";
console.log(
  `consumer built against ^${consumerFloor} can reuse ${notifications.name}@${breaking}: ` +
    satisfiesCaretRange(breaking, consumerFloor),
);
```

Compiled with `npx tsc --target es2020 --module commonjs` and run with
`node`. Output.

```text
consumer built against ^2.1.0 can reuse notifications@2.3.1: true
consumer built against ^2.1.0 can reuse notifications@3.0.0: false
```

### Python

```python
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class ReleaseUnit:
    name: str
    version: str
    exports: List[str] = field(default_factory=list)


def parse_version(v: str) -> Tuple[int, int, int]:
    parts = v.split(".")
    if len(parts) != 3:
        raise ValueError(f"not a semantic version: {v}")
    major, minor, patch = (int(p) for p in parts)
    return major, minor, patch


def satisfies_caret_range(version: str, floor: str) -> bool:
    v_major, v_minor, v_patch = parse_version(version)
    f_major, f_minor, f_patch = parse_version(floor)
    if v_major != f_major:
        return False
    if v_minor != f_minor:
        return v_minor > f_minor
    return v_patch >= f_patch


if __name__ == "__main__":
    notifications = ReleaseUnit(
        name="notifications",
        version="2.3.1",
        exports=["EmailSender", "SmsSender", "PushSender"],
    )
    consumer_floor = "2.1.0"
    print(
        f"consumer built against ^{consumer_floor} can reuse "
        f"{notifications.name}@{notifications.version}: "
        f"{satisfies_caret_range(notifications.version, consumer_floor)}"
    )
    breaking = "3.0.0"
    print(
        f"consumer built against ^{consumer_floor} can reuse "
        f"{notifications.name}@{breaking}: "
        f"{satisfies_caret_range(breaking, consumer_floor)}"
    )
```

Run with `python3`. Output.

```text
consumer built against ^2.1.0 can reuse notifications@2.3.1: True
consumer built against ^2.1.0 can reuse notifications@3.0.0: False
```

### Go

```go
package main

import (
	"fmt"
	"strconv"
	"strings"
)

type ReleaseUnit struct {
	Name    string
	Version string
	Exports []string
}

func parseVersion(v string) (int, int, int, error) {
	parts := strings.Split(v, ".")
	if len(parts) != 3 {
		return 0, 0, 0, fmt.Errorf("not a semantic version: %s", v)
	}
	nums := make([]int, 3)
	for i, p := range parts {
		n, err := strconv.Atoi(p)
		if err != nil {
			return 0, 0, 0, fmt.Errorf("not a semantic version: %s", v)
		}
		nums[i] = n
	}
	return nums[0], nums[1], nums[2], nil
}

func satisfiesCaretRange(version, floor string) bool {
	vMajor, vMinor, vPatch, err1 := parseVersion(version)
	fMajor, fMinor, fPatch, err2 := parseVersion(floor)
	if err1 != nil || err2 != nil {
		return false
	}
	if vMajor != fMajor {
		return false
	}
	if vMinor != fMinor {
		return vMinor > fMinor
	}
	return vPatch >= fPatch
}

func main() {
	notifications := ReleaseUnit{
		Name:    "notifications",
		Version: "2.3.1",
		Exports: []string{"EmailSender", "SmsSender", "PushSender"},
	}
	consumerFloor := "2.1.0"
	fmt.Printf("consumer built against ^%s can reuse %s@%s: %v\n",
		consumerFloor, notifications.Name, notifications.Version,
		satisfiesCaretRange(notifications.Version, consumerFloor))

	breaking := "3.0.0"
	fmt.Printf("consumer built against ^%s can reuse %s@%s: %v\n",
		consumerFloor, notifications.Name, breaking,
		satisfiesCaretRange(breaking, consumerFloor))
}
```

Run with `go run`. Output.

```text
consumer built against ^2.1.0 can reuse notifications@2.3.1: true
consumer built against ^2.1.0 can reuse notifications@3.0.0: false
```

Java, Rust, C#, and Kotlin are omitted here because the compatibility-range
check the samples demonstrate is language-neutral logic with no
language-idiomatic variant worth adding a fourth near-identical
implementation for. The three languages above already span a static,
compiled, class-based style, TypeScript, a dynamic, script-run style,
Python, and a statically compiled, non-object-oriented style with explicit
error returns, Go, which covers the range of idioms this particular
demonstration has anything new to say in.
