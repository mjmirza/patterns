---
name: Acyclic Dependencies Principle
slug: acyclic-dependencies-principle
family: 04-principles-and-laws
category: Design Principle
aliases: [ADP, No Cyclic Dependencies, Component Coupling Principle]
first_described: "Robert C. Martin, Design Principles and Design Patterns, 2000"
maturity: canonical
related: [dependency-inversion-principle, interface-segregation-principle, single-responsibility-principle, low-coupling, high-cohesion, factory-method]
incompatible_with: []
verified: 2026-08-02
---

# Acyclic Dependencies Principle

## 1. Name, aliases, and lineage

The canonical name is the Acyclic Dependencies Principle, almost always
shortened to ADP. It states that the dependency graph of packages,
components, or modules in a software system must contain no cycles, so that
following the arrows from any node and back to that node is never possible
(summary of the principle statement, [Wikipedia, Acyclic dependencies
principle](https://en.wikipedia.org/wiki/Acyclic_dependencies_principle),
verified 2026-08-02).

Robert C. Martin wrote the principle down as one of three coupling
principles for packages, alongside the Stable Dependencies Principle and the
Stable Abstractions Principle, in the paper "Design Principles and Design
Patterns," which Martin published in the year 2000 and which Wikipedia's own
entry on the principle cites as the source of the statement that "the
dependency graph of packages or components should have no cycles" ([Wikipedia,
Acyclic dependencies
principle](https://en.wikipedia.org/wiki/Acyclic_dependencies_principle),
verified 2026-08-02). Martin restated the same three coupling principles
seventeen years later in Part IV, "Component Principles," in the chapter
titled "Component Coupling," of his book *Clean Architecture. A Craftsman's
Guide to Software Structure and Design*, Prentice Hall, 2017 (chapter and
part title confirmed by multiple independent reading summaries of the
book's table of contents, verified 2026-08-02).

No community uses a different name for the principle itself. What varies is
the unit the principle is applied to. The original 2000 paper and the 2017
book both write it in terms of packages, because Martin's working definition
of a package in that era is a releasable unit, something a team version
controls and ships as one. Contemporary usage extends the same statement to
Java packages, Swift and Kotlin modules, npm packages, Go packages, Gradle or
Maven modules, and Bazel or Buck build targets, because every one of those
units is, in the relevant sense, a releasable or buildable node in a
dependency graph. The principle does not change shape when the unit changes
name, only the tool that enforces it changes.

A companion phrase that shows up in secondary writing about this principle
is the "morning after syndrome." A developer stays late to finish a change,
comes back the next morning, and finds the change no longer compiles or no
longer passes tests, because someone else, working in a different part of a
cyclically coupled dependency graph, checked in an unrelated change
overnight that reached back around the cycle and touched the same code
(paraphrase of the informal description of the syndrome and its root cause
in a cyclic dependency graph, [summary discussion of the principle and the
morning after syndrome, via the Wayback Machine snapshot](https://web.archive.org/web/2/https://karandhillon95.medium.com/the-morning-after-syndrome-4e49096156ed),
verified 2026-08-10; Medium now returns a bot-block to automated requests
on the live host, checked directly against the same probe this catalogue's
validator uses, so the archived snapshot is cited in its place). The name
is memorable because the pain it describes
happens to a person who did nothing wrong themselves. Their code broke
because the graph they depend on, indirectly, loops back through their own
work.

## 2. Problem and context

A codebase of any real size is not one file. It is partitioned into units,
packages, modules, libraries, services, whatever the platform calls them.
Each unit imports, requires, or otherwise depends on some other units to do
its job. Draw an arrow from a unit to every unit it depends on and the whole
codebase becomes a directed graph.

The problem ADP addresses appears the moment two units depend on each other,
directly or through a chain. Unit A imports unit B, unit B imports unit C,
and unit C imports unit A. Nothing in that description says the code is
wrong in a functional sense. The classes might all compile, in a language
that permits it, and the tests might all pass. The problem is structural,
not functional, and it shows up under three conditions that separate real
production systems from a classroom exercise. more than one person or team
working in the codebase, the codebase being released or deployed in
independently buildable pieces, and the codebase living long enough that
"independently buildable pieces" needs to remain true across many changes.

Under those three conditions a cycle turns the units inside it into one
undividable unit for every purpose that matters. They must be built
together, because building A requires C, which requires B, which requires A.
They must be tested together, because a change anywhere in the cycle can
alter behavior anywhere else in the cycle through a path a reviewer of the
immediate diff cannot see without reading the whole loop. They must be
released together, because there is no version of A that is compatible with
an arbitrary version of C without also being compatible with the specific
version of B that C was compiled against, and vice versa in every direction
around the loop.

This context is the one that ADP is written for. any codebase organized
into more than one buildable, testable, or releasable unit, worked on by
more than one contributor, over a lifespan long enough for the units to
evolve independently of each other. A single-file script, a proof of
concept, or a monolith that is genuinely never going to be decomposed, sits
outside this context and is addressed under dimension 4.

## 3. Forces

Judgement. The following is engineering reasoning about which pressures
matter most, not a sourced claim about a specific system.

Four forces pull against each other whenever a dependency between two units
is being decided.

**Convenience of reuse versus independence of release.** The easiest thing
for a developer to do, when a function they need already exists in another
unit, is to import that unit. Reuse is good in isolation. The force that ADP
pushes back against is reuse pursued without regard for the direction of the
resulting arrow. An import that closes a cycle buys local convenience today
at the cost of coupling every future release of both units together,
forever, until someone pays down the cycle.

**Team topology versus code topology.** When two teams each own one side of
a cyclic pair, every change either team makes can, through the cycle, affect
work the other team is doing at the same time. This is the direct cause of
the morning after syndrome. ADP favors a code topology that mirrors a team
topology of independent, parallel work, over a code topology that happens to
be the shortest path to a working feature this week.

**Compile and test time versus abstraction cost.** Breaking a cycle
frequently means introducing a new abstraction, an interface, or a third
package that both former cycle members now depend on instead of on each
other. That third package is a real cost. It is another file, another name
to learn, one more level of indirection between the caller and the concrete
implementation. ADP accepts that cost in exchange for a dependency graph
that a build system can order, cache, and partially rebuild, instead of one
massive unit that must be rebuilt and retested in full on every change.

**Local optimality versus global structure.** A single import, viewed only
at the two endpoints, almost always looks harmless when the reasoning stops
at "this one function is all I need from the other package." The force ADP names is that the graph-level property, acyclicity,
is not visible from either endpoint of a single edge. A developer adding the
edge that finally closes a large, indirect cycle across a dozen packages
has, from their local view, done nothing different from any other import
they have written before. ADP is a principle precisely because the harm is
invisible locally and visible only in aggregate, which is why it must be
checked mechanically rather than trusted to individual judgement at the
point of each edge.

ADP resolves these forces in favor of graph structure over local
convenience. It accepts more files, more indirection, and more up-front
design cost, in exchange for a codebase whose units can be built, tested,
and released independently of each other, indefinitely, as the system
grows.

## 4. Applicability and non-applicability

Reach for ADP, and for the mechanical enforcement described in dimension 8,
when the following hold.

- The codebase is split into more than one buildable, testable, or
  publishable unit, packages, modules, services, or libraries, in any
  combination.
- More than one person, or more than one team, contributes to the codebase
  concurrently.
- Units need to be released, deployed, or versioned on schedules that are
  not always identical, even if that independence is only exercised
  occasionally.
- The codebase is expected to live and grow over a period long enough that
  build times, test times, and change isolation become a measurable cost.
- A build or dependency tool exists, or can be introduced, that is capable
  of computing the dependency graph and reporting a cycle. Enforcing ADP
  without such a tool degrades to hoping every contributor remembers a rule
  that is, by its own forces above, invisible at the point of any single
  edit.

Do not apply ADP, or do not treat a detected cycle inside these boundaries
as a defect requiring the same fix, when the following hold.

- **A single file or a single compilation unit with no internal package
  boundary.** ADP is a statement about the graph of packages or components.
  A function calling another function inside the same file is not an edge in
  that graph. There is nothing to be acyclic or cyclic about.
- **Mutual recursion between two functions or two classes that are, by
  design, one cohesive unit and are always built, tested, and released
  together.** A parser's expression and statement grammar rules routinely
  call each other by mutual recursion within one module. That module-level
  cohesion is exactly what ADP asks the developer to draw the package
  boundary around, so the recursive calls stay inside one node of the graph
  rather than becoming an edge between two nodes.
- **A genuine one-shot prototype or throwaway script with no plan for
  independent release of its parts.** Paying the cost of an extra
  abstraction layer, described under dimension 3, to satisfy a graph
  property that will never be checked by a second contributor or a second
  release, is waste.
- **Bidirectional protocols that are symmetric by design, such as a
  request-response contract shared by a client and a server in the same
  monorepo, where the shared contract lives in its own package that neither
  side depends on the other for.** The correct structure here is client and
  server both depending on the shared contract package, never depending on
  each other. Treating that shared-contract package as the two callers
  "cyclically" needing each other is a misreading of the actual graph. The
  real graph, contract as a separate node, is already acyclic. The
  non-applicability is that ADP is not violated here at all once the graph
  is drawn correctly, so no special exemption is being made, but the case is
  listed because it is the one most often mistaken for a necessary,
  tolerated cycle.
- **A vendored or generated dependency graph outside your control**, for
  example transitive dependencies inside a third-party library's own
  package structure. ADP is a principle for the graph you author. A cycle
  discovered deep inside a vendored dependency's own internals is that
  vendor's defect, not yours, though it is still worth reporting or avoiding
  that dependency if the cycle causes observable pain in your build.

## 5. Structure

ADP has no participants in the sense of collaborating runtime objects, the
way a design pattern such as Observer or Strategy does. Its structure is a
static graph, and the roles are graph-theoretic.

- **Node.** A unit of release. a package, a module, a component, a library,
  or a build target, depending on the platform. Each node is expected to be
  independently buildable and, ideally, independently testable and
  releasable.
- **Edge, the "depends upon" relation.** A directed arrow from a node to
  another node that it imports, requires, links against, or otherwise needs
  present to compile or run. Bazel's own documentation frames this
  precisely, stating that "the depends upon relation induces a Directed
  Acyclic Graph over targets" (exact phrase, [Bazel, Concepts and
  terminology, Dependency
  graph](https://bazel.build/concepts/dependencies), verified 2026-08-10).
- **Dependency graph.** The complete set of nodes and edges for the system
  under study. ADP is a property claimed about this graph as a whole, never
  about any single edge examined in isolation.
- **Cycle.** A sequence of one or more edges that starts and ends at the
  same node. The shortest possible cycle has two nodes, A depends on B and B
  depends on A. Longer cycles, involving three, five, or dozens of nodes
  chained together, are structurally identical in effect and are the harder
  case to see by inspection, which is why dimension 8 covers automated
  detection rather than manual review.
- **Cycle-breaking mechanism.** When an existing or proposed cycle must be
  removed, one of two structural moves is used. Either an interface is
  extracted so the arrow that used to point "backward" now points to an
  abstraction that both former cycle members depend on, which is the
  Dependency Inversion Principle applied at the package level, or a third
  package is created to hold the code that both original packages need,
  which removes the reason for either to depend on the other directly. Both
  moves are covered in depth under dimension 14.

## 6. ASCII structure diagram

```
BEFORE, a cycle across three packages

  +------------+       +------------+
  |    ui      | ----> |   domain   |
  +------------+       +------------+
        ^                     |
        |                     v
        |               +------------+
        +-------------- |    data    |
                         +------------+

  ui -> domain -> data -> ui   (cycle, length 3)


AFTER, broken by extracting an interface package

  +------------+       +------------+
  |    ui      | ----> |   domain   |
  +------------+       +------------+
                              |
                              v
                        +------------+
                        |  data-api  |  (interface only)
                        +------------+
                              ^
                              |
                        +------------+
                        |    data    |
                        +------------+

  ui -> domain -> data-api  (acyclic)
  data -> data-api          (implements, no back-edge to domain)
```

The interface package `data-api` declares the storage contract that
`domain` needs. `domain` depends on `data-api`, never on the concrete
`data` package. `data` depends on `data-api` too, to implement it, but has
no arrow back toward `domain` or `ui`. Following any arrow from any node in
the AFTER graph never leads back to the node it started from.

## 7. Dynamics

ADP is a static property, checked before or during a build rather than
observed at runtime, so its "dynamics" are the dynamics of a build and
release pipeline rather than of running objects passing messages.

```
1. Developer edits package X, adds an import of package Y.
2. Build tool (or a dedicated dependency checker) recomputes the
   dependency graph including the new edge X -> Y.
3. Graph is checked for cycles, typically via a depth-first traversal
   that colors each node white (unvisited), gray (on the current
   path), or black (fully explored).
4. IF a gray node is reached again while traversing from itself:
     a cycle exists. The checker reports the cycle path and the
     build (or the CI job, or the pre-commit hook) fails before
     the change is merged.
5. IF no gray node is revisited:
     the graph remains acyclic. The topological order of nodes is
     computable, which drives the build order (compile leaves of
     the graph first, then the nodes that depend on them) and the
     release order (a leaf package can ship a new version without
     waiting on anything above it in the graph).
6. Independent release. Package Y at version 2.3 ships. Every
   package that depends on Y, directly or transitively, can adopt
   2.3 on its own schedule, because no arrow points from Y back
   toward any of them.
```

Step 4 is the moment the "morning after syndrome" from dimension 1 is
prevented mechanically rather than discovered painfully. A checker that
runs on every proposed change, described under dimension 8, turns the
cycle-introducing edit into a build failure at the moment it is proposed,
instead of a mystery breakage discovered by an unrelated developer the next
day.

## 8. Implementation variants

Judgement. The relative merits of each variant below are drawn from
engineering practice, not a single sourced ranking.

**Compiler-enforced acyclicity.** The strongest variant. the language
toolchain itself refuses to build a cyclic dependency graph, so ADP cannot
be violated between packages, full stop, no separate tool required. Go is
the clearest example. The Go compiler rejects an import cycle between
packages with the literal error "import cycle not allowed" ([golang/go
issue #28845, "Getting ERROR 'import cycle not allowed' when import
package"](https://github.com/golang/go/issues/28845), verified 2026-08-02,
also reproduced directly for this entry, see dimension 9). Rust's crate
system and, for a single crate, its module system, apply the same
compile-time rejection. This variant costs nothing to maintain, because
there is no separate check to keep passing. It costs design flexibility,
because a language that forbids cycles between its own units also forbids
the legitimate mutual-recursion-within-one-cohesive-unit case from dimension
4, forcing that case to live inside a single package rather than be split
further.

**Build-graph-enforced acyclicity.** The build system itself is defined as
a directed acyclic graph over targets, and a cyclic target dependency is a
build configuration error, not a compile error inside any one target. Bazel
states this directly, defining the dependency graph as a DAG over targets
([Bazel, Concepts and
terminology](https://bazel.build/concepts/dependencies), verified
2026-08-10). This variant applies at a coarser grain than the language
compiler variant. It can catch a cycle across languages, across services, or
across targets that a single-language compiler has no visibility into,
because the compiler only sees its own language's import statements while
the build graph sees every declared target dependency regardless of
language.

**Metrics-and-report tooling run in CI.** For languages and build systems
that do not forbid cycles themselves, a separate analyzer computes the
dependency graph from the compiled artifacts or the source and reports any
cycle it finds, typically as part of a broader package-quality report. The
canonical example for Java package tooling is JDepend, written by Mike Clark,
which the project itself describes as generating "design quality metrics"
for Java packages, with cycle detection runnable "automatically...by a
JUnit test" so the check runs on every build ([clarkware/jdepend README and
docs](https://github.com/clarkware/jdepend), verified 2026-08-02). This
variant is weaker than the previous two because it is opt-in. nothing stops
a developer from merging a cyclic change if the CI job that runs the
analyzer is skipped, misconfigured, or its failure is ignored, which is why
the strongest deployments wire the check as a required, blocking CI gate
rather than an informational report.

**Manual convention with code review as the only gate.** The weakest
variant, and one dimension 3 explains is structurally unreliable. humans
are asked to keep the dependency graph acyclic by inspection alone, with no
tool computing or checking the graph. This variant is common in smaller
codebases and in languages without strong package boundaries, such as a
large single npm package with deep internal folder nesting and no
enforced module boundary. It routinely fails at the scale and team-size
threshold described in dimension 2, because the harm of any single edge is
invisible locally.

**Dependency-inversion refactor as an implementation technique, not a
separate variant of enforcement.** Whichever detection variant is used, the
technique for fixing a detected cycle is consistent. extract a shared
abstraction that both former cycle participants depend on, so no edge points
"backward." This is covered fully under dimension 14.

## 9. Known production uses

**The Go compiler, rejecting package import cycles at compile time.**
Verified directly for this entry. a two-package Go module was constructed
where package `order` imports package `invoice` and package `invoice`
imports package `order`. Running `go build ./...` against that module on
2026-08-10 produced this output.

```text
package adpdemo/invoice
	imports adpdemo/order from invoice.go
	imports adpdemo/invoice from order.go: import cycle not allowed
```

This is the Go language specification's package-import model in effect. The
toolchain computes the package dependency graph before compilation and
refuses to proceed if it contains a cycle, structurally enforcing ADP for
every Go program that exists, not as an opt-in linter but as a hard
compilation failure (transcript reproduced by direct execution 2026-08-10;
the same error class is also independently documented at [golang/go
issue #28845](https://github.com/golang/go/issues/28845), verified 2026-08-02).

**JDepend, the Java package dependency analyzer.** JDepend, written by Mike
Clark of Clarkware Consulting and published as open source, scans compiled
Java `.class` and `.jar` files and computes package-level design metrics
directly derived from Robert Martin's package principles, including cycle
detection between packages that "can be automatically checked by a JUnit
test," letting teams run the acyclicity check as part of every build
([clarkware/jdepend on
GitHub](https://github.com/clarkware/jdepend), verified 2026-08-02). JDepend
predates most modern static analysis suites and is the tool most directly
descended from Martin's own package-coupling metrics, since its design
metrics were explicitly built to operationalize the principles Martin first
described.

**Bazel's target dependency graph.** Google's Bazel build system, used to
build Google's own internal monorepo among many other large codebases,
defines its core dependency model as a Directed Acyclic Graph over build
targets, stating plainly that "the depends upon relation induces a Directed
Acyclic Graph (DAG) over targets, and it is called a dependency graph"
([Bazel, Concepts and terminology](https://bazel.build/concepts/dependencies),
verified 2026-08-10). Because Bazel's own build-order and incremental-rebuild
algorithms are defined in terms of this DAG, a proposed target dependency
that would introduce a cycle is rejected by the tool before a build plan
can even be constructed, making ADP a structural precondition of using
Bazel at all rather than a style guideline layered on top of it.

## 10. Consequences

**Positive.**

- **Independent buildability.** Any node in an acyclic graph can be built
  once every node it transitively depends on has been built, and the graph
  guarantees that process terminates, because there is no cycle to loop
  forever around. This is the mathematical property, a DAG always admits a
  topological order, that a build tool relies on to schedule work and to
  parallelize builds of independent subgraphs.
- **Independent releasability.** A leaf node, or any node whose dependents
  are willing to move at their own pace, can publish a new version without
  coordinating a simultaneous release of everything it touches, because
  nothing it depends on needs to change in lockstep with it.
- **Localized change impact.** When the graph is acyclic, the set of nodes
  a given change can possibly affect is exactly the set reachable by
  following dependency edges from the changed node, a finite and computable
  set. In a cyclic graph, that reachable set can, in the worst case, be the
  entire cycle plus everything downstream of the cycle, because the cycle
  collapses every node inside it into one unit for impact-analysis
  purposes.
- **Faster incremental builds and tests.** Build tools that understand the
  graph, whether via a compiler as in Go or a build system as in Bazel, can
  skip rebuilding and retesting nodes whose transitive dependencies did not
  change. A cycle destroys this optimization for every node caught inside
  it, because "did not change" can no longer be evaluated per node. The
  whole cycle must be treated as one unit.

**Negative.**

- **Design cost of extra abstraction.** Breaking or preventing a cycle
  frequently requires introducing an interface package or a shared
  abstraction, described in dimension 6's AFTER diagram, that did not exist
  before. That is one more artifact for every future reader to learn, and
  one more layer of indirection between a caller and the concrete code it
  ultimately reaches.
- **Discipline cost at every edge.** Because the harm of a single cyclic
  edge is invisible locally, as dimension 3 argues, maintaining ADP requires
  either a mechanical check on every change, which is infrastructure to
  build and maintain, or sustained collective discipline that dimension 2's
  three conditions, team size, independent release, longevity, make
  unreliable without tooling.
- **False sense of modularity from folder structure alone.** Splitting code
  into folders or namespaces without also splitting it into genuinely
  separate build or release units, and without a tool that computes the
  graph across those units, can create the appearance of modularity while
  the actual dependency graph, hidden inside a single compiled artifact,
  remains as tangled as ever. ADP is a property of the graph a tool can
  compute, not of the folder names a human chose.
- **A necessary redesign can be more disruptive than it first appears.**
  When a mature codebase is discovered to have a long-standing cycle, the
  fix under dimension 14 can require moving code across package boundaries
  that many other modules already depend on for their own imports, which
  can itself be a multi-team, multi-release undertaking rather than a
  small patch.

## 11. Failure modes and misuse

Symptom, cause, and fix triples, each grounded in an observable signal a
developer or a build system would actually produce, per the template's
requirement for this dimension.

**A change to one package unexpectedly breaks a test suite in a seemingly
unrelated package overnight, with no direct edit to that package's own
files.** The cause is that the two packages sit inside an undetected cycle.
A change in one propagates through the cycle's edges to affect behavior
compiled or linked into the other, even though no import statement in
either package's diff appears to touch the other directly, because the
affecting edge is several hops around the loop. The fix is to run a cycle
detector, per dimension 8, against the full dependency graph, not only the
two packages involved, to find the complete cycle, then apply the
extraction technique from dimension 14 to remove it.

**Build times grow non-linearly as the codebase grows, well past what the
addition of new, unrelated features would predict, and a significant
fraction of the codebase seems to rebuild on almost every change regardless
of which file changed.** The cause is that one or more large cycles have
merged what should be many independently buildable units into effectively
one giant unit, so the build tool can no longer skip rebuilding unaffected
nodes because, inside a cycle, "unaffected" cannot be determined per node.
The fix is to profile the dependency graph to find the largest strongly
connected component, the graph-theoretic name for a maximal cycle-containing
subgraph where every node can reach every other node, then break it
starting with the edges that are structurally least necessary, typically
ones added for a one-off convenience import rather than a genuine
architectural need.

**A team introduces an interface package specifically to "break a cycle,"
but developers keep needing to add new methods to that interface whenever
either original side changes, and the interface package now imports
concrete types from both sides that it was supposed to sit between.** The
cause is that the interface extraction was performed mechanically, moving a
type declaration into a new file, without actually inverting which side
owns the abstraction. The Dependency Inversion Principle, which underlies
the correct fix, requires the abstraction to be owned by, and shaped
around the needs of, the calling side, not simply relocated. An interface
package that still needs concrete knowledge from both former cycle members
has not actually broken the coupling. It has renamed it. The fix is to
redesign the interface so its shape reflects only what the consumer, the
former "upstream" side, genuinely needs, place it in a package the consumer
owns or that is clearly consumer-facing, and have the former "downstream"
side implement that interface without the interface package needing to
import anything concrete from either side.

**No cycle is ever reported by CI, yet developers still describe the
codebase as tightly coupled, with unrelated feature work routinely touching
the same handful of shared files.** This is not an ADP violation at all,
and treating it as one is the misuse. Acyclicity is necessary but not
sufficient for a well-factored dependency graph. A perfectly acyclic graph
can still have an unhealthy shape, for instance every single package
depending directly on one "god" utility package that itself has no
dependents, which is legal under ADP alone. This symptom is a Stable
Dependencies Principle or package-cohesion problem, a sibling principle to
ADP, not an acyclicity problem, and applying an interface-extraction fix
from dimension 14 will not address it. The real fix is to measure
package-level fan-in and fan-out, per dimension 16's observability signals,
and apply the Stable Dependencies Principle and the Single Responsibility
Principle instead, since there is no cycle to break here.

**A "temporary" cycle, added under deadline pressure with a comment
promising a follow-up refactor, is still present a year later and has grown
to include several more packages.** The cause is that nothing mechanically
enforces the removal of a known, tolerated cycle once it exists, and the
local-invisibility force from dimension 3 that made the original cycle easy
to introduce makes every subsequent edge added to the same already-cyclic
subgraph feel equally harmless, since the graph was "already" cyclic before
that edge was added. The fix is to configure a cycle detector that runs on
every change, per dimension 8, to fail on any new edge that increases the
size of an existing cycle or adds a new cycle, even while a pre-existing
cycle is tracked as a known, ticketed debt item with an owner and a target
removal date, rather than silently permitted to grow.

## 12. Trade-off matrix

Comparison against two named, related principles, across the forces named
in dimension 3. All three principles are complementary, not mutually
exclusive. The table clarifies which specific problem each one solves so a
reader does not reach for the wrong one.

| Force | Acyclic Dependencies Principle | Stable Dependencies Principle | Dependency Inversion Principle |
|---|---|---|---|
| What it constrains | The graph shape, no cycles between packages | The graph direction, depend only on things at least as stable as you | A single edge, depend on an abstraction, not a concretion |
| Unit of application | Whole dependency graph of packages or components | Pairwise relation between two packages, judged by each package's stability metric | A single dependency relationship inside or between packages |
| Detects | A closed loop of any length across any number of packages | A package that depends on something less stable than itself, inviting future breakage even without a cycle | A caller bound to a concrete implementation instead of an interface |
| Typical tool | Graph cycle detector (DFS with coloring, or a compiler that forbids cycles) | Package stability metrics, instability ratio Ce over Ca plus Ce | Code review, or a linter checking that a module imports an interface type rather than a concrete class from another layer |
| Cost of violation | Independent build and release becomes impossible for every node in the cycle | A stable package becomes fragile because it now depends on volatile code, even with no cycle present | A single call site is harder to test or swap, but the graph can still be acyclic |
| Composability | Frequently satisfied by applying Dependency Inversion at the one edge that would otherwise close a cycle | Assumes ADP already holds, since stability is only well-defined across an acyclic graph, a cycle has no direction to measure stability along | The mechanical technique most often used to satisfy ADP, described in dimension 14 |

## 13. Related and incompatible patterns

**Dependency Inversion Principle.** The primary technique for satisfying
ADP when a cycle would otherwise form. Where two concrete packages would
need to depend on each other, DIP says to introduce an abstraction that
both depend on instead, so the edge that used to point "backward" now
points toward the abstraction. ADP names the graph-level property to
achieve. DIP is frequently the mechanism that achieves it at a single edge.

**Interface Segregation Principle.** When the abstraction extracted to
satisfy ADP is an interface, ISP governs how that interface should be
shaped, narrow, specific to what the consumer actually needs, rather than a
single bloated interface that reintroduces coupling of a different kind,
every implementer forced to satisfy methods it does not need. A cycle
broken with a poorly segregated interface, as the third failure mode in
dimension 11 describes, has not really been broken.

**Single Responsibility Principle.** A package that is genuinely cohesive
around one responsibility rarely needs a cyclic relationship with another
package, because most cyclic dependencies arise from two packages each
containing a mix of responsibilities, some of which naturally belong with
the other package. Applying SRP to split a tangled package often removes
the motivation for the cycle before any interface extraction is needed.

**Stable Dependencies Principle and Stable Abstractions Principle.** Both
are Martin's sibling coupling principles, described alongside ADP in the
same 2000 paper and the same "Component Coupling" chapter of Clean
Architecture. SDP and SAP only make sense once ADP already holds,
because both are statements about the direction of dependency along an
acyclic graph, depend toward stability, and make stable packages abstract,
and direction is not a well-defined concept along a cycle.

**Factory Method and Abstract Factory.** When breaking a cycle requires
that one side stop constructing concrete instances of the other side
directly, a factory, injected or resolved through the newly extracted
abstraction, is frequently the mechanism that lets the consuming side stop
importing the concrete constructor at all, completing the inversion.

Incompatible with, none, in the sense of a pattern that cannot coexist
with ADP. The closest candidate, mutual recursion between two functions
that are part of one deliberately cohesive unit, is not actually
incompatible. Dimension 4 explains that it is out of scope for ADP because
it occurs inside one node of the graph rather than between two nodes, so it
does not conflict with ADP, it simply is not the kind of relationship ADP
describes.

## 14. Refactoring path in and out

**Introducing ADP enforcement into a codebase that has never checked for
cycles.**

1. Choose the unit ADP will be measured over for this codebase, packages,
   top-level modules, or build targets, matching whatever the platform
   already treats as a releasable or independently buildable thing.
2. Run a cycle detector, using the language's own toolchain where one
   exists, dimension 8's compiler-enforced variant, or a dedicated
   analyzer such as JDepend for Java, or a hand-written detector like the
   one in this entry's code examples, against the current graph.
3. Record every cycle found as a known item, with the full cycle path,
   every node in the loop, rather than fixing all of them immediately.
   A large, mature codebase discovering its first several cycles at once is
   common and does not need to be treated as an emergency.
4. Configure the detector to run on every proposed change, a pre-commit
   hook, a required CI job, or, where the language supports it, the
   compiler itself, and to fail specifically on any new cycle, or on any
   change that grows an already-known cycle, per the last failure mode in
   dimension 11. This makes the graph monotonically improve, or at worst
   hold steady, from that point forward, without requiring the entire
   backlog of existing cycles to be paid down first.
5. Pay down the recorded backlog incrementally, using the extraction steps
   below, prioritized by which cycles are actually causing observed pain,
   slow builds, unpredictable test breakage, rather than by cycle length
   alone.

**Breaking a specific existing cycle, A depends on B, B depends on A.**

1. Identify exactly what A needs from B, and exactly what B needs from A.
   In many real cycles, the actual surface each side needs from the other
   is a small handful of methods or types, even though the import is of
   the whole package.
2. Decide which side's need is more fundamental to the domain, meaning
   more likely to be stable and less likely to change for reasons specific
   to the other side's implementation details. That side's need defines
   the shape of the abstraction to extract.
3. Create a new package (or, in a single-package language, a new file
   inside a shared parent that neither A nor B is nested under) containing
   only that abstraction, an interface, a protocol, or a set of types, with
   no implementation logic that depends on either A's or B's internals.
4. Change the side that owns the concrete implementation of the extracted
   abstraction to depend on the new package and implement the interface
   there. This side's import of the abstraction package is a legitimate,
   one-directional edge.
5. Change the side that consumes the abstraction to depend on the new
   package instead of on the concrete implementation package directly,
   removing its former direct import.
6. Re-run the cycle detector. The graph should now show A pointing to the
   abstraction and B pointing to the abstraction, with no edge from the
   abstraction package back to either A or B, matching the AFTER diagram in
   dimension 6.
7. Verify no other package in the codebase still imports the now-internal
   concrete implementation directly, bypassing the new abstraction, which
   would silently reintroduce the same coupling through a different path.

**Removing ADP enforcement, the rarer direction.** A team occasionally
decides an abstraction extracted to satisfy ADP has outlived its purpose,
for instance when two packages that were once independently released are
formally merged into one package because they are now always changed and
released together. In that case the correct move is not to remove the ADP
check, but to physically merge the two nodes into one node in the graph,
literally combine the packages, after which the interface that used to
separate them can be simplified or removed, because it is no longer
separating two independently releasable units, only organizing code inside
one unit.

## 15. Testing and verification

ADP is a build-time and CI-time property, not a runtime behavior, so its
primary verification is structural rather than a conventional unit test of
program behavior. This dimension is largely engineering practice rather
than sourced claim, aside from the tools it names, which are the same ones
covered in dimension 8 and 9.

**Structural verification, automated cycle detection as a required check.**
The most direct test of ADP is running a cycle detector against the actual
compiled or declared dependency graph, not against a hand-maintained
diagram that can drift out of date. For languages with compiler-enforced
acyclicity, such as Go, this test is free. A build that succeeds has
already proven the language-level package graph acyclic. For other
languages and build systems, wiring the detector as a required, blocking CI job, rather than
an informational report, is what makes this a genuine test rather than a
suggestion. JDepend's own documented pattern of running its cycle check
"automatically...by a JUnit test" is exactly this, making the structural
property assertable inside the same test suite that already gates merges
([clarkware/jdepend](https://github.com/clarkware/jdepend), verified
2026-08-02).

**What ADP compliance makes easier to test.** Once a graph is acyclic, unit
tests for a given node can be written and reasoned about against a bounded,
computable set of dependencies, the transitive closure reachable from that
node, without needing to account for the possibility that testing the node
in isolation somehow requires the whole cycle to be present. Test doubles,
mocks, fakes, stubs, for a dependency are also easier to construct once
that dependency is an extracted, narrow interface, per Interface
Segregation, rather than a whole concrete package pulled in through a
cyclic edge.

**What becomes harder.** An acyclic graph with an interface extracted at
every former cycle point can, if over-applied, produce a codebase with more
integration-level seams than a purely concrete, tangled one, and a
developer new to the codebase can find it harder to trace "what actually
runs" through several layers of interface indirection without an IDE's
go-to-implementation feature. This is a real cost, named honestly rather
than glossed over, and is the reason dimension 4's non-applicability list
matters. not every internal relationship needs this treatment.

**Regression test for a specific past cycle.** When a cycle is deliberately
broken, it is worth adding a permanent, lightweight test, run in CI, that
asserts the specific packages involved never import each other again, even
indirectly. This catches the case in the failure modes under dimension 11
where the fix was applied but a later, unrelated change quietly reopens the
same cycle through a new path.

## 16. Observability signals

This dimension is analytical and practice-derived, not built from a single
sourced authority, beyond the tools it names.

**What to measure.** Two of the classic package metrics that this
principle's sibling tools compute, and that are directly useful for
watching a graph's health over time, are afferent coupling, the number of
packages outside a given package that depend on it, and efferent coupling,
the number of packages the given package depends on. Neither metric on its
own detects a cycle, but tracking both per package over time, alongside the
cycle detector's pass or fail result, gives a build dashboard a way to show
which packages are becoming coupling hotspots before a cycle actually forms
there. JDepend computes exactly these two metrics per package as part of
its output, alongside its cycle check ([clarkware/jdepend](https://github.com/clarkware/jdepend),
verified 2026-08-02).

**A healthy dashboard.** Cycle count at zero, held at zero across every
build, is the primary signal, ideally surfaced as a hard pass or fail on
every CI run rather than a number a human has to remember to check. A
secondary, softer signal is the trend of the afferent and efferent coupling
for the packages closest to the center of the graph. A package whose
efferent coupling keeps growing while its afferent coupling also grows is
trending toward becoming the "god package" failure mode described in
dimension 11's fourth entry, which, while still technically acyclic, is a
warning sign the graph's cycle count alone will not surface.

**A failing dashboard.** A cycle count above zero on a build that is
nonetheless marked green means the check either is not wired as a required
gate or is being run against a stale or incomplete view of the graph, for
instance a checker scoped only to a subdirectory that misses cross-cutting
imports elsewhere in the repository. Build-time trending upward alongside a
flat or shrinking codebase size, without a corresponding feature-size
explanation, is the operational symptom named in dimension 11's second
failure mode and is worth graphing against the cycle detector's history to
see if the two moved together.

**Log and trace signals, where applicable.** ADP is checked at build time,
not at runtime, so there is normally nothing to trace in a running system.
The one runtime-adjacent signal worth logging, in systems that lazily
resolve dependencies through a plugin or service-locator mechanism rather
than static imports, is a resolution failure or a resolution cycle detected
at startup, which is the runtime analog of the same structural problem and
should be treated with the same urgency as a build-time cycle failure.

## 17. Security and privacy implications

This principle's security surface is indirect and structural, not a
mechanism for handling secrets or authentication itself, so it is stated
here plainly rather than inflated.

**Blast radius of a compromised dependency.** A dependency graph free of
cycles gives a security reviewer a computable, finite answer to "what does
this package have the ability to affect, if it were compromised or
malicious," namely everything reachable by following edges forward from
it, meaning everything that depends on it transitively, not everything it
itself transitively depends on, since dependency does not run in reverse.
A cyclic graph destroys this computation for every package caught inside
the cycle, because each one can, through the loop, ultimately affect every
other one in the cycle regardless of the direction any single edge points,
collapsing a supply-chain risk assessment that should be graph-shaped into
one that has to treat the whole cycle as a single trust boundary.

**Audit and provenance clarity.** Software provenance manifests such as an
SBOM are typically expressed as a dependency graph. A
cyclic graph is harder to represent faithfully in tooling built around the
assumption of a DAG, the same assumption Bazel's own dependency model makes
explicit, per dimension 6 and 9, which can produce an inaccurate or
incomplete SBOM for any system that has a cycle, understating or
mischaracterizing which components a given package's vulnerabilities can
actually reach.

**No implication for data handling.** ADP says nothing about what data
flows through the edges of the graph, only about the graph's shape. A
system can be fully acyclic and still handle personal data insecurely at
any single node, and a cyclic system can, in principle, be handling no
sensitive data at all. This principle is silent on data classification,
encryption, or access control, and should not be conflated with a data-flow
or privacy-boundary analysis, which requires its own, separate review.

## 18. References

1. Robert C. Martin, "Design Principles and Design Patterns," 2000, cited
   by name and year as the origin of the Acyclic Dependencies Principle in
   [Wikipedia, Acyclic dependencies
   principle](https://en.wikipedia.org/wiki/Acyclic_dependencies_principle),
   verified 2026-08-02.
2. Robert C. Martin, *Clean Architecture. A Craftsman's Guide to Software
   Structure and Design*, Prentice Hall, 2017, Part IV, "Component
   Principles," chapter "Component Coupling," which restates the Acyclic
   Dependencies Principle alongside the Stable Dependencies Principle and
   the Stable Abstractions Principle. Part and chapter titles confirmed
   across multiple independent reading summaries of the book's table of
   contents, verified 2026-08-02.
3. Wikipedia, "Acyclic dependencies principle,"
   [https://en.wikipedia.org/wiki/Acyclic_dependencies_principle](https://en.wikipedia.org/wiki/Acyclic_dependencies_principle),
   verified 2026-08-02.
4. Bazel documentation, "Concepts and terminology, Dependency graph,"
   [https://bazel.build/concepts/dependencies](https://bazel.build/concepts/dependencies),
   direct quote "The depends upon relation induces a Directed Acyclic
   Graph (DAG) over targets, and it is called a dependency graph,"
   verified 2026-08-10.
5. clarkware/jdepend, GitHub repository, "A Java package dependency
   analyzer that generates design quality metrics,"
   [https://github.com/clarkware/jdepend](https://github.com/clarkware/jdepend),
   verified 2026-08-02.
6. golang/go issue #28845, "Getting ERROR 'import cycle not allowed' when
   import package,"
   [https://github.com/golang/go/issues/28845](https://github.com/golang/go/issues/28845),
   verified 2026-08-02.
7. Direct reproduction for this entry. a two-package Go module (`order`
   importing `invoice`, `invoice` importing `order`) built with `go build
   ./...`, producing the compiler error quoted in dimension 9, executed
   and captured 2026-08-10.
8. Discussion of the "morning after syndrome" as the informal description
   of the harm caused by a cyclic package dependency graph,
   [https://web.archive.org/web/2/https://karandhillon95.medium.com/the-morning-after-syndrome-4e49096156ed](https://web.archive.org/web/2/https://karandhillon95.medium.com/the-morning-after-syndrome-4e49096156ed),
   verified 2026-08-10 (the live Medium host now bot-blocks automated
   requests, checked directly, so the Wayback Machine snapshot is cited
   in its place).

## Code examples

### TypeScript, cycle detector over a package dependency graph

```typescript
type Graph = Map<string, string[]>;

function detectCycle(graph: Graph): string[] | null {
  const WHITE = 0, GRAY = 1, BLACK = 2;
  const color = new Map<string, number>();
  const path: string[] = [];

  function visit(node: string): string[] | null {
    color.set(node, GRAY);
    path.push(node);
    for (const dep of graph.get(node) ?? []) {
      const state = color.get(dep) ?? WHITE;
      if (state === GRAY) {
        const start = path.indexOf(dep);
        return [...path.slice(start), dep];
      }
      if (state === WHITE) {
        const found = visit(dep);
        if (found) return found;
      }
    }
    path.pop();
    color.set(node, BLACK);
    return null;
  }

  for (const node of graph.keys()) {
    if ((color.get(node) ?? WHITE) === WHITE) {
      const found = visit(node);
      if (found) return found;
    }
  }
  return null;
}

const layered: Graph = new Map([
  ["ui", ["domain"]],
  ["domain", ["data"]],
  ["data", []],
]);

const feedback: Graph = new Map([
  ["ui", ["domain"]],
  ["domain", ["data"]],
  ["data", ["ui"]],
]);

for (const [label, graph] of [
  ["layered", layered],
  ["feedback", feedback],
] as [string, Graph][]) {
  const cycle = detectCycle(graph);
  console.log(label, cycle ? `cycle: ${cycle.join(" -> ")}` : "acyclic");
}
```

Compiled with `tsc --strict --target es2022` against the exact flags this
repository's gate uses. Run output, captured 2026-08-10.

```text
layered acyclic
feedback cycle: ui -> domain -> data -> ui
```

### Python, cycle detector plus a refactor that removes a cycle

```python
from __future__ import annotations
from typing import Dict, List, Optional

Graph = Dict[str, List[str]]

WHITE, GRAY, BLACK = 0, 1, 2


def detect_cycle(graph: Graph) -> Optional[List[str]]:
    color: Dict[str, int] = {}
    path: List[str] = []

    def visit(node: str) -> Optional[List[str]]:
        color[node] = GRAY
        path.append(node)
        for dep in graph.get(node, []):
            state = color.get(dep, WHITE)
            if state == GRAY:
                start = path.index(dep)
                return path[start:] + [dep]
            if state == WHITE:
                found = visit(dep)
                if found:
                    return found
        path.pop()
        color[node] = BLACK
        return None

    for node in graph:
        if color.get(node, WHITE) == WHITE:
            found = visit(node)
            if found:
                return found
    return None


def extract_shared_module(order_service: Graph, invoice_service: Graph) -> Graph:
    merged: Graph = {}
    for src in (order_service, invoice_service):
        for k, v in src.items():
            merged.setdefault(k, []).extend(v)
    return merged


if __name__ == "__main__":
    layered: Graph = {"ui": ["domain"], "domain": ["data"], "data": []}
    print("layered:", detect_cycle(layered) or "acyclic")

    order_before = {"order": ["invoice"]}
    invoice_before = {"invoice": ["order"]}
    coupled = extract_shared_module(order_before, invoice_before)
    print("coupled:", detect_cycle(coupled))

    order_after = {"order": ["pricing"]}
    invoice_after = {"invoice": ["pricing"]}
    decoupled = extract_shared_module(order_after, invoice_after)
    print("decoupled:", detect_cycle(decoupled) or "acyclic")
```

`order` and `invoice` each depending on the other's package directly is a
two-node cycle, `["order", "invoice", "order"]`. After both are refactored
to depend on an extracted `pricing` package instead of on each other, per
the dimension 14 technique, the graph is acyclic. Run with `python3
s.py`, output captured 2026-08-10.

```text
layered: acyclic
coupled: ['order', 'invoice', 'order']
decoupled: acyclic
```

### Go, the same cycle detector, and a real compiler-enforced cycle

```go
package main

import "fmt"

type Graph map[string][]string

const (
	white = 0
	gray  = 1
	black = 2
)

func detectCycle(g Graph) []string {
	color := make(map[string]int)
	var path []string
	var cycle []string

	var visit func(node string) bool
	visit = func(node string) bool {
		color[node] = gray
		path = append(path, node)
		for _, dep := range g[node] {
			if color[dep] == gray {
				start := 0
				for i, n := range path {
					if n == dep {
						start = i
						break
					}
				}
				cycle = append([]string{}, path[start:]...)
				cycle = append(cycle, dep)
				return true
			}
			if color[dep] == white {
				if visit(dep) {
					return true
				}
			}
		}
		path = path[:len(path)-1]
		color[node] = black
		return false
	}

	for node := range g {
		if color[node] == white {
			if visit(node) {
				return cycle
			}
		}
	}
	return nil
}

func main() {
	acyclic := Graph{
		"ui":     {"domain"},
		"domain": {"data"},
		"data":   {},
	}
	if cyc := detectCycle(acyclic); cyc != nil {
		fmt.Println("cycle found:", cyc)
	} else {
		fmt.Println("acyclic: safe to release independently")
	}

	cyclic := Graph{
		"ui":     {"domain"},
		"domain": {"data"},
		"data":   {"ui"},
	}
	if cyc := detectCycle(cyclic); cyc != nil {
		fmt.Println("cycle found:", cyc)
	}
}
```

`go vet` passes on this file, and `go run` against it, captured 2026-08-10,
prints this output.

```text
acyclic: safe to release independently
cycle found: [data ui domain data]
```

Go additionally enforces ADP at the compiler level for real, multi-package
programs, which the hand-written detector above only simulates within one
file. A two-package module was built for this entry with `order` importing
`invoice` and `invoice` importing `order`. Running `go build ./...` against
it on 2026-08-10, without any custom detector at all, produced this output.

```text
package adpdemo/invoice
	imports adpdemo/order from invoice.go
	imports adpdemo/invoice from order.go: import cycle not allowed
```

This is the same class of check the hand-written detector performs, applied
automatically by the Go toolchain itself, matching the description in
dimension 8's compiler-enforced variant.
