# Family 04. Principles and Laws

Origin. Martin, Larman, Brewer, Conway

42 entries, 327,241 words. Every entry carries all 18
dimensions from [the entry contract](../../docs/ENTRY-TEMPLATE.md).

## Design Principle

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Acyclic Dependencies Principle](acyclic-dependencies-principle.md) | canonical | 8,479 | A codebase of any real size is not one file. |
| [Composable](composable.md) | canonical | 7,680 | Every system with more than one moving part eventually needs behavior that no single unit provides on its own. |
| [Dependency Inversion Principle](dependency-inversion-principle.md) | canonical | 7,097 | A codebase grows outward from a small number of policy decisions, what the system does, in what order, and why. |
| [Inversion of Control](inversion-of-control.md) | canonical | 4,789 | In an ordinary, un-inverted call structure, application code owns the entry point. |
| [Predictable](predictable.md) | canonical | 9,475 | A caller who invokes an operation, reads an API's documentation, or pulls a dependency's published version needs to know, before acting, what is going to happen. |
| [Stable Abstractions Principle](stable-abstractions-principle.md) | canonical | 8,095 | A codebase accumulates two kinds of code over its life. |
| [Unix Philosophy (CUPID)](unix-philosophy-cupid.md) | established | 5,536 | A function, class, module, or service accumulates responsibility over time because adding one more branch to something that already exists is almost always locally cheaper than ... |

## Package and Component Design

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Common Reuse Principle](common-reuse-principle.md) | canonical | 7,467 | A team ships a library, an internal package, or a service client as one deployable unit. |

## Principle

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [ACID](acid.md) | canonical | 7,029 | A database serves many concurrent operations against shared, durable state. |
| [BASE](base.md) | canonical | 8,219 | A system holds one logical piece of data on more than one physical machine, because a single machine cannot serve the read and write volume, cannot survive its own failure, or ... |
| [CAP Theorem](cap-theorem.md) | canonical | 7,623 | A system holds one piece of mutable state that more than one machine can read and write, and those machines are connected by a network that is not perfectly reliable. |
| [Common Closure Principle](common-closure-principle.md) | canonical | 7,574 | A codebase reaches the size where a single flat namespace of classes stops being a unit anyone can reason about, and the team splits it into smaller compilation and deployment ... |
| [Composition over Inheritance](composition-over-inheritance.md) | canonical | 6,930 | A designer needs an object to have several independent, combinable behaviours, and reaches for a single class hierarchy to express all of them. |
| [Controller](controller.md) | canonical | 6,874 | A team wiring a new interaction into an object-oriented system reaches a concrete, recurring question the moment a user clicks a button, submits a form, or an external system ... |
| [Conway's Law](conway-law.md) | canonical | 7,751 | A team is asked to build a system with several distinct concerns. |
| [Creator](creator.md) | canonical | 7,514 | Every object-oriented system eventually needs a new object of type A to come into existence somewhere, and the code that calls the constructor has to live in some class B. |
| [Do Not Repeat Yourself](do-not-repeat-yourself.md) | canonical | 6,449 | A single fact about the system, a tax rate, a validation rule, a URL, a unit conversion, a business rule about who is allowed to approve a refund, gets written down in more than ... |
| [Fail Fast](fail-fast.md) | established | 7,090 | A running program encounters a state it was not written to handle correctly. |
| [High Cohesion](high-cohesion.md) | canonical | 8,014 | A team splits a system into modules, classes, packages, or services, and almost every split is defensible on some axis. |
| [Idiomatic](idiomatic.md) | canonical | 7,073 | A person who learns to program in one language carries that language's mental model into every language learned afterward. |
| [Indirection](indirection.md) | canonical | 8,493 | Two parts of a system need to interact, but binding them together directly creates a cost that shows up later rather than now. |
| [Information Expert](information-expert.md) | canonical | 7,089 | A team building an object model reaches a point, usually within the first design session, where a piece of business logic needs a home. |
| [Interface Segregation Principle](interface-segregation-principle.md) | canonical | 9,180 | The problem ISP names is specific and recognizable once you have seen it. |
| [Keep It Simple](keep-it-simple.md) | canonical | 8,079 | Every non-trivial piece of software accretes complexity over its lifetime, and that accretion happens in two very different ways that are easy to conflate. |
| [Law of Demeter](law-of-demeter.md) | canonical | 7,910 | A method reaches through an object it was handed to get at a second object, then calls a method on that second object. |
| [Low Coupling](low-coupling.md) | canonical | 7,282 | Every nontrivial system is built from more than one unit of code, whether those units are classes in one process, packages in one codebase, or services across a network. |
| [Open Closed Principle](open-closed-principle.md) | canonical | 5,598 | A piece of software that ships once and never changes does not need this principle. |
| [PACELC Theorem](pacelc-theorem.md) | canonical | 9,039 | A team picks a distributed database, reads that it is "AP" or "CP" under CAP, and believes that single letter fully describes how the system will behave in production. |
| [Postel's Law](postel-law.md) | contested | 8,878 | Two or more parties implement the same open, published specification independently, without coordinating their release schedules, their source code, or in most cases even knowing ... |
| [Principle of Least Astonishment](principle-of-least-astonishment.md) | canonical | 9,080 | A person interacts with a piece of software, whether by reading its code, by calling its API, by typing a command at a shell, or by clicking a button in a user interface, and ... |
| [Protected Variations](protected-variations.md) | canonical | 8,161 | A system is never finished changing. Requirements shift, a vendor is replaced, a data format gains a field, a regulator adds a rule, a second platform needs support, a team splits ... |
| [Pure Fabrication](pure-fabrication.md) | canonical | 7,604 | A designer following Information Expert as the default rule will, for a large share of responsibilities, land on the right class without further thought. |
| [Release Reuse Equivalence](release-reuse-equivalence.md) | canonical | 8,321 | The problem REP addresses shows up the moment more than one piece of software wants to depend on the same piece of source code. |
| [Separation of Concerns](separation-of-concerns.md) | canonical | 10,250 | A codebase grows by accretion. A new requirement lands, and the fastest way to satisfy it is to add a few lines wherever the relevant data already sits in memory. |
| [Single Responsibility Principle](single-responsibility-principle.md) | canonical | 8,408 | The problem SRP names is a specific, recognizable shape of decay. |
| [Single Source of Truth](single-source-of-truth.md) | canonical | 8,258 | A fact about the world gets written down more than once, in more than one system, in more than one file, or in more than one variable, because writing it again was faster than ... |
| [Stable Dependencies Principle](stable-dependencies-principle.md) | canonical | 8,881 | A system of any real size is built from more than one compilation or deployment unit, whatever the language calls that unit, a package, a module, a JAR, a crate, an npm package ... |
| [Tell, Don't Ask](tell-do-not-ask.md) | canonical | 9,194 | The problem this principle answers shows up the first time a codebase grows past the size where one person holds the whole design in their head. |
| [You Aren't Gonna Need It](you-are-not-gonna-need-it.md) | canonical | 8,862 | A developer sits inside a piece of work that is genuinely needed today, and partway through, notices a plausible future requirement. |

## Principles and Laws

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Liskov Substitution Principle](liskov-substitution-principle.md) | canonical | 6,210 | Object-oriented languages let a caller hold a reference typed as a base class or an interface and receive, at runtime, any one of several concrete subtypes. |
| [Polymorphism](polymorphism.md) | canonical | 7,452 | A piece of client code needs to perform an operation, render a shape, calculate a price, serialize a value, and it needs to do so uniformly over a collection of things that are ... |

## Structural principle

| Pattern | Maturity | Words | Intent |
|---|---|---|---|
| [Domain-based](domain-based.md) | canonical | 8,254 | A system of any real size grows two kinds of edges as it is built. |

## Reading order

Entries are independent. Each one names the patterns it composes with and
the patterns it conflicts with in dimension 13, so following those links
gives a better path than reading top to bottom.

Generated by `tools/gen-indexes.py`. Do not edit by hand.
