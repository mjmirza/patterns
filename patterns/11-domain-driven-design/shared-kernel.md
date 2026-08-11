---
name: Shared Kernel
slug: shared-kernel
family: 11-domain-driven-design
category: Strategic Design
aliases: [Shared Kernel Context, Kernel Sharing]
first_described: "Evans 2003"
maturity: canonical
related: [bounded-context, context-map, ubiquitous-language, anticorruption-layer, published-language, core-domain]
incompatible_with: [conformist, anticorruption-layer-as-primary-boundary]
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

The canonical name is Shared Kernel. Eric Evans introduced it in "Domain-Driven
Design. Tackling Complexity in the Heart of Software" (Addison-Wesley, 2003),
Part IV, Chapter 14, "Maintaining Model Integrity," as one of the named
relationships a team can choose when two Bounded Contexts need to interoperate.
Evans states the pattern directly in that chapter, designate some subset of the
domain model that the two teams agree to share, keep that subset small, and do
not change it without consulting the other team first. The subset itself, the
shared portion of code and the model it expresses, is what Evans calls the
kernel, and the arrangement between the two teams is the Shared Kernel
relationship.

Vaughn Vernon's "Implementing Domain-Driven Design" (Addison-Wesley, 2013),
Chapter 3, "Context Maps," restates the pattern as one of the eight named
Context Map relationships and adds an operational detail Evans left implicit,
a Shared Kernel needs its own build, its own version number, and its own
continuous integration step, because it is a real, separately compiled
artifact that two teams both depend on, not a folder either team can edit
freely inside its own repository. Evans's later summary document,
"Domain-Driven Design Reference. Definitions and Pattern Summaries" (Domain
Language, Inc., self-published, 2015), lists Shared Kernel alongside Bounded
Context, Continuous Integration, Context Map, Customer-Supplier Development
Teams, Conformist, Anticorruption Layer, Separate Ways, Open Host Service, and
Published Language as the nine strategic design patterns that populate a
Context Map, and gives Shared Kernel the same one-line definition used in the
2003 book.

The name is occasionally confused with two things it is not. A shared code
library that every team in an organization is required to use, sometimes
called a "core library" or a "common utils" package, is not automatically a
Shared Kernel in the Evans sense unless the two consuming sides are genuinely
separate Bounded Contexts with their own models, and the shared part
genuinely carries domain meaning rather than pure infrastructure code such as
a logging wrapper or an HTTP client. A single team's internal module
structure, where one team owns several packages inside one Bounded Context,
is also not a Shared Kernel, because Shared Kernel is a relationship between
two Bounded Contexts owned by two different teams, and a single team sharing
code with itself is simply modular design inside one context. This entry
uses "team" the way Evans and Vernon use it, an organizational unit with its
own release cadence and its own accountability for a model, which in a small
organization can be one or two people, and in a large one is a department.

## 2. Problem and context

Two Bounded Contexts model a piece of the domain in a compatible way, not
because either team designed it that way on purpose, but because the concept
genuinely is the same concept in both places. A payments team and an
invoicing team both need a `Money` type with a currency and an amount that
rounds and compares the same way in both systems, because a rounding
difference between the two would produce a ledger that does not reconcile.
An order-taking team and a fulfillment team both need the same
`ShipmentRequested` event shape, because if the two teams draw the event
independently, one will eventually add a field the other silently ignores,
and a shipment will go out with the wrong address because the two teams read
"address" to mean two different things.

The two teams face a choice. They can duplicate the type in both codebases
and translate between the two representations at every boundary, which is
the Anticorruption Layer or Published Language response and is the default,
recommended posture in Evans's own text. Or, for the narrow subset of the
model where duplication would create more risk than the coupling it avoids,
because the two teams already agree on the concept and disagreeing later
would be a bug rather than a legitimate difference in perspective, they can
choose to share the actual code. That second choice is Shared Kernel. It is a
deliberate, narrow exception to the default rule that each Bounded Context
owns its own model, made because for this specific subset, translation adds
cost without adding safety, since a translation step between two
representations of the same rounding rule for `Money` cannot catch the case
where the two representations quietly drift apart, it can only formalize the
drift once it has already happened.

The context in which this problem is legitimate to solve with Shared Kernel,
rather than with a full Anticorruption Layer, is narrow. Evans is explicit
that the teams involved must be able to communicate frequently, must be
willing to treat a change to the shared code as a joint decision rather than
a unilateral one, and must have low enough organizational distance that a
change lands in both codebases close together in time. Two teams in
different companies, two teams on different continents with no overlapping
work hours, or two teams whose release cycles are measured in quarters
rather than days, are not in the right context for this pattern, whatever
their models happen to agree on.

## 3. Forces

Consistency versus autonomy is the dominant force. A Shared Kernel buys exact
consistency for the shared subset, the two sides cannot drift because they
are, mechanically, running the same code, but it spends autonomy to get
there, because neither team can change the kernel without the other team's
agreement, and a change one team needs on its own schedule now has to wait
for a joint decision. Duplication with translation gives each side full
autonomy over its own copy at the cost of a permanent risk that the two
copies drift, caught only by tests or by production incidents.

Coupling versus translation cost is the second force. Shared Kernel removes
the translation step entirely for the shared subset, no mapping code, no
anticorruption layer, no risk that the mapping itself has a bug. In exchange
it accepts the tightest coupling a Context Map relationship can have, a
shared compiled artifact, a shared deploy dependency, and in most
implementations a shared version number that both sides must bump together.
Every other Context Map relationship, Customer-Supplier, Conformist, Open
Host Service with Published Language, keeps the translation cost and buys
looser coupling in return.

Team communication overhead is the third force, and it is the one most
teams underweight when they first reach for this pattern. A Shared Kernel is
not free once it is built, it is a standing coordination cost, every change
to the kernel needs a conversation, a joint review, and a joint release,
forever, for as long as the kernel exists. Evans's own guidance in Chapter
14 is to run frequent, even daily, integration of the kernel precisely
because the alternative, letting each side's copy of the kernel drift out of
sync between infrequent syncs, defeats the entire purpose of sharing the
code in the first place, and produces the worst of both worlds, coupling
without consistency.

Blast radius is the fourth force. Because the kernel is compiled into or
imported by both sides, a defect in the kernel is a defect in both Bounded
Contexts simultaneously. A duplication approach contains a defect to one
side until the other side independently makes, or does not make, the same
mistake. This is a real cost of Shared Kernel that the pattern's proponents
sometimes understate, a shared kernel is a single point of correctness for
two systems, and a regression in it ships to both at once.

Cognitive load is the fifth force. A developer working in either Bounded
Context has to hold in their head that a piece of the code they are looking
at is not owned by their team alone, that changing it requires a
cross-team conversation they might not think to start, and that the
change control process for this one folder or package is different from
the change control process for the rest of the codebase around it. This
asymmetry inside a single codebase, most of the code moves at the speed of
one team, a small slice moves at the speed of a negotiated agreement between
two, is itself a maintenance cost independent of the technical coupling.

## 4. Applicability and non-applicability

Reach for Shared Kernel when all of the following hold at once. Two Bounded
Contexts are owned by teams that communicate frequently and can schedule a
joint code review and a joint release within days, not months. The concept
being shared genuinely means the same thing in both contexts, verified by
both teams' domain experts agreeing on a single definition, not by a
developer on one side noticing a superficial resemblance. The shared subset
is small, ideally a handful of value objects, a shared identifier type, or a
small number of stable domain events, never an entire aggregate or an entire
context's worth of entities. The cost of a translation layer between the two
contexts would be real and ongoing, not hypothetical, because the two
representations would otherwise need to be kept manually synchronized by a
person reading both codebases and updating both by hand. And the
organization is willing to accept that a change to the kernel is a two-team
decision, encoded in an actual process such as a required review from the
other team's lead, not merely a shared understanding that everyone forgets
under deadline pressure.

Do not reach for Shared Kernel in the following situations, and the reason
is given for each, because this is the list most catalogs leave out.

Two teams belong to different companies, or to the same company but
different reporting lines with materially different roadmaps and different
release cadences. The coordination cost the pattern demands cannot be paid
reliably across that organizational distance, and the relationship degrades
into one side treating the kernel as if it were an external dependency it
does not control, which is a worse outcome than an honest Customer-Supplier
or Conformist relationship chosen up front.

The concept looks similar but is not actually the same concept, for example
"Customer" in a billing context, which needs a payment method and a credit
limit, and "Customer" in a support context, which needs a contact preference
and a case history. Sharing the type here does not remove translation cost,
it hides the fact that the two sides need different fields and different
invariants, and the shared type either grows an unmanageable list of
optional fields to serve both sides or one side quietly abuses the type for
data it was never designed to hold. This is the single most common misuse
of the pattern, covered further in dimension 11.

The two contexts have very different rates of change, one is actively being
rewritten every sprint while the other is stable and rarely touched. A
volatile side dragging a stable side into its churn through a shared
artifact defeats the reason the stable side chose to be stable, and the
stable team ends up reviewing and re-releasing for changes it did not want
and does not benefit from.

A large or growing portion of the model would need to be shared for the two
sides to interoperate correctly. At that point the two contexts are not
really separate Bounded Contexts sharing a kernel, they are one context that
has been split by an org chart rather than by a genuine seam in the domain,
and the correct fix is to redraw the boundary, either merging the contexts
back together under one team or shrinking the shared surface until only the
genuinely stable, genuinely agreed part remains.

The relationship between the two contexts is asymmetric, one side is the
authority on the concept and the other side is a downstream consumer that
should adapt to whatever the authority publishes. That relationship is
Customer-Supplier or, when the downstream side has no negotiating power at
all, Conformist, and forcing it into Shared Kernel's mutual, symmetric
governance model creates friction because one side genuinely does not want
a vote in the other side's decisions, it wants a stable published contract
it can adapt to on its own schedule. Open Host Service with a Published
Language is the better fit there.

## 5. Structure

Two Bounded Contexts, each owned by its own team, each with its own model,
its own database, and its own deployment. A third artifact, the kernel,
sits between them, containing a deliberately small set of types, value
objects, domain events, or shared identifiers, that both contexts compile
against or import directly. The kernel is not a running service and does
not have its own database, it is source code or a compiled library, and it
has no behavior beyond what the shared types themselves carry, invariant
enforcement inside a value object's constructor, equality and comparison
logic, and serialization. A governance mechanism, most often a required
review from both teams before a change to the kernel merges, and a shared
continuous integration pipeline that builds and tests both contexts against
any proposed kernel change before it is accepted, sits alongside the kernel
itself and is, in practice, as much a part of the pattern as the code.

The participants are these four. Context A and Context B, two Bounded
Contexts, each with its own team, its own aggregates, its own repository
implementations, and its own release pipeline, that both depend on the
kernel for the small shared subset of the model. The kernel, the shared
code artifact itself, a package, a library, or a vendored module,
containing only the value objects, events, and identifier types both teams
have agreed genuinely mean the same thing in both contexts. The kernel's
governance process, the joint review requirement, the shared CI check, and
the versioning discipline that keeps changes to the kernel a two-team
decision rather than either team's unilateral choice. And the kernel's own
test suite, tests that exercise the invariants of the shared types in
isolation from either context, so a defect in the kernel is caught before
it reaches either consuming side, plus, where practical, a contract test
run from each context's own test suite against the kernel it currently
depends on.

## 6. ASCII structure diagram

```
+-----------------------------+          +-----------------------------+
|   Bounded Context. Billing  |          | Bounded Context. Fulfillment|
|   (owned by Team Billing)   |          | (owned by Team Fulfillment) |
|                              |          |                              |
|  Invoice, Payment,           |          |  Shipment, Route,            |
|  BillingAccount               |          |  DeliveryWindow              |
+---------------+---------------+          +---------------+---------------+
                |                                            |
                | imports / depends on                       | imports / depends on
                v                                            v
        +-------------------------------------------------------+
        |                     SHARED KERNEL                     |
        |  Money (currency, amount, rounding rule)               |
        |  OrderId (identifier type, equality, parsing)          |
        |  ShipmentRequested (domain event, field shape)         |
        +-------------------------------------------------------+
                                    |
                                    | governed by
                                    v
                +---------------------------------------+
                |  Joint review + shared CI + version tag |
                |  (both teams sign off, both teams test) |
                +---------------------------------------+
```

The kernel sits below both contexts, not beside them, because it is a
dependency both contexts pull in, never a service either context calls.
There is no arrow from Billing to Fulfillment or from Fulfillment to
Billing directly, the two contexts remain otherwise decoupled, integrating
by ordinary means such as events or an API for everything outside the
kernel's small surface.

## 7. Dynamics

The dynamics of Shared Kernel are almost entirely about how a change to the
kernel travels, because at runtime the kernel is inert code linked into two
otherwise independent systems, there is no message passing between the two
contexts through the kernel itself.

```
Developer on Team Billing needs to add a field to Money
        |
        v
Opens a change against the kernel repository or package
        |
        v
CI builds the kernel, then builds Context A (Billing) against the
proposed kernel, then builds Context B (Fulfillment) against the
same proposed kernel
        |
        v
Team Fulfillment is required to review the change before merge,
because their build depends on the same artifact
        |
        +-- Fulfillment objects. the field breaks an existing invariant
        |   they rely on
        |         |
        |         v
        |   Change is revised or the two teams agree on a version
        |   that adds the field without breaking the old shape
        |
        +-- Fulfillment approves
                  |
                  v
        Kernel version is bumped, published, or merged
                  |
                  v
        Both contexts update their dependency on the new kernel
        version, on their own release schedule, but neither can
        stay indefinitely on the old version if the old version
        is retired
                  |
                  v
        Both contexts' own CI, running their own test suites,
        confirms the new kernel version has not broken anything
        the context relies on
```

At ordinary runtime, once the kernel version both contexts depend on is
settled, a request into Context A that touches a `Money` value and a
request into Context B that touches the same `Money` type run the identical
constructor, the identical rounding rule, and the identical equality
comparison, because it is the same bytecode or the same compiled object
code in both processes. This is the entire payoff of the pattern, no
message crosses a wire to keep the two sides consistent, consistency is a
property of both sides literally running the same code, not of any
synchronization protocol between them.

## 8. Implementation variants

**Shared library published to a package registry.** The most common variant
in practice. The kernel is built as its own artifact, an npm package, a
NuGet package, a PyPI package, a Maven artifact, published to a registry
either team can consume, with an explicit semantic version. Both contexts
declare a dependency on a specific version. This variant makes the
"separately built and versioned" nature of the kernel explicit and gives
each side a controlled moment to adopt a new kernel version, at the cost of
requiring a real publish step for even a small change.

**Shared library as a git submodule or subtree.** The kernel lives in its
own repository, and each context's repository includes it as a submodule or
subtree pinned to a commit. This avoids a package registry publish step but
trades it for the operational friction git submodules are known for,
developers forgetting to update the pinned commit, and a subtree merge that
is easy to get wrong. Teams that choose this variant most often do so
because they already run a monorepo-adjacent workflow and want to avoid
adding a package registry to their toolchain.

**Vendored copy with an explicit sync script.** Some organizations
deliberately avoid a shared build dependency and instead copy the kernel
source files into both contexts' repositories, with a script that diffs the
two copies and fails a build if they have drifted. This variant sacrifices
some of the strict guarantee that both sides run the identical compiled
artifact, since it is possible, briefly, for one side to have merged a sync
and the other not to have, but it removes the coordination cost of shared
build infrastructure and lets each side vendor the kernel using whatever
build tool it already uses.

**Single monorepo with a shared internal package.** When both Bounded
Contexts live in one repository, the kernel is simply an internal package or
module both contexts import, with the joint review requirement enforced by
a code owners file that requires approval from both teams for changes under
the kernel's path. This is the lightest-weight variant operationally,
because there is no separate publish step, but it still requires the same
social discipline, a monorepo does not by itself prevent one team from
editing the shared package without the other team's knowledge, only a code
owners rule or an equivalent review gate does.

**Language-idiomatic shape of the kernel itself.** In a functional-leaning
codebase, the kernel is most often a small set of immutable value types with
pure construction functions and no behavior beyond validation, matching the
shape shown in dimension 6's diagram directly. In an object-oriented
codebase built around aggregates, the kernel is still kept to value objects
and events, never entities or aggregate roots, because sharing an aggregate
root would mean sharing the invariant-enforcing behavior that is supposed to
belong to exactly one Bounded Context's model, which defeats the entire
point of drawing a Bounded Context boundary in the first place.

## 9. Known production uses

The Ardalis.SharedKernel package, published by Steve Smith and maintained on
GitHub as part of the Clean Architecture Solution Template ecosystem, is a
concrete, publicly inspectable shared kernel for .NET, providing base
classes such as `Entity`, `AggregateRoot`, and `DomainEvent` that a Clean
Architecture project's separately structured layers depend on. The repository
itself states plainly that it is intended as a demonstration template rather
than a hardened dependency, and instructs adopting teams to fork it into
their own organization-owned package, for example the sibling
`NimblePros.SharedKernel` package referenced from the same project, which is
itself a direct, documented instance of the Evans guidance that a kernel
should be owned jointly and evolved deliberately rather than pulled in as an
unmanaged third-party dependency. Source, https://github.com/ardalis/Ardalis.SharedKernel,
verified 2026-08-02.

Vaughn Vernon's own reference implementation for "Implementing Domain-Driven
Design" includes an `iddd_common` module in the book's companion source
code, shared across the separately built Bounded Contexts in the sample,
including the identity and access context and the agile project management
context. The module provides identifier and value-object base types that
the separate contexts both depend on, functioning as the book's own worked
example of a Shared Kernel used in service of several otherwise independent
Bounded Contexts. Source, https://github.com/VaughnVernon/IDDD_Samples, module
`iddd_common`, verified 2026-08-02.

Codebelt's `shared-kernel` project, published as the `Codebelt.SharedKernel`
NuGet package and documented at `sharedkernel.codebelt.net`, is a maintained,
independently versioned open source library that names itself explicitly as
an implementation of the Shared Kernel pattern from Domain-Driven Design,
providing `AggregateRoot`, `Entity`, `ValueObject`, `DomainEvent`, and
repository and unit-of-work abstractions intended to be depended on by
multiple, separately owned application codebases. Its documentation and its
release history on the NuGet gallery demonstrate the pattern operating with
the independent versioning and publish discipline described in dimension 8.
Source, https://github.com/codebeltnet/shared-kernel, verified 2026-08-02.

## 10. Consequences

Positive consequences. Exact consistency for the shared subset of the model
is guaranteed mechanically, by the fact that both sides run the same code,
rather than by a discipline of keeping two independently maintained copies
in sync. No translation layer is needed for the shared subset, removing an
entire class of mapping bugs, where a translation between two
representations quietly loses a field or applies a rounding rule
differently than the source. A defect fix in the kernel benefits both
contexts at once, once both sides adopt the fixed version, rather than
needing the fix to be discovered and applied independently on each side.
The pattern also gives two closely collaborating teams a concrete, visible
artifact around which to hold their integration conversation, the pull
request against the kernel, rather than an informal agreement that lives
only in a meeting nobody wrote down.

Negative consequences. Every change to the kernel is a two-team decision,
which slows down any change either side wants to make unilaterally, and this
slowdown compounds as the number of consuming contexts grows past two,
because Evans's guidance assumes the pattern stays between a small number of
closely collaborating teams. A defect in the kernel is a defect in every
consuming context simultaneously, removing the containment that separate
copies would have provided. The coupling is the tightest of any Context Map
relationship, both sides are pinned to compatible versions of the same
build artifact, which means an organizational change, one team being
reorganized, one team's roadmap diverging sharply from the other's, can
strand the pattern in a state where the coordination cost it demands can no
longer be reliably paid. And the pattern is easy to reach for out of
convenience rather than genuine model agreement, which produces the specific
failure mode covered next.

## 11. Failure modes and misuse

**Symptom.** A change to the shared kernel by one team unexpectedly breaks
a build or, worse, a production deploy on the other team's side, and the
other team was not aware the change was coming.
**Cause.** The joint review and joint CI requirement from dimension 5 was
never actually put in place, or was put in place and then quietly bypassed
under deadline pressure, so the kernel is technically shared code but is
socially governed by only one team, which is exactly the arrangement
Evans's chapter warns against.
**Fix.** Add a mechanical code owners rule or an equivalent required-review
gate on the kernel's repository path that cannot be merged around, and wire
the shared CI check described in dimension 6 so that a proposed kernel
change is built against both contexts before it can be merged, not after.

**Symptom.** The shared type keeps growing new, mostly-null optional fields,
and neither team can confidently say which fields the other team actually
needs.
**Cause.** The two contexts do not actually agree on the concept, one side
is using the shared type as a convenient place to bolt on data that belongs
to its own model, rather than the two sides having independently arrived at
the same definition, which is the "looks similar but is not the same
concept" trap named in dimension 4.
**Fix.** Split the type. Move the fields one side needs but the other does
not into that side's own model, leaving the kernel with only the fields
both teams' domain experts can independently justify as meaning the exact
same thing, and if the overlap turns out to be nearly nothing, replace the
Shared Kernel relationship with a translation at the boundary instead, per
dimension 14.

**Symptom.** The two teams stop coordinating kernel changes with each
other's release schedule, and one side is running against a kernel version
weeks or months older than the other, with a growing list of "we will
upgrade later" items.
**Cause.** The coordination overhead named as a force in dimension 3 was
underestimated when the pattern was adopted, and without active
enforcement, the two sides quietly drift back toward independent evolution
while still nominally sharing code, which produces the worst outcome
available, the coupling cost of Shared Kernel with none of its consistency
benefit, because the two sides are no longer actually running the same
version of the shared code.
**Fix.** Set an explicit, short maximum staleness window, for example no
consuming context may run a kernel version more than one release cycle
behind the latest published version, enforced by a CI check that fails the
build once the pinned version is older than the window allows, forcing the
upgrade conversation to happen on a cadence rather than being deferred
indefinitely.

**Symptom.** A third Bounded Context, owned by a third team, starts
depending on the same kernel that two other teams already share, and kernel
changes now require sign-off from three, then four, then five teams, and
nothing about the kernel can move without a lengthy negotiation.
**Cause.** Shared Kernel was scaled past the small, closely collaborating
group of teams the pattern assumes, without anyone deciding to do so on
purpose, the kernel simply accreted new dependents over time because it was
the path of least resistance for each new team that needed the `Money` type
or the `OrderId` type.
**Fix.** Convert the relationship for the newer dependents into a
Published Language served through an Open Host Service instead, so the
original kernel keeps its small, tightly governed group of joint owners,
and the additional teams consume a stable, versioned, one-directional
contract rather than joining the mutual-governance group, per the guidance
in dimension 14.

## 12. Trade-off matrix

Compared against the two nearest named alternatives from the same Context
Map vocabulary, Anticorruption Layer with independent models on both sides,
and Open Host Service paired with a Published Language.

| Force | Shared Kernel | Anticorruption Layer | Open Host Service + Published Language |
|---|---|---|---|
| Consistency of the shared concept | Exact, mechanical, both sides run the same code | Approximate, depends entirely on the correctness of the translation code | Exact for whatever the published contract defines, approximate for anything outside it |
| Coupling | Tightest, shared build artifact, pinned compatible versions | Loosest, each side owns its own model completely | Moderate, downstream depends on a published contract but not on the upstream's internal code |
| Autonomy to change independently | Lowest, kernel changes are a joint decision | Highest, either side changes its own model freely at any time | High for the downstream consumer, moderate for the publishing side, which must version its contract carefully |
| Translation code needed | None for the shared subset | Yes, a full mapping layer at every boundary crossing | Yes, but only at the consuming side, against a stable published shape |
| Best fit | Two closely collaborating teams with genuine model agreement on a small, stable subset | Two teams with different models and no expectation of converging | One authoritative team publishing to several downstream consumers who should not have a say in the model |

## 13. Related and incompatible patterns

Shared Kernel is one of the named relationships that populate a Context Map,
and this entry treats Bounded Context and Context Map as prerequisite
reading, since Shared Kernel only makes sense as a relationship between two
already-identified Bounded Contexts, described fully in this repository's
`context-map` and `bounded-context` entries. Ubiquitous Language is the
closest conceptual relative, because the entire justification for sharing a
piece of the model is that both teams' Ubiquitous Languages genuinely
overlap for that concept, if the two languages diverge later, the kernel has
stopped earning its place and the relationship should be dissolved.

Anticorruption Layer and Published Language are the alternatives this entry
compares against directly in dimension 12, and they are the patterns a team
graduates to when a Shared Kernel relationship is retired, described in
dimension 14. Core Domain, described in this repository's `core-domain`
entry, interacts with Shared Kernel in one specific way worth naming, a
kernel is almost never appropriate for a team's Core Domain itself, because
the Core Domain is precisely the part of the model a team should retain
full, undiluted control over to build a competitive advantage, and sharing
governance of it with another team's priorities undermines that control.
Shared Kernel belongs, when it belongs at all, in the Generic Subdomain or
Supporting Subdomain space, on concepts like money handling or a common
identifier scheme that are necessary but not differentiating.

Shared Kernel is named here as incompatible, in the sense of solving the
same problem with an opposite answer, with treating an Anticorruption Layer
as the exclusive integration mechanism between two contexts that also need
exact consistency on a narrow shared subset, because a team cannot
simultaneously translate a concept at the boundary and share the concept's
actual code, it has to pick one governance model for that concept. It is
also incompatible with the Conformist relationship for the same concept,
because Conformist is a one-sided, asymmetric arrangement where one side
adopts the other's model wholesale with no negotiating power, while Shared
Kernel is explicitly a symmetric, jointly governed arrangement, and applying
both labels to the same relationship at once describes two contradictory
governance structures for the identical piece of code.

## 14. Refactoring path in and out

Refactoring in. Start from two Bounded Contexts that currently integrate
through duplicated types and an ordinary translation layer at their
boundary. Identify the specific value objects or events, using the domain
experts from both sides, not developers alone, where both teams independently
confirm the concept means exactly the same thing and has meant the same
thing without disagreement for some time, typically observed as the
translation code for that specific type never having needed a real mapping
decision, only a straight field-for-field copy. Extract those types into
their own package or module, write the kernel's own test suite against them
in isolation, then switch both contexts to depend on the extracted kernel
in place of their own previously duplicated copies, deleting the now-dead
translation code for that narrow subset. Put the joint review gate and the
shared CI check from dimension 6 in place before, not after, the first
contexts adopt the kernel, because retrofitting governance onto a kernel
that has already drifted unmanaged for a while is materially harder than
establishing it from the extraction commit onward.

Refactoring out. A Shared Kernel earns removal when any of the failure
modes in dimension 11 persist despite an honest attempt at the fixes listed
there, or when the organizational distance between the two teams grows past
what the pattern assumes, one team is reorganized, acquired, or moved to a
different release cadence than the other. The removal path starts by
identifying exactly which fields or which parts of the kernel each side
actually still uses, since kernels tend to accumulate unused surface over
time, then introducing a translation layer, an Anticorruption Layer if the
two sides' models are meant to diverge going forward, or an Open Host
Service with a Published Language if one side is meant to become the
authority and the other a downstream consumer, at the boundary between the
two contexts for the subset being removed from the kernel. Once the
translation layer is in place and both sides' test suites pass against it,
shrink the kernel to only the fields still genuinely needed, and if the
kernel reaches zero fields both sides still share, delete the dependency
entirely and retire the kernel's repository or package, rather than leaving
an empty or near-empty package as a historical artifact nobody remembers
the purpose of.

## 15. Testing and verification

The kernel's own test suite is the first and most important layer, run in
complete isolation from either consuming context, exercising every
invariant the shared value objects and events enforce, equality, rounding,
serialization round trips, and any validation performed in a constructor or
factory function. This suite is what makes a kernel change trustworthy
enough for the other team to review quickly rather than needing to
re-derive correctness from first principles on every proposed change.

Each consuming context's own test suite becomes easier to write for the
specific concepts covered by the kernel, because a test in Context A never
needs to construct a fake or a stub for `Money` or `OrderId`, it uses the
real, shared type directly, the same type production code uses, removing an
entire class of test double drift where a hand-maintained fake silently
falls out of sync with the real type's behavior.

Contract tests running from each context's test suite against the exact
kernel version that context currently depends on are the layer that catches
the failure mode in dimension 11 where a kernel change breaks an assumption
one side relied on. These tests assert behavior the consuming context needs
from the kernel, for example that adding two `Money` values with the same
currency never loses precision, and are run in the shared CI pipeline
described in dimension 6 against any proposed kernel change, before that
change is allowed to merge, which is what turns "the other team should
review this" from a social expectation into a build that fails loudly when
skipped.

What becomes harder to test is the boundary itself, because there is, by
design, no translation layer to test for the shared subset, the correctness
of that subset now depends entirely on the kernel's own tests being
sufficient, which means the kernel's test suite carries more weight per
line than an equivalent amount of code inside either context alone, and
should be reviewed with that weight in mind.

## 16. Observability signals

The version of the kernel each context currently depends on should be
visible in that context's own build metadata, deployment manifest, or a
health-check endpoint, so an operator or either team can answer, without
reading source code, which kernel version production is running right now
on each side. A dashboard or a simple CI check comparing the two sides'
pinned kernel versions and flagging when they diverge beyond the staleness
window from dimension 11 is the direct observability signal for the drift
failure mode, a healthy pair of contexts shows both pinned to the same or
adjacent kernel versions, an unhealthy pair shows a widening gap that
nobody has scheduled time to close.

The kernel repository's own change history, specifically how many proposed
changes required back-and-forth negotiation between the two teams before
merging versus how many merged on the first review, is a signal for whether
the coordination cost from dimension 3 is being paid smoothly or is
becoming a source of friction, a rising rate of contested changes over time
is an early warning that the model agreement underlying the kernel is
starting to erode before it shows up as an outright failure mode.

Build and test duration for the kernel's own CI pipeline is worth watching
directly, because that pipeline sits on the critical path for every kernel
change in both contexts, a slow kernel pipeline adds friction to the
already-heavier joint review process and makes teams more likely to bypass
the process under time pressure, which is exactly the precondition for the
first failure mode in dimension 11.

## 17. Security and privacy implications

A Shared Kernel widens the blast radius of a defect in the shared code to
every consuming context at once, which has a direct security implication,
a vulnerability introduced into the kernel, for example an integer overflow
in a `Money` amount field or an insufficiently validated identifier parser,
is now a vulnerability in every Bounded Context that depends on the kernel
simultaneously, rather than being contained to whichever one context first
introduced it. This is the security-relevant restatement of the blast
radius consequence named in dimension 10, and it argues for the kernel's
own test suite, described in dimension 15, to include adversarial and
boundary-condition tests, not only happy-path tests, given how many
consumers a single kernel defect can reach at once.

The joint governance and shared CI required by the pattern also means both
teams' access controls and both teams' supply chain security posture now
apply, in effect, to the same artifact. If one team's package registry
credentials or one team's CI pipeline is compromised, and that team has
publish rights to the kernel package, the kernel becomes a route for that
compromise to reach the other team's production systems as well, which is
a supply chain risk specific to sharing a build artifact across
organizational boundaries and does not exist for the Anticorruption Layer
alternative, where each side's build pipeline is independent.

Beyond blast radius and supply chain exposure, this pattern is otherwise
silent on data privacy, a Shared Kernel typically carries value objects and
event shapes, not data itself, and whatever privacy obligations apply to
the actual values flowing through `Money` or `ShipmentRequested` in
production are governed by each context's own data handling policy, not by
the kernel pattern itself.

## 18. References

- Eric Evans, "Domain-Driven Design. Tackling Complexity in the Heart of
  Software," Addison-Wesley, 2003, Part IV, Chapter 14, "Maintaining Model
  Integrity," section "Shared Kernel."
- Vaughn Vernon, "Implementing Domain-Driven Design," Addison-Wesley, 2013,
  Chapter 3, "Context Maps," section on Shared Kernel.
- Eric Evans, "Domain-Driven Design Reference. Definitions and Pattern
  Summaries," Domain Language, Inc., self-published, 2015, pattern summary
  for Shared Kernel.
- https://github.com/ardalis/Ardalis.SharedKernel, README description of the
  package's purpose and its relationship to the Clean Architecture Solution
  Template, verified 2026-08-02.
- https://github.com/VaughnVernon/IDDD_Samples, module `iddd_common`, the
  shared base types used across the book's separately built sample Bounded
  Contexts, verified 2026-08-02.
- https://github.com/codebeltnet/shared-kernel, project description and
  provided types (`AggregateRoot`, `Entity`, `ValueObject`, `DomainEvent`),
  published as the `Codebelt.SharedKernel` NuGet package, verified
  2026-08-02.

## Code examples

The three samples below model the same scenario, a Billing context and a
Fulfillment context, each with its own aggregate, both depending on a small
shared kernel containing a `Money` value object and a `ShipmentRequested`
domain event. Each sample is a single, self-contained file, with the kernel,
both consuming contexts, and a small runnable check all in one file, because
the pattern's defining property, that both sides import the identical code,
is clearest when shown in one compilation unit per language. C# and Kotlin
are omitted because neither toolchain was available to compile against in
this environment, and the pattern does not have a materially different shape
in either language beyond ordinary package or module syntax.

```python
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


# --- shared kernel: jointly owned by Team Billing and Team Fulfillment ---

@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if self.amount != self.amount.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        ):
            object.__setattr__(
                self, "amount", self.amount.quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            )
        if len(self.currency) != 3:
            raise ValueError("currency must be a three letter code")

    def add(self, other: "Money") -> "Money":
        if other.currency != self.currency:
            raise ValueError("cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)


@dataclass(frozen=True)
class ShipmentRequested:
    order_id: str
    ship_to_country: str
    declared_value: Money


# --- Context: Billing, owned by Team Billing ---

@dataclass
class Invoice:
    invoice_id: str
    total: Money

    def apply_late_fee(self, fee: Money) -> None:
        self.total = self.total.add(fee)


# --- Context: Fulfillment, owned by Team Fulfillment ---

@dataclass
class Shipment:
    shipment_id: str
    request: ShipmentRequested

    def customs_value(self) -> Money:
        return self.request.declared_value


def _demo() -> None:
    invoice = Invoice("INV-1", Money(Decimal("100.00"), "EUR"))
    invoice.apply_late_fee(Money(Decimal("5.00"), "EUR"))
    assert invoice.total == Money(Decimal("105.00"), "EUR")

    request = ShipmentRequested(
        order_id="ORD-1",
        ship_to_country="DE",
        declared_value=Money(Decimal("105.00"), "EUR"),
    )
    shipment = Shipment("SHIP-1", request)
    assert shipment.customs_value() == invoice.total


if __name__ == "__main__":
    _demo()
```

```go
package main

import (
	"errors"
	"fmt"
)

// --- shared kernel: jointly owned by Team Billing and Team Fulfillment ---

type Money struct {
	AmountCents int64
	Currency    string
}

func NewMoney(amountCents int64, currency string) (Money, error) {
	if len(currency) != 3 {
		return Money{}, errors.New("currency must be a three letter code")
	}
	return Money{AmountCents: amountCents, Currency: currency}, nil
}

func (m Money) Add(other Money) (Money, error) {
	if m.Currency != other.Currency {
		return Money{}, errors.New("cannot add different currencies")
	}
	return Money{AmountCents: m.AmountCents + other.AmountCents, Currency: m.Currency}, nil
}

type ShipmentRequested struct {
	OrderID       string
	ShipToCountry string
	DeclaredValue Money
}

// --- Context: Billing, owned by Team Billing ---

type Invoice struct {
	InvoiceID string
	Total     Money
}

func (i *Invoice) ApplyLateFee(fee Money) error {
	total, err := i.Total.Add(fee)
	if err != nil {
		return err
	}
	i.Total = total
	return nil
}

// --- Context: Fulfillment, owned by Team Fulfillment ---

type Shipment struct {
	ShipmentID string
	Request    ShipmentRequested
}

func (s Shipment) CustomsValue() Money {
	return s.Request.DeclaredValue
}

func main() {
	total, err := NewMoney(10000, "EUR")
	if err != nil {
		panic(err)
	}
	invoice := &Invoice{InvoiceID: "INV-1", Total: total}
	fee, err := NewMoney(500, "EUR")
	if err != nil {
		panic(err)
	}
	if err := invoice.ApplyLateFee(fee); err != nil {
		panic(err)
	}
	if invoice.Total.AmountCents != 10500 {
		panic("late fee not applied correctly")
	}

	request := ShipmentRequested{
		OrderID:       "ORD-1",
		ShipToCountry: "DE",
		DeclaredValue: invoice.Total,
	}
	shipment := Shipment{ShipmentID: "SHIP-1", Request: request}
	if shipment.CustomsValue().AmountCents != invoice.Total.AmountCents {
		panic("customs value diverged from invoice total")
	}
	fmt.Println("shared kernel demo passed")
}
```

```typescript
// --- shared kernel: jointly owned by Team Billing and Team Fulfillment ---

class Money {
  readonly amountCents: number;
  readonly currency: string;

  constructor(amountCents: number, currency: string) {
    if (currency.length !== 3) {
      throw new Error("currency must be a three letter code");
    }
    if (!Number.isInteger(amountCents)) {
      throw new Error("amountCents must be an integer");
    }
    this.amountCents = amountCents;
    this.currency = currency;
  }

  add(other: Money): Money {
    if (other.currency !== this.currency) {
      throw new Error("cannot add different currencies");
    }
    return new Money(this.amountCents + other.amountCents, this.currency);
  }

  equals(other: Money): boolean {
    return this.amountCents === other.amountCents && this.currency === other.currency;
  }
}

interface ShipmentRequested {
  readonly orderId: string;
  readonly shipToCountry: string;
  readonly declaredValue: Money;
}

// --- Context: Billing, owned by Team Billing ---

class Invoice {
  invoiceId: string;
  total: Money;

  constructor(invoiceId: string, total: Money) {
    this.invoiceId = invoiceId;
    this.total = total;
  }

  applyLateFee(fee: Money): void {
    this.total = this.total.add(fee);
  }
}

// --- Context: Fulfillment, owned by Team Fulfillment ---

class Shipment {
  shipmentId: string;
  request: ShipmentRequested;

  constructor(shipmentId: string, request: ShipmentRequested) {
    this.shipmentId = shipmentId;
    this.request = request;
  }

  customsValue(): Money {
    return this.request.declaredValue;
  }
}

function demo(): void {
  const invoice = new Invoice("INV-1", new Money(10000, "EUR"));
  invoice.applyLateFee(new Money(500, "EUR"));
  if (!invoice.total.equals(new Money(10500, "EUR"))) {
    throw new Error("late fee not applied correctly");
  }

  const request: ShipmentRequested = {
    orderId: "ORD-1",
    shipToCountry: "DE",
    declaredValue: invoice.total,
  };
  const shipment = new Shipment("SHIP-1", request);
  if (!shipment.customsValue().equals(invoice.total)) {
    throw new Error("customs value diverged from invoice total");
  }
}

demo();
```
