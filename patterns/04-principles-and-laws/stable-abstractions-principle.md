---
name: Stable Abstractions Principle
slug: stable-abstractions-principle
family: 04-principles-and-laws
category: Design Principle
aliases: [SAP, The Stable Abstraction Principle]
first_described: "Robert C. Martin, Design Principles and Design Patterns, 2000"
maturity: canonical
related: [acyclic-dependencies-principle, dependency-inversion-principle, open-closed-principle, single-responsibility-principle, interface-segregation-principle, factory-method]
incompatible_with: []
verified: 2026-08-02
---

# Stable Abstractions Principle

## 1. Name, aliases, and lineage

The canonical name is the Stable Abstractions Principle, almost always
shortened to SAP. Robert C. Martin states it in one sentence, quoted
consistently across secondary summaries of his work, that a package should
be as abstract as it is stable ([summary of Martin's package design
principles, via a blog post quoting the Clean Architecture chapter
directly](https://kevbuchanan.github.io/posts/stable-abstraction-principle),
verified 2026-08-02). Martin himself is reported using a slightly earlier
phrasing tied to inheritance depth rather than a package, stated as the
more stable a class category is, the more it must consist of abstract
classes (summary of the earlier C++ era wording, verified against a
secondary academic source below).

Martin introduced SAP as the third of three coupling principles for
packages, alongside the Acyclic Dependencies Principle and the Stable
Dependencies Principle, in the paper Design Principles and Design Patterns,
which he published in the year 2000 (dating and grouping confirmed
consistently across secondary treatments of Martin's package principles,
including [Wikipedia's Package principles article](https://en.wikipedia.org/wiki/Package_principles),
verified 2026-08-02, which cites Martin's work from 1996 and from the 2002
book Agile Software Development, Principles, Patterns, and Practices as the
sources for the same set of principles). Martin restated all three coupling
principles seventeen years later in Part IV, Component Principles, in
Chapter 14, titled Component Coupling, of Clean Architecture. A Craftsman's
Guide to Software Structure and Design, Prentice Hall, 2017 (chapter number
and title independently confirmed by three separate reading summaries of
the book, including [a chapter-by-chapter blog summary titled Clean
Architecture, Chapter 14, Component Coupling, SAP, The Stable Abstractions
Principle](https://www.letscodethemup.com/clean-architecture-chapter-14-component-coupling-sap-the-stable-abstractions-principle/),
verified 2026-08-02).

The book also states the relationship between SAP and its sibling
principle plainly. The Stable Dependencies Principle says dependencies
should run in the direction of stability, and SAP says that stability
implies abstraction, so as a consequence dependencies should run in the
direction of abstraction (paraphrase of the stated relationship between
SDP and SAP as reported in the same chapter summary above, verified
2026-08-02). This is the load-bearing consequence of the two principles
taken together, and it is the reason SAP is usually not read alone.

Martin's own vocabulary for the two coupling counts that feed the SAP
metric varies slightly between the original C++ era writing and the later
Clean Architecture text. The C++ era writing and most tool documentation
use afferent coupling, abbreviated Ca, for the number of external classes
that depend on a package, and efferent coupling, abbreviated Ce, for the
number of external classes a package depends on. Clean Architecture itself
uses fan-in and fan-out for the same two counts (terminology confirmed by
[a direct GitHub summary of Part IV of Clean Architecture, section on
component coupling metrics](https://github.com/serodriguez68/clean-architecture/blob/master/part-4-component-principles.md),
verified 2026-08-02, which gives the instability formula as fan-out over
the sum of fan-in and fan-out). Both vocabularies describe the identical
count and the identical formula, and a reader moving between a tool's
documentation and the book should expect the terms to be used
interchangeably.

No community applies a materially different name to SAP itself. What
varies is the unit the principle is measured against. The original writing
speaks of packages in the C++ and Java sense of the word, a releasable,
independently versionable unit. Later tooling applies the identical
formula to Java packages, .NET assemblies, npm packages, and any other
compilation or distribution unit that groups related types, because each
of those units plays the same role in a dependency graph that a package
played in 2000.

## 2. Problem and context

A codebase accumulates two kinds of code over its life. Policy code, the
part that encodes business rules, decisions, and the high-level shape of
what the system does, and mechanism code, the part that carries those
decisions out against a database, a network, a file system, or a UI
toolkit. Policy code should change rarely, because a change to a business
rule is a considered, infrequent event. Mechanism code changes often,
because frameworks release new versions, drivers get replaced, and
third-party APIs evolve on their own schedule.

The problem SAP addresses appears when a team places policy code in a
package that many other packages import, so that package becomes stable in
Martin's specific sense of the word, meaning it is costly to change because
many things depend on it, and then fills that same package with concrete
classes rather than interfaces. Concrete stable code produces the worst
combination available to a team, a piece of the system that many other
packages rely on, and that resists change precisely because so much relies
on it, because there is nowhere for a variant to be introduced without
touching the widely depended-upon code directly.

The context in which SAP becomes the right lens has two properties present
at once. First, a package has genuinely become a dependency hub, meaning
several other packages import it and would need to change if its public
surface changed. Second, that package still needs to accommodate variation,
meaning new behaviour, new backends, or new policies will need to be
introduced against it in the future without editing it. When both hold,
the fix is not to make the package less depended upon, which is often not
achievable, but to make what other packages depend on abstract, so the
stable package can be extended by new code arriving elsewhere rather than
modified in place. This is the same insight as the Open Closed Principle,
applied specifically to the packages that sit at the bottom of a
dependency graph rather than to an individual class.

## 3. Forces

The principle balances the following competing pressures, using the
graph-theoretic definition of stability that Martin gives, where a
package's instability I is the ratio of its outgoing dependencies to its
total dependencies, so a low I means a package many others rely on and few
things itself relies on ([the formula I equals Ce over the sum of Ca and
Ce, attributed to Martin, restated by the Wikipedia article on software
package metrics](https://en.wikipedia.org/wiki/Software_package_metrics),
verified 2026-08-02).

- **Changeability where change is expected.** Favoured for the packages a
  team actually intends to keep editing. SAP does not ask every package to
  become abstract, only the ones that have already become hard to change
  because many others depend on them.
- **Cost of touching widely depended-upon code.** This is the pressure SAP
  responds to directly. A concrete class in a stable package cannot be
  swapped for a variant without editing the package itself, and every
  consumer of that package is exposed to the edit. An abstract type in the
  same position can be extended by a new subclass living entirely outside
  the stable package.
- **Class and interface count.** Sacrificed. Making a stable package
  abstract typically means splitting one concrete class into an interface
  plus one or more implementations, so the type count in the system rises
  even though behaviour has not changed.
- **Indirection and readability.** Sacrificed at the call site, in the same
  way that the Dependency Inversion Principle sacrifices it. A reader
  following a call into a stable, abstract package finds an interface
  rather than the executing code, and must locate the concrete
  implementation separately.
- **Architectural legibility.** Favoured system-wide. Once SAP is applied
  consistently, the dependency graph itself communicates which packages
  hold policy, because they sit low in the graph and are abstract, and
  which hold mechanism, because they sit high in the graph and are
  concrete. This is the graph the Dependency Inversion Principle and Clean
  Architecture's layering both rely on being true.
- **Cost of getting the boundary wrong.** Sacrificed when applied to a
  package that was never actually going to accumulate many dependents.
  Abstracting a package nobody else needs to depend on produces the failure
  mode named the zone of uselessness in dimension 11, an interface with no
  callers and no reason to exist.

A pattern or principle that costs nothing is being described incorrectly.
Here the price is paid in type count and indirection, purchased against the
cost of being unable to extend the parts of the system most other parts
rely on.

## 4. Applicability and non-applicability

Reach for the Stable Abstractions Principle when the following hold at
once.

- A package already has, or is clearly going to accumulate, several
  dependents inside the codebase, so its instability I is low and edits to
  it ripple outward.
- The behaviour that package exposes is expected to vary, either now or
  later, across environments, tenants, backends, or policies.
- The package sits at a layer boundary a team already cares about, a
  domain layer, a public API surface, or a plugin contract, where the
  choice to keep it abstract is a deliberate architectural decision rather
  than an accident of import order.
- The team is willing to own the extra indirection and the extra type this
  produces, and has a place, an interface segregation discipline and a
  factory or a dependency injection mechanism, ready to supply the
  concrete implementations.

Do NOT apply the Stable Abstractions Principle in these cases, and the
reason matters more than the rule.

- **The package has no dependents and none are likely.** Martin's own
  argument for SAP is that instability alone is fine, and a package with
  few or no dependents can, and arguably should, stay concrete, because
  concreteness there costs nothing. Abstracting it anyway produces an
  interface that exists for no reader, the zone of uselessness described in
  dimension 11.
- **The package is a leaf that talks directly to a specific external
  system and will only ever have one implementation.** A driver for one
  specific piece of hardware, or a client tied to one specific third-party
  API by contract, gains nothing from an interface that will only ever
  have a single implementer, and the interface becomes a maintenance tax
  with no payoff. This is the same judgement the Applicability section of
  the Factory Method entry makes about a creator with only one plausible
  product.
- **The instability is intentionally high by design, such as a UI layer or
  a top-level composition root.** SAP's own companion, the Stable
  Dependencies Principle, expects some packages to sit at the top of the
  graph with high instability and many outgoing dependencies. Forcing an
  unstable, high-churn package to also be abstract fights the shape the
  system is supposed to have; a composition root is meant to be the most
  concrete, most volatile part of the system, wiring everything else
  together.
- **The variation the team is trying to accommodate has not actually
  happened yet, and there is no second implementation in view.** Applying
  SAP speculatively, before a genuine second variant exists, produces
  exactly the same waste that speculative use of Factory Method produces,
  an abstraction carried by a single implementation that earns nothing.
- **Data-driven variation, not type-driven variation, is what is actually
  needed.** If what differs between cases is a configuration value rather
  than a class of behaviour, an abstract type and a family of
  implementations is the wrong tool; a lookup table or a strategy selected
  by value is cheaper and clearer.
- **The measurement itself would be gamed by a shallow interface.** A team
  under pressure to improve an abstractness score can wrap every concrete
  class in a trivial single-implementation interface without changing the
  design at all. If that is the only path being considered, the team is
  optimizing the metric in dimension 6 rather than applying the principle
  in dimension 1, and the fix is a genuine second implementation or
  extension point, not a wrapper.

## 5. Structure

The Stable Abstractions Principle is a property of a dependency graph
between packages, not a structure of classes inside one file, so the
participants are the packages themselves and the relationship is
dependency, not composition or inheritance.

- **StablePackage.** A package with a low instability score, meaning few
  outgoing dependencies and, typically, several incoming ones. In a
  healthy system this package holds interfaces, abstract classes, or
  otherwise abstract types that express policy.
- **DependentPackage.** Any package that imports and depends on
  StablePackage. Its own instability can be high or low; what matters for
  SAP is only that its dependency points toward StablePackage.
- **ConcreteImplementationPackage.** A package that supplies a concrete
  implementation of a type defined in StablePackage. In a system that
  correctly applies the Dependency Inversion Principle alongside SAP, this
  package depends on StablePackage, never the reverse, so
  StablePackage never needs to know the implementation package exists.
- **CompositionRoot.** The high-instability package, often the outermost
  layer of an application, that imports both StablePackage and every
  ConcreteImplementationPackage and wires a concrete instance into the
  abstract type the stable package expects. Its own instability is
  expected to be high, and per the non-applicability list in dimension 4
  it is not itself a candidate for abstraction.

The relationships. DependentPackage and ConcreteImplementationPackage both
depend on StablePackage. CompositionRoot depends on all three of the
others. No arrow points from StablePackage toward any of the other three,
which is exactly the reversal the Dependency Inversion Principle names, and
SAP is the metric-based check that this reversal has actually been carried
out and not merely intended.

## 6. ASCII structure diagram

```
              (many packages depend on it, I is low)
   +---------------------------------------------------+
   |                  StablePackage                     |
   |  interface PaymentGateway { charge(amount): void } |
   +---------------------------------------------------+
             ^                              ^
             | depends on                   | depends on
             |                               |
   +-------------------+          +---------------------------+
   |  DependentPackage  |          | ConcreteImplementationPkg |
   |  uses PaymentGateway|         | class StripeGateway       |
   |  through the        |         | implements PaymentGateway |
   |  interface only     |         +---------------------------+
   +-------------------+                      ^
             ^                                 |
             |          wires the concrete     |
             |          class into the         |
             |          interface at startup   |
             +---------------------------------+
                          |
                +--------------------+
                |   CompositionRoot   |
                |  (I is high, many   |
                |   outgoing imports, |
                |   stays concrete)   |
                +--------------------+

   No arrow points out of StablePackage toward the other three boxes.
```

## 7. Dynamics

SAP is not exercised at runtime, in the sense that no message passes
between the participants because of it; the principle governs how the
dependency graph is drawn at compile time and build time. The dynamics
worth showing are therefore the two moments where SAP is checked, and how
the wiring behaves once the graph is correct.

```
Build time                          Runtime, once wired
   |                                     |
Static analysis walks import graph      Application startup runs the
   |                                    CompositionRoot
Computes Ca, Ce per package              |
   |                                    CompositionRoot imports
Computes I = Ce / (Ca + Ce)             ConcreteImplementationPackage
   |                                     |
Computes A = abstract types / total     CompositionRoot constructs
   types                                StripeGateway
   |                                     |
Computes D = |A + I - 1|                CompositionRoot passes it to
   |                                    DependentPackage's constructor,
Reports packages far from the           typed only as PaymentGateway
main sequence, D close to 1              |
   |                                    DependentPackage calls
Team reviews flagged packages,          gateway.charge(amount) without
either raises abstractness or           ever importing StripeGateway
lowers dependents before the            |
next build                              StablePackage's interface never
                                         changes when a second gateway,
                                         say AdyenGateway, is added later
```

The property worth naming plainly. Once the graph is wired this way, adding
a second concrete implementation touches only
ConcreteImplementationPackage and CompositionRoot. StablePackage and every
DependentPackage compile and run unmodified, which is the entire practical
payoff SAP is chasing.

## 8. Implementation variants

**Interface extraction in an existing stable package.** The most common
form. A concrete class inside a package that already has several
dependents is replaced by an interface of the same name plus a concrete
class moved to a new package. This is a mechanical refactor and is covered
step by step in dimension 14.

**Abstract base class instead of an interface.** Used when the stable
package needs to supply default behaviour alongside the contract, not only
a signature. This raises the abstractness score identically to an
interface under Martin's formula, since abstract classes count the same as
interfaces in the count of abstract types, but it reintroduces
implementation inheritance, so it should be preferred only when shared
default behaviour genuinely exists, per the non-applicability guidance in
the Composition Over Inheritance entry.

**Ports and adapters, sometimes called hexagonal architecture.** The port,
an interface defined by the domain, lives in the stable package. The
adapter, a concrete implementation talking to a specific external system,
lives in its own package that depends inward on the port. This is SAP
applied at the scale of an entire application boundary rather than a
single class, and it is the shape the Composition Root participant in
dimension 5 assumes in most hexagonal designs.

**Protocol or duck typing instead of a declared interface.** In languages
with structural typing, Python's typing.Protocol, TypeScript's structural
interfaces, or Go's implicit interface satisfaction, a stable package can
declare a shape without any concrete implementation ever importing it or
even knowing it exists. This raises abstractness under the same formula
while removing the explicit implements-style dependency the classical
variant requires, and it is the idiomatic form of SAP in Go, where
interfaces are conventionally declared by the consumer rather than the
producer.

**Volatility-weighted distance, as JDepend implements it.** A pure
computation of D treats every package as equally important to keep near
the main sequence. JDepend's JavaPackage class multiplies the raw distance
by a per-package volatility value, defaulting to 1, that a team can set to
0 for packages it has decided to exempt from the check, typically
third-party or generated code the team does not own and cannot refactor
(confirmed directly from source, see dimension 9). This is the practical
answer to the objection that SAP, applied uniformly, would flag code
outside a team's control.

**Registry or dependency injection container resolving the concrete
type.** Rather than a hand-written CompositionRoot, a container reads
configuration or annotations and supplies the concrete implementation at
resolution time. The stable package and its dependents are unaffected;
only the wiring mechanism changes, and this is the form most enterprise
Java and .NET codebases use in practice.

## 9. Known production uses

**JDepend, an open source Java design-quality analysis tool.** Its
JavaPackage class implements the metric directly. The source defines
afferentCoupling and efferentCoupling methods whose Javadoc comments read
"The afferent coupling (Ca) of this package" and "The efferent coupling
(Ce) of this package," an instability method computing efferent coupling
divided by the sum of the two, an abstractness method computing the ratio
of abstract classes to total classes, and a distance method computing the
absolute value of abstractness plus instability minus one, multiplied by a
per-package volatility factor (read directly from source,
https://raw.githubusercontent.com/clarkware/jdepend/master/src/jdepend/framework/JavaPackage.java
verified 2026-08-02, GitHub repository clarkware/jdepend).

**NDepend, a commercial .NET static analysis tool.** Its documented code
metrics include Afferent Coupling, defined as the number of types outside
an assembly that depend on types within it, Efferent Coupling, the
converse, Abstractness, the ratio of internal abstract types to internal
types, Instability, Ce over the sum of Ce and Ca, and Distance from Main
Sequence, the perpendicular normalized distance of an assembly from the
line A plus I equals 1. NDepend's own documentation states these metrics
were "first introduced by the excellent book Agile Software Development,
Principles, Patterns, and Practices in C#, Robert C. Martin," attributing
the metric set directly to Martin (https://www.ndepend.com/docs/code-metrics,
verified 2026-08-02).

**Lattix, a commercial software architecture management tool.** Its
documented metrics include instability, defined as outgoing dependencies
over the sum of outgoing and incoming dependencies, abstractness, defined
as abstract atom count over total atom count, and distance from main
sequence, defined as the absolute value of abstractness plus instability
minus one, with the documentation explicitly attributing all three metrics
to Robert C. Martin's Agile Software Development, Principles, Patterns,
and Practices, Prentice Hall, 2003 (https://docs.lattix.com/lattix/userGuide/Metrics.html,
verified 2026-08-02).

**ArchUnitTS, an open source TypeScript architecture testing library.**
It ships a DistanceFromMainSequence class, documented as measuring how far
a component is from the ideal balance between abstractness and
instability using Robert Martin's metric, computing D as the absolute
value of A plus I minus one, and explicitly crediting the formula to
Martin's Stable Abstractions Principle
(https://lukasniessen.github.io/ArchUnitTS/classes/DistanceFromMainSequence.html,
verified 2026-08-02), which shows the metric being used as an automated
architecture test assertion rather than only a reporting number.

## 10. Consequences

Positive.

- A stable package can be extended by code that arrives later, in a
  package the stable package never imports, because the extension point is
  an abstract type rather than a concrete class.
- The Ca, Ce, A, I, D metrics turn architectural intent, which is stable
  code should be abstract, into a number every package in a codebase can
  be checked against automatically, rather than a design review judgement
  applied inconsistently.
- Consistent application of SAP alongside the Stable Dependencies
  Principle produces a dependency graph that visibly separates policy from
  mechanism, because policy accumulates low in the graph as abstract types
  and mechanism accumulates high in the graph as concrete, frequently
  changing packages.
- The measurement is cheap. Computing Ca, Ce, and the abstract-to-concrete
  ratio for every package in a codebase is a static analysis pass, not a
  runtime cost, and several open source and commercial tools already
  perform it, as shown in dimension 9.

Negative.

- Every stable package that adopts SAP gains at least one additional type,
  an interface or abstract class, over the plain concrete version, which
  raises the total type count of the system.
- A reader tracing a call into a stable package now finds a contract
  rather than executing code, and must find the concrete implementation
  separately, which is the same readability cost the Dependency Inversion
  Principle imposes.
- The metric can be gamed. A team can raise a package's abstractness score
  by wrapping every concrete class in a trivial, single-implementation
  interface, which improves the number without improving the design, as
  named in dimension 4.
- The two source metrics, Ca and Ce, only see dependencies the static
  analyzer can observe, so reflection-based construction, dependency
  injection resolved purely by runtime configuration, or dynamic imports
  can undercount both, silently skewing instability and, in turn, distance.
- SAP gives no guidance on which packages should be made stable in the
  first place; it only tells a team what to do once a package already has
  low instability. A team that has not deliberately decided which packages
  are meant to be dependency hubs gets a metric with nothing to act on.

## 11. Failure modes and misuse

**The zone of pain.** Symptom. A package many other packages depend on,
low instability, that consists entirely of concrete classes, high
concreteness, meaning close to zero abstractness. Martin's own recurring
example is a database schema definition, something the whole application
imports and therefore cannot easily change, yet expressed as concrete
tables and columns rather than an abstraction, so every schema change
becomes a coordinated, risky, whole-system migration (example attributed
to Martin's own teaching material, corroborated independently by two
secondary summaries,
https://kevbuchanan.github.io/posts/stable-abstraction-principle and
https://www.letscodethemup.com/clean-architecture-chapter-14-component-coupling-sap-the-stable-abstractions-principle/,
both verified 2026-08-02). Cause. The package became a dependency hub
before anyone decided it should hold policy, and nobody revisited whether
it needed an abstraction layer once the dependent count grew. Fix. Extract
an interface or a versioned contract in front of the concrete schema, and
route the rest of the system through it, per the refactoring path in
dimension 14.

**The zone of uselessness.** Symptom. An interface or abstract class with
zero dependents, discovered during a codebase audit because nothing
imports it and, in a compiled language, the linker or dead code checker
flags it. Cause. SAP applied speculatively, before a second implementation
or a real consumer existed, or an abstraction left behind after the last
consumer was refactored away. Fix. Delete the abstraction, following the
same you-are-not-gonna-need-it discipline that governs speculative Factory
Method hierarchies, or, if a second implementation is now genuinely
planned, keep it and add the missing consumer in the same change.

**Interface theatre.** Symptom. A code review reveals a package where
every class has a matching single-implementation interface, and the
interface adds no seam a test double or a second backend ever uses.
Abstractness looks high on a dashboard while the design has not actually
changed. Cause. A team optimizing the abstractness number directly rather
than responding to a real need for extension. Fix. Collapse the pair back
into one concrete class unless a genuine second implementation is
scheduled, and measure success by whether a new implementation was ever
added, not by the abstractness score alone.

**Undercounted coupling from dynamic resolution.** Symptom. A static
analysis tool reports a package as highly unstable, or reports a stable
package as having very few dependents, that experienced engineers on the
team know is actually depended on heavily, because the real wiring happens
through a dependency injection container, a plugin registry, or reflection
that a static import scanner cannot see. Cause. Ca and Ce are defined over
statically visible imports, and any dynamic binding mechanism is invisible
to that count. Fix. Either configure the analysis tool to also scan
configuration or registration code, where several dependency injection
frameworks provide such an extension, or treat the tool's number as a
lower bound and correct it with team knowledge before acting on it.

**Circular improvement, abstracting a package that also violates ADP.**
Symptom. Raising a package's abstractness does not reduce its distance
from the main sequence the way the team expected, because the package
sits inside a dependency cycle, which corrupts the very Ca and Ce counts
the formula depends on. Cause. The Acyclic Dependencies Principle was
violated first, and SAP's metrics assume an acyclic graph to mean anything
stable at all. Fix. Break the cycle first, per the Acyclic Dependencies
Principle entry, then recompute and re-evaluate abstractness.

**Composition root mistakenly abstracted.** Symptom. A team applies SAP to
the outermost wiring layer of the application because a linter flagged it
as high instability, and introduces interfaces for the wiring code itself.
Cause. Confusing high instability with a defect, when the Stable
Dependencies Principle expects the composition root to be unstable and
concrete by design, per the non-applicability list in dimension 4. Fix.
Exclude the composition root and other intentionally volatile layers from
the check, using a volatility weight of zero as JDepend supports, or an
equivalent exclusion list in whichever tool is in use.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Stable Abstractions Principle | Dependency Inversion Principle alone, no metric | Interface Segregation Principle alone | No principle, package left concrete | Full ports and adapters architecture |
|---|---|---|---|---|---|
| Detects the problem automatically | Yes, via A, I, D on every build | No, DIP is a design instinct with no built-in measurement | No, ISP concerns interface shape, not package stability | No | Only if the ports and adapters boundary is also measured with SAP |
| Cost to introduce | Medium, one interface extraction per flagged package | Low, applied case by case as reviewers notice a smell | Low, applied case by case | None, but the cost is deferred | High, a whole-application restructuring |
| Guards against the zone of pain specifically | Yes, that is its purpose | Indirectly, if reviewers happen to notice | No | No | Yes, structurally, by construction |
| Guards against speculative abstraction | Partially, D flags an unused interface as far from the main sequence too | No | No | Not applicable, nothing is abstracted | No, the architecture assumes ports exist regardless of dependent count |
| Requires ongoing measurement discipline | Yes, a static analysis step in the build | No | No | No | No, once built the shape is structural |
| Scope of change per adoption | One package at a time | One dependency edge at a time | One interface at a time | None | The whole application boundary at once |
| Readability at the call site | Reduced, an interface stands between reader and implementation | Reduced, same reason | Improved for large interfaces, reduced overall for the same reason as DIP | Best, the concrete class is right there | Reduced, same reason, applied everywhere |

Reading of the table. SAP wins where a team wants an automatable,
build-time signal that a specific package has drifted into the zone of
pain or the zone of uselessness, and is willing to pay for that signal
with an ongoing measurement step. DIP applied without a metric is cheaper
to start but relies entirely on a reviewer noticing the same problem SAP
would compute automatically. Ports and adapters gets the same structural
guarantee without measurement, at the price of committing the whole
application to the boundary up front rather than introducing it package
by package as instability accumulates.

## 13. Related and incompatible patterns

- **Acyclic Dependencies Principle.** A precondition. Martin presents ADP
  as the first of the three coupling principles, and SAP's Ca and Ce
  counts, along with the direction-of-stability reasoning in the Stable
  Dependencies Principle, only mean what they claim to mean inside a graph
  that is already free of cycles. Apply ADP first.
- **Stable Dependencies Principle.** The direct partner. SDP says
  dependencies should run toward stability, SAP says stability should
  imply abstraction, and the two together mean dependencies should run
  toward abstraction, which is the practical rule a codebase can be
  checked against.
- **Dependency Inversion Principle.** The class-level mechanism SAP
  operates through. SAP is, in effect, a package-scale, measurable
  restatement of the same reversal DIP describes at the level of a single
  class depending on an abstraction rather than a concretion. A package
  that satisfies DIP consistently at every dependency edge will tend to
  score well on SAP's abstractness metric as a consequence.
- **Open Closed Principle.** The reason SAP wants abstraction in stable
  packages at all. A stable, abstract package is exactly the shape OCP
  asks for, open to extension through a new implementation, closed to
  modification because the existing consumers never need to change.
- **Interface Segregation Principle.** Composes cleanly, and is often
  necessary once SAP has been applied broadly. Extracting a single large
  interface to satisfy SAP can produce a fat interface that forces every
  implementer to supply methods it does not need; ISP is the principle
  that then narrows that interface back down.
- **Factory Method and Abstract Factory.** The usual mechanism for
  supplying the concrete implementation that a SAP-compliant stable
  package cannot construct itself, since a package holding only
  abstractions has, by definition, nothing concrete to instantiate. The
  ConcreteImplementationPackage participant in dimension 5 is frequently
  produced by a factory living in the composition root.
- **Speculative generality, an anti-pattern.** Actively conflicts when SAP
  is applied ahead of a genuine second implementation. This is the same
  caution the Factory Method entry gives against a subclass hierarchy with
  only one plausible product, restated for packages, and the resulting
  smell is named directly in dimension 11 as the zone of uselessness.
- **Service Locator, an anti-pattern.** Conflicts in practice. A stable,
  abstract package whose consumers resolve their concrete implementation
  through a global locator inside the package itself hides the dependency
  the whole exercise was meant to expose, and defeats the measurable,
  visible wiring SAP is chasing.

## 14. Refactoring path in and out

Introducing SAP into a package that has already become a dependency hub
and is still concrete.

1. Measure first. Compute Ca and Ce for the candidate package using a
   static analysis tool, or by counting imports by hand for a small
   codebase, and confirm instability is genuinely low, meaning several
   packages depend on it and it depends on few others itself. Do not
   proceed on instinct alone.
2. Identify the smallest surface the dependents actually use. Read the
   call sites in DependentPackage, not the whole public surface of the
   stable package, and extract an interface covering only what those call
   sites call. This keeps the new interface from becoming a fat interface
   that Interface Segregation would need to split again immediately.
3. Rename the existing concrete class and move it to a new
   ConcreteImplementationPackage that depends inward on the new interface.
   This is the Move Class refactoring applied specifically to reverse the
   dependency direction; see the refactoring family entry for the general
   technique.
4. Update DependentPackage to depend on the interface type rather than
   the concrete class. Run the existing test suite after this step alone,
   before touching wiring, since this is the step most likely to reveal a
   call site the interface extraction missed.
5. Introduce or extend a CompositionRoot that constructs the concrete
   implementation and supplies it to DependentPackage, whether by
   constructor injection, a factory, or a dependency injection container.
6. Recompute abstractness and distance for the now-split packages.
   StablePackage's abstractness should be close to 1, and its distance
   from the main sequence should have moved toward zero, confirming the
   refactor actually improved the measured design rather than only
   rearranging files.
7. Add the type-per-dependent regression test described in dimension 15
   so a future change cannot silently reintroduce a concrete dependency
   from DependentPackage back to ConcreteImplementationPackage.

Removing SAP from a package where it stopped earning its place. Signals
this has happened include a package whose interface has exactly one
implementation years after it was introduced, with no second
implementation ever having existed, or a package whose dependent count has
fallen to zero or one because the rest of the system was refactored away
from it.

1. Confirm, by searching the whole codebase, that only one implementation
   of the interface exists and none is planned. Check test doubles too; a
   test-only fake counts as a second implementation and is a legitimate
   reason to keep the interface, per dimension 15.
2. Inline the single implementation's members directly into the interface
   type, or delete the interface and rename the implementation class to
   the name the interface held, whichever preserves more of the existing
   call sites unchanged. This is the Collapse Hierarchy or Inline Class
   refactoring, see the refactoring family entries for both.
3. Update every DependentPackage import to point at the now-concrete
   class directly, and delete the now-unused CompositionRoot wiring for
   that specific type.
4. Recompute the metrics for the collapsed package and confirm the change
   was intentional and not a silent loss of a genuinely needed seam,
   before deleting the interface from version control.

## 15. Testing and verification

Easier because of the pattern.

- Every DependentPackage can be tested against a hand-written or generated
  test double of the interface defined in the stable package, without any
  bytecode manipulation or partial-mock trickery, because the seam is a
  plain interface boundary rather than a concrete class that must be
  subclassed or monkey-patched.
- A contract test suite, one shared set of assertions run against every
  concrete implementation of the stable package's interface, becomes
  possible once the interface exists, and catches an implementation that
  satisfies the type signature but violates the behavioural contract the
  other implementations honour.
- Architecture tests, described further in dimension 16, can assert the
  dependency direction directly, failing a build the moment
  StablePackage's source imports anything from
  ConcreteImplementationPackage, which turns a design rule into an
  automatically enforced one.

Harder because of the pattern.

- A reader or a debugger stepping through DependentPackage's call into the
  interface lands on the interface declaration, not on executing code, and
  must locate the concrete implementation separately, usually by searching
  for implementers or by inspecting how the composition root wired the
  call.
- Verifying that abstractness genuinely improved, rather than only adding
  a wrapper interface with no independent value, requires either a second
  implementation to already exist or a specific plan for one; a lone
  interface with one implementer and no test double does not by itself
  prove the refactor was worth its cost, as named in dimension 11.

Techniques that apply.

- **Architecture fitness function, sometimes implemented as a dependency
  direction test.** A single automated test, run in CI, that asserts no
  file inside StablePackage imports anything from
  ConcreteImplementationPackage. ArchUnitTS, shown in dimension 9, ships
  this as a first-class assertion type built directly on the distance
  metric.
- **Type-per-consumer instantiation test.** For each DependentPackage,
  one test constructs it with a fake implementation of the stable
  interface and asserts the expected calls occur, proving the dependency
  really runs through the interface and not, silently, through a
  concrete import that slipped past review.
- **Metric threshold in CI.** A build step that fails when a package's
  computed distance from the main sequence exceeds a team-agreed
  threshold, the same way a coverage threshold gates a build, using any of
  the tools named in dimension 9. This turns the zone of pain and the zone
  of uselessness from a manual audit finding into an automatic build
  failure.
- **Property test on the contract.** When several concrete implementations
  exist, a property-based test that generates inputs and asserts every
  implementation satisfies the same invariant catches behavioural drift
  between implementations that a type checker cannot see, because the
  type checker only confirms the signature matches, not the behaviour.

## 16. Observability signals

SAP itself is a build-time and architecture-review signal rather than a
runtime one, so what is recorded is a snapshot of the dependency graph,
not a trace of a running request.

What to record.

- Per-package Ca, Ce, computed instability, computed abstractness, and
  computed distance from the main sequence, generated on every build or on
  a scheduled architecture scan, and stored so the values can be compared
  release over release.
- A count of packages whose distance from the main sequence exceeds the
  team's agreed threshold, tracked as a trend over time rather than a
  single snapshot, so a slow drift into the zone of pain is visible before
  it becomes a crisis.
- For each abstract type in a stable package, the number of concrete
  implementations found in the codebase, which is the single fastest check
  for the zone of uselessness failure mode named in dimension 11, an
  interface count of zero or one implementation.
- Where a dependency injection container performs the wiring, a log of
  which concrete type was bound to which interface at application startup,
  so a production incident review can confirm which implementation was
  actually in play without reading source code under time pressure.

A healthy instance on a dashboard. Most packages cluster near the diagonal
line from full abstractness at zero instability to full concreteness at
full instability, the main sequence, with distance values close to zero.
The count of packages flagged as far from the main sequence stays flat or
falls over successive releases. Stable, low-instability packages show a
high abstractness ratio and, for each interface, at least two consumers or
implementations, evidence the abstraction is earning its cost rather than
sitting unused.

A failing instance. A cluster of packages sits in the bottom left of the
graph, low abstractness and low instability, the zone of pain, and that
cluster is growing release over release, which is the schema-style failure
named in dimension 11 accumulating rather than being caught. Or a cluster
sits in the top right, high abstractness and high instability, the zone of
uselessness, which usually means interfaces are being introduced ahead of
real demand. Or the flagged-package count spikes sharply in one release,
which localises exactly which change introduced a new concrete dependency
into a package that was previously clean, without anyone needing to read
the diff by hand first.

## 17. Security and privacy implications

The principle is a design-time and build-time concern, and it has no
runtime attack surface of its own; a package's abstractness score is not
something an attacker interacts with directly. That said, three practical
implications follow from applying it, stated honestly rather than
invented for completeness.

**Abstraction hides the concrete security boundary from a casual
reader.** A stable package expressed as an interface, for instance an
authentication port, deliberately does not show which concrete
implementation is bound at runtime, which is the whole design payoff. The
same property means a security reviewer auditing DependentPackage cannot
determine from that package alone which concrete class actually validates
a credential, verifies a signature, or enforces a permission; the review
must also trace the composition root's wiring to know what code path is
truly executing. Teams applying SAP to a security-sensitive boundary
should keep the wiring, the binding from interface to concrete
implementation, in one clearly named, easily located composition root
rather than scattered across several dependency injection configuration
files, precisely so a security review can find it.

**A widened extension point is a widened supply chain surface.** Making a
package abstract specifically so that a second, third, or Nth
implementation can be added later means, by construction, that new code
elsewhere in the system, potentially from a different team, a plugin, or a
third-party package, can now satisfy that interface and be wired into a
position the original stable package's authors trusted implicitly. This is
the identical concern the Factory Method entry raises about untrusted
implementors of a published extension point, applied here at the scale of
an entire package boundary rather than a single method; the same guidance
applies, validate what a new implementation actually does rather than
trusting that satisfying the interface's type signature implies safe or
correct behaviour.

**Static analysis of Ca and Ce, run as part of a build, reads the whole
dependency graph, including internal package names.** In most codebases
this is not sensitive information, but in a codebase where package or
module names encode something confidential, an unreleased product name, an
internal codename, or a client-specific integration, the generated metrics
report is itself a document that describes the shape of that unreleased or
confidential work, and should be handled with the same access control as
any other internal architecture document, not published to a public
dashboard by default.

On data privacy specifically the principle is silent; it says nothing
about what data flows through a package, only about how many other
packages depend on it and how abstract its types are.

## Code examples

Three languages, all illustrating the metric computation itself, since the
Stable Abstractions Principle is a property of a dependency graph rather
than a single class-level idiom, so the most faithful runnable example is
a small program that computes Ca, Ce, instability, abstractness, and
distance for a handful of representative packages. Java is omitted here
because dimension 9 already demonstrates the identical formula read
directly from JDepend's real production source, and repeating the same
Java shape as a fourth example would add length without adding a new
idiom. TypeScript, Python, and Go were chosen because each shows a
different natural home for the abstraction being measured, an interface in
TypeScript, a Protocol or ABC in Python, and an implicitly satisfied
interface in Go, the idiomatic form noted in dimension 8.

### Python

```python
from dataclasses import dataclass


@dataclass
class Package:
    name: str
    total_classes: int
    abstract_classes: int
    afferent: int = 0  # Ca, incoming dependents
    efferent: int = 0  # Ce, outgoing dependencies

    def instability(self) -> float:
        total = self.afferent + self.efferent
        return self.efferent / total if total else 0.0

    def abstractness(self) -> float:
        return self.abstract_classes / self.total_classes if self.total_classes else 0.0

    def distance(self) -> float:
        return abs(self.abstractness() + self.instability() - 1)


def zone_of(a: float, i: float) -> str:
    if a < 0.3 and i < 0.3:
        return "zone of pain"
    if a > 0.7 and i > 0.7:
        return "zone of uselessness"
    return "main sequence"


def report(packages: list[Package]) -> None:
    for p in packages:
        i, a, d = p.instability(), p.abstractness(), p.distance()
        print(f"{p.name:14s} I={i:.2f} A={a:.2f} D={d:.2f}  {zone_of(a, i)}")


if __name__ == "__main__":
    schema = Package("db-schema", total_classes=40, abstract_classes=0, afferent=30, efferent=1)
    contract = Package("http-contract", total_classes=6, abstract_classes=6, afferent=12, efferent=1)
    orphan = Package("unused-plugin", total_classes=8, abstract_classes=8, afferent=0, efferent=2)
    report([schema, contract, orphan])
```

Compiled and run with `python3`. Output confirmed.

```
db-schema      I=0.03 A=0.00 D=0.97  zone of pain
http-contract  I=0.08 A=1.00 D=0.08  main sequence
unused-plugin  I=1.00 A=1.00 D=1.00  zone of uselessness
```

### TypeScript

```typescript
interface PackageMetrics {
  name: string;
  totalClasses: number;
  abstractClasses: number;
  afferent: number;
  efferent: number;
}

function instability(p: PackageMetrics): number {
  const total = p.afferent + p.efferent;
  return total === 0 ? 0 : p.efferent / total;
}

function abstractness(p: PackageMetrics): number {
  return p.totalClasses === 0 ? 0 : p.abstractClasses / p.totalClasses;
}

function distance(p: PackageMetrics): number {
  return Math.abs(abstractness(p) + instability(p) - 1);
}

function zoneOf(a: number, i: number): string {
  if (a < 0.3 && i < 0.3) return "zone of pain";
  if (a > 0.7 && i > 0.7) return "zone of uselessness";
  return "main sequence";
}

const packages: PackageMetrics[] = [
  { name: "db-schema", totalClasses: 40, abstractClasses: 0, afferent: 30, efferent: 1 },
  { name: "http-contract", totalClasses: 6, abstractClasses: 6, afferent: 12, efferent: 1 },
  { name: "unused-plugin", totalClasses: 8, abstractClasses: 8, afferent: 0, efferent: 2 },
];

for (const p of packages) {
  const i = instability(p);
  const a = abstractness(p);
  const d = distance(p);
  console.log(
    `${p.name.padEnd(14)} I=${i.toFixed(2)} A=${a.toFixed(2)} D=${d.toFixed(2)}  ${zoneOf(a, i)}`
  );
}
```

Compiled with `npx tsc --target es2020 --module commonjs`, run with
`node`, output confirmed identical to the Python run above.

### Go

Go has no inheritance, so nothing here mirrors a class hierarchy. What
translates directly is the package-level metric itself, and the idiomatic
Go form of the abstraction SAP asks a stable package to hold, an interface
declared by the consumer, satisfied implicitly, with no `implements`
keyword and no explicit dependency from the concrete type back to the
interface.

```go
package main

import (
	"fmt"
	"math"
)

type pkg struct {
	name          string
	totalClasses  int
	abstractCount int
	afferent      int
	efferent      int
}

func (p pkg) instability() float64 {
	total := p.afferent + p.efferent
	if total == 0 {
		return 0
	}
	return float64(p.efferent) / float64(total)
}

func (p pkg) abstractness() float64 {
	if p.totalClasses == 0 {
		return 0
	}
	return float64(p.abstractCount) / float64(p.totalClasses)
}

func (p pkg) distance() float64 {
	return math.Abs(p.abstractness() + p.instability() - 1)
}

func zoneOf(a, i float64) string {
	switch {
	case a < 0.3 && i < 0.3:
		return "zone of pain"
	case a > 0.7 && i > 0.7:
		return "zone of uselessness"
	default:
		return "main sequence"
	}
}

func main() {
	packages := []pkg{
		{"db-schema", 40, 0, 30, 1},
		{"http-contract", 6, 6, 12, 1},
		{"unused-plugin", 8, 8, 0, 2},
	}
	for _, p := range packages {
		i, a, d := p.instability(), p.abstractness(), p.distance()
		fmt.Printf("%-14s I=%.2f A=%.2f D=%.2f  %s\n", p.name, i, a, d, zoneOf(a, i))
	}
}
```

Run with `go run`, output confirmed identical to the Python and
TypeScript runs above.

## 18. References

1. Robert C. Martin. *Design Principles and Design Patterns*. 2000. Source
   of the original statement of the three package coupling principles,
   the Acyclic Dependencies Principle, the Stable Dependencies Principle,
   and the Stable Abstractions Principle, as a set. Origin and grouping
   corroborated via Wikipedia contributors, "Package principles",
   https://en.wikipedia.org/wiki/Package_principles verified 2026-08-02.
2. Robert C. Martin. *Agile Software Development, Principles, Patterns,
   and Practices*. Prentice Hall, 2002. The book-length restatement of the
   package design principles, cited directly by NDepend and Lattix
   documentation as the origin of the Ca, Ce, Instability, Abstractness,
   and Distance formulas, see references 4 and 5 below.
3. Robert C. Martin. *Clean Architecture. A Craftsman's Guide to Software
   Structure and Design*. Prentice Hall, 2017. ISBN 978-0-13-449416-6.
   Part IV, Component Principles, Chapter 14, Component Coupling. Source
   of the restated principle, the fan-in and fan-out terminology, and the
   relationship between the Stable Dependencies Principle and the Stable
   Abstractions Principle. Chapter number and title independently
   confirmed by a chapter-by-chapter summary,
   https://www.letscodethemup.com/clean-architecture-chapter-14-component-coupling-sap-the-stable-abstractions-principle/
   verified 2026-08-02, and by a direct GitHub reading summary,
   https://github.com/serodriguez68/clean-architecture/blob/master/part-4-component-principles.md
   verified 2026-08-02.
4. NDepend documentation. "Code metrics definitions."
   https://www.ndepend.com/docs/code-metrics
   Verified 2026-08-02. Source for the NDepend production use in
   dimension 9, and for the explicit attribution of Ca, Ce, Abstractness,
   Instability, and Distance to Martin's book.
5. Lattix documentation. "Metrics."
   https://docs.lattix.com/lattix/userGuide/Metrics.html
   Verified 2026-08-02. Source for the Lattix production use in
   dimension 9.
6. GitHub, clarkware/jdepend. `src/jdepend/framework/JavaPackage.java`.
   https://raw.githubusercontent.com/clarkware/jdepend/master/src/jdepend/framework/JavaPackage.java
   Verified 2026-08-02. Source code read directly for the JDepend
   production use in dimension 9, including the volatility-weighted
   distance variant in dimension 8.
7. ArchUnitTS documentation. `DistanceFromMainSequence` class reference.
   https://lukasniessen.github.io/ArchUnitTS/classes/DistanceFromMainSequence.html
   Verified 2026-08-02. Source for the ArchUnitTS production use in
   dimension 9 and the architecture fitness function technique in
   dimension 15.
8. Wikipedia contributors. "Software package metrics."
   https://en.wikipedia.org/wiki/Software_package_metrics
   Verified 2026-08-02. Used to confirm the standard forms of the
   afferent coupling, efferent coupling, instability, abstractness, and
   distance formulas as commonly restated from Martin's work.
9. Kevin Buchanan. "The Stable-Abstraction Principle."
   https://kevbuchanan.github.io/posts/stable-abstraction-principle
   Verified 2026-08-02. Used to corroborate the exact one-sentence
   statement of the principle and the zone of pain and zone of
   uselessness terminology and examples.
10. Mohammad Raji and Behzad Montazeri. "On the Relationship Between
    Modularity and Stability in Software Packages." arXiv:1812.01061,
    2018. University of Tennessee and Razi University. Retrieved and
    read directly, https://arxiv.org/pdf/1812.01061 verified 2026-08-02.
    Independent academic restatement of Martin's instability formula and
    the reasoning behind the Stable Abstractions Principle, used to
    corroborate the forces described in dimension 3.
