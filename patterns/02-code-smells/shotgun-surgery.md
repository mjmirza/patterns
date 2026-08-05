---
name: Shotgun Surgery
slug: shotgun-surgery
family: 02-code-smells
category: Coupling
aliases: []
first_described: "Fowler and Beck 1999"
maturity: canonical
related: [divergent-change, duplicate-code, feature-envy, message-chains, parallel-inheritance-hierarchies, data-clumps, move-method, move-field, inline-class, extract-class, chain-of-responsibility, strategy, observer, template-method]
incompatible_with: []
verified: 2026-08-02
---

# Shotgun Surgery

## 1. Name, aliases, and lineage

The canonical name is Shotgun Surgery. It is one of the original smells in the
"Bad Smells in Code" catalog that Kent Beck wrote for Martin Fowler's
*Refactoring. Improving the Design of Existing Code*, Addison-Wesley, 1st
edition, 1999, chapter 3. The same catalog survives, with the same name and the
same diagnosis, into the 2nd edition, Addison-Wesley, 2018, where Fowler again
credits Beck as the author of that chapter's smell list while Fowler wrote the
surrounding refactoring entries. Fowler makes the authorship split explicit on
his own site when he traces the origin of the sibling term code smell itself.
"The term was first coined by Kent Beck while helping me with my Refactoring
book" (martinfowler.com/bliki/CodeSmell.html, verified 2026-08-02).

Two independent secondary catalogs restate Fowler's definition in the same
words the primary source uses. sourcemaking.com defines it plainly. "Shotgun
Surgery refers to when a single change is made to multiple classes
simultaneously," adding that the root cause is that "a single responsibility
has been split up among a large number of classes"
(sourcemaking.com/refactoring/smells/shotgun-surgery, verified 2026-08-02).
Wikipedia's own code smell article lists it under application level smells
with the near identical wording "a single change that needs to be applied to
multiple classes at the same time" (en.wikipedia.org/wiki/Code_smell, verified
2026-08-02), though the Wikipedia page itself flags that specific sentence
with a citation needed marker rather than a direct reference to Fowler, a gap
in the tertiary literature rather than any uncertainty about the primary
source.

There is no widely attested alternate name for this smell in the way that,
say, God Class competes with Blob or Large Class. Every catalog this entry
checked, Fowler's own book, sourcemaking, and Wikipedia, uses Shotgun Surgery
as the sole label, so this entry lists no aliases rather than invent
descriptive synonyms that no source actually uses. The name is a medical
metaphor Beck chose deliberately. a shotgun blast scatters pellets across a
wide area rather than delivering one precise wound, and the surgery required
to remove every pellet means many small incisions rather than one. The
metaphor maps directly onto the smell. one conceptual change forces many small
edits scattered across the codebase rather than one edit in one place.

Shotgun Surgery is closely paired with its named opposite, Divergent Change,
in the same chapter of Fowler's book. sourcemaking's entry on that sibling
smell states the pairing directly. "Divergent Change is when many changes are
made to a single class," and identifies the two smells as opposite in shape,
one class absorbing many unrelated reasons to change against one reason to
change scattering across many classes (sourcemaking.com/refactoring/divergent-change,
verified 2026-08-02). Fowler places both smells in the book because they read
as mirror images of the same underlying problem, poor alignment between the
axis along which the code is organized and the axis along which real change
actually happens, and dimension 13 below returns to exactly how that
mirroring plays out.

## 2. Problem and context

A team ships a single logical concept, adding a new payment method, adding a
new shipping carrier, adding a new order status, renaming a field that a
dozen call sites read. Under Shotgun Surgery, that one concept does not have
one home in the code. Its rules are copied, restated, or partially duplicated
across many files, many classes, many switch statements, or many
configuration blocks, each holding its own slice of the same fact. To make the
change land correctly, an engineer has to find every one of those slices, edit
each one consistently, and verify none was missed, before the change is
correct anywhere.

The smell is most visible the moment a new case is added to an existing
family, a new enum value, a new record type, a new external integration,
because that is the moment every scattered location has to be touched at
once. A codebase with three payment methods and Shotgun Surgery does not look
broken. Nothing crashes, nothing is obviously wrong on inspection of any single
file. The cost only surfaces at the moment of change, and it surfaces as a
checklist rather than a compiler error. find the enum, find the validator,
find the fee table, find the receipt template, find the admin dropdown, find
the analytics event schema, and hope the list above is actually complete
because nothing in the language or the type system enforces that it is.

The context in which this arises is almost always organic growth rather than
deliberate design. Nobody sits down and decides to scatter the rules for
payment methods across six files. The scattering accumulates one small
addition at a time. the first payment method is added correctly inside one
class, the second is added by copying the pattern of the first into a nearby
switch statement because that felt like the smallest local change, and by the
fifth payment method the rules live in five or six places that nobody
designed together. This is why Fowler frames the smell as a signal about
misplaced responsibility rather than about any single bad decision. no single
edit that created the scattering was wrong in isolation. the accumulation is
what is wrong.

The problem is sharpest in domains with a closed but growing set of variants,
payment methods, file formats, notification channels, feature flags,
localization targets, deployment environments, because those are exactly the
places where a new case is added often enough that the coordination cost
compounds. It is comparatively mild in domains where the set of variants is
genuinely fixed and rarely touched, where the up front cost of consolidating
the logic would outweigh a coordination tax that is paid once a year rather
than once a sprint. Dimension 4 below draws that boundary in detail.

## 3. Forces

Coupling versus locality is the central tension. The scattered version has
low coupling in one narrow sense, no single class imports or depends on
another class to do its job, each switch statement stands alone and can be
read without following a reference elsewhere. But that apparent independence
is an illusion at the level that actually matters, because the classes are
coupled through a fact they all silently share, the current, complete list of
payment methods, and that coupling is invisible to the compiler and to any
static dependency graph. The consolidated version trades that invisible
coupling for a visible one, every caller now genuinely depends on one shared
definition, which is a real dependency edge a reader and a type checker can
both see.

Change frequency versus change amplitude is the second force. If the concept
being scattered changes rarely, the coordination tax is paid rarely and the
scattering may never become expensive enough to justify consolidation. If it
changes often, every addition pays the tax again, and the tax grows with the
number of scattered locations, not with the size of the change itself. Adding
one payment method is conceptually a one line change. under Shotgun Surgery
it is a six file change, and the six stays fixed or grows as the codebase
grows, so the amplitude between intended change and actual change widens over
time even as each individual edit looks small.

Consistency versus flexibility is the third force, and this is the one most
catalogs understate. Consolidating scattered logic into one place makes every
consumer of that logic behave identically by construction, which is exactly
what you want when the variants genuinely are supposed to behave the same
shape of way, present a badge color, format a receipt line, decide who gets
an email. It is exactly what you do not want when two of the scattered call
sites have a legitimate reason to diverge, when the shipping fee calculation
for international orders needs different terms than domestic ones even for
the same carrier. Consolidating without checking for that legitimate
divergence first can force artificial uniformity onto code that needed to
differ, which is why dimension 11 treats over-consolidation as a real failure
mode of the fix, not only of the smell.

Operability and how easily the scattering is discovered are the fourth
force. A newcomer reading one scattered switch statement can understand that
one file completely without opening any other, which is a genuine short term
readability win for that single file. The cost lands on the person doing the
cross cutting change, who must now discover every location before they can
trust that the change is complete, and that discovery step scales with the
number of scattered call sites and with how consistently they were named,
which in a large team is rarely perfect. Grep and IDE find usages both help,
but only if every location uses the literal same string or symbol, and by the
time a scattered concept has drifted for a year that is frequently no longer
true.

## 4. Applicability and non-applicability

Reach for the diagnosis, and for the consolidating refactorings in dimension
14, when most of the following hold. The same conceptual set (payment
methods, statuses, carriers, locales, feature flags) needs to be extended
more than roughly twice a year and each extension currently requires editing
more than two or three files. The scattered logic across those files
genuinely represents one fact stated in different forms, a fee, a label, a
color, a template key, rather than genuinely independent decisions that only
happen to share a discriminator value. A recent incident or a recent code
review caught a case where one location was updated and a sibling location
was missed, direct evidence the coordination is already failing in practice
rather than only failing in theory. The team can name, today, every location
that would need to change for the next new case, because if they cannot name
them all confidently that is itself evidence the scattering has already
outrun anyone's mental map of the codebase.

Do not reach for consolidation, and the list below is intentionally the
non-applicability list this entry's dimension calls for, when any of the
following hold. First, the variants genuinely diverge in behavior for
domain reasons rather than by accident, an international shipping fee
formula that is structurally different from a domestic one is not the same
fact restated, it is two different facts that happen to share a carrier code,
and forcing them into one shared table produces the over-consolidation
failure mode in dimension 11 rather than fixing anything. Second, the set of
variants is closed and effectively permanent, three tax jurisdictions defined
by a stable regulatory boundary that has not changed in a decade do not carry
the same amortized coordination cost as payment methods a product team adds
every quarter, and the up front cost of a Strategy or table driven
abstraction can exceed the total lifetime coordination tax it would save.
Third, the scattering is only two locations, not many, and both are trivial
to keep in sync by inspection, in which case introducing an interface, a
registry, or a lookup table adds a layer of indirection whose cost is paid
immediately while the benefit it buys is marginal. Fourth, the code is a
small script or a short lived prototype that will not survive long enough for
a second addition to ever happen, where the entire diagnosis is moot because
there is no repeated coordination cost to save. Fifth, and this is the case
teams miss most often, the apparent duplication across files is actually
Duplicate Code rather than Shotgun Surgery, meaning the same block of logic is
copied verbatim in multiple places with no discriminator value driving it at
all, in which case the correct refactoring target is Extract Function or
Pull Up Method rather than a variant registry, because there is no set of
variants to register, only one piece of logic that was copy pasted.

## 5. Structure

Shotgun Surgery is a smell, not a construct with participants you would
design in from scratch, so this dimension follows the family 02 convention of
describing the shape you recognize in code that already exists rather than a
blueprint you would draw before writing anything.

The discriminator is the single value, an enum member, a string tag, a type
name, that determines which variant of behavior applies, "ups" versus
"fedex" versus "dhl", or "pending" versus "shipped" versus "cancelled".

A scattered decision site is any function, method, or class that contains a
conditional, most often an if chain or a switch statement, keyed on the
discriminator, which returns or computes one slice of the total behavior for
that variant, a fee, a label, a validity flag, a template key.

The scattering set is the full collection of scattered decision sites that
together, but only together, describe the complete behavior of every
variant. No single site holds the whole picture. the picture only exists as
the union of every site, which is exactly what has to be reassembled by hand
on every change.

The shared but implicit contract is the fact, never written down anywhere as
code, that every scattered decision site must agree on the exact same set of
valid discriminator values. Nothing enforces this contract. it exists only in
the collective memory of whoever maintains the code, and it is precisely this
un-enforced, implicit contract that the consolidating refactoring in
dimension 14 turns into an explicit, checkable one.

## 6. ASCII structure diagram

```
BEFORE. the discriminator "ups | fedex | dhl" is known separately
by four unrelated decision sites. Nothing binds them together.

  isValidCarrier()          shippingFee()
  +------------------+      +------------------+
  | if code == ups   |      | if code == ups   |
  | if code == fedex |      | if code == fedex |
  | if code == dhl   |      | if code == dhl   |
  +------------------+      +------------------+

  carrierDisplayName()      trackingUrl()
  +------------------+      +------------------+
  | if code == ups   |      | if code == ups   |
  | if code == fedex |      | if code == fedex |
  | if code == dhl   |      | if code == dhl   |
  +------------------+      +------------------+

  Adding "usps" means editing all four boxes, correctly, in order.


AFTER. one registry is the single source of truth. Every
decision site reads from it instead of restating it.

              +---------------------------+
              |      CARRIER REGISTRY      |
              |  ups   -> {fee, name, url} |
              |  fedex -> {fee, name, url} |
              |  dhl   -> {fee, name, url} |
              +---------------------------+
                 ^        ^        ^        ^
                 |        |        |        |
        isValid  |  fee   |  name  |  url   |
                 |        |        |        |
        (reads only, never restates the set)

  Adding "usps" means adding one entry to the registry.
```

## 7. Dynamics

At edit time, the smell drives a fan out sequence rather than a call
sequence, since nothing runs at the moment the smell manifests, it is a
maintenance path, not a runtime path. An engineer receives a request to add a
new variant. They locate one decision site, often the first one they happen
to find through search, and add the new case there. They then have to
independently rediscover every other decision site, typically by grepping for
the discriminator's existing values or by following what breaks in manual
testing, and repeat the edit in each one. The process terminates only when
every site has been found and updated, and there is no signal internal to the
process that confirms termination. the engineer's confidence that they are
done is a belief, not a fact the system can check for them, unless the team
has built an explicit completeness check, which is itself rare precisely
because the scattering was never designed, only accumulated.

At review time, the same fan out repeats for whoever reviews the change. A
reviewer who does not already hold the full scattering set in memory cannot
tell, from the diff alone, whether the change is complete, because the diff
only shows what was touched, not what should have been touched but was not.
This is why Shotgun Surgery specifically defeats diff based code review in a
way that many other smells do not, a missing edit in an untouched file
produces no diff at all, so there is nothing for the reviewer to see.

At runtime, once the edit is genuinely complete and consistent, the scattered
version and the consolidated version behave identically, since the smell is
purely a maintenance time property. This matters for dimension 15,
because it means the smell cannot be detected by any runtime test that only
exercises correct, already synchronized code, it can only be caught by a test
that specifically simulates the moment of change, or by static inspection of
the source for repeated discriminator literals.

## 8. Implementation variants

The instrument used to remove Shotgun Surgery depends on what kind of thing is
scattered and how the variants differ from one another, but every variant
below shares the same underlying move. replace many places that each know a
partial fact with one place that knows the whole fact, and have every other
site read from it.

The lookup table or registry variant suits the common case where each
variant differs only in data, not in behavior, a fee number, a display
string, a URL template. This is the shape shown in the code examples below,
a `Record`, `dict`, or `map` from discriminator to a small value object. It is
the cheapest variant to introduce and the easiest to keep synchronized,
because adding a case is a single map entry rather than a new type.

The Strategy variant, in the sense the Gang of Four describe the pattern,
suits the case where variants differ in behavior, not only in data, where
`shippingFee` for one carrier genuinely needs a different calculation shape
than another, not merely a different number plugged into the same formula.
Each variant becomes its own class or function implementing a shared
interface, and a registry maps the discriminator to an instance of that
interface rather than to plain data.

The polymorphic dispatch variant replaces the discriminator entirely, where
the language and the domain allow it, by giving each variant its own class
that overrides a shared method, so the conditional disappears rather than
merely moving. This is the strongest fix when applicable, since there is no
longer a discriminator value to keep synchronized at all, only a set of
classes, and the compiler in a statically typed language enforces that every
class implements the shared interface, a stronger guarantee than any
registry can offer on its own. It is the least applicable variant when the
discriminator arrives as external, untyped data, a string from a database row
or an API payload, since something still has to map that string onto the
correct class instance, which reintroduces one single decision site, the
factory, but exactly one, not many.

The table driven configuration variant moves the scattered facts out of code
entirely into a single external file, YAML, JSON, or a database table, which
suits organizations where non engineers, product or operations staff, need
to add a new variant without a code change and a deploy. This trades a
compile time guarantee for an operational one, the file's shape has to be
validated at load time rather than checked by the compiler, and that
validation step becomes the new place a missing or malformed entry can slip
through, so it is not a strictly safer variant, only a differently governed
one.

## 9. Known production uses

Feature flag proliferation is the most extensively documented real world
instance of exactly this coordination cost, even though the literature that
documents it rarely uses the words Shotgun Surgery. Pete Hodgson, writing on
martinfowler.com, describes the underlying dynamic directly. "Feature Flags
have a tendency to multiply rapidly, particularly when first introduced. They
are useful and cheap to create and so often a lot are created," and goes on
to frame each flag as inventory carrying an ongoing cost, recommending teams
"view their Feature Toggles as inventory which comes with a carrying cost and
seek to keep that inventory as low as possible"
(martinfowler.com/articles/feature-toggles.html, verified 2026-08-02). Every
flag check scattered through a codebase is structurally identical to a
scattered decision site keyed on a discriminator, the flag's on or off state,
and removing a flag correctly means finding and removing every one of those
scattered checks, precisely the Shotgun Surgery coordination problem,
restated in the language of feature flag debt rather than in Fowler's
original vocabulary.

The August 2012 Knight Capital Group trading incident is a documented, well
sourced real world failure whose direct technical cause was an uncoordinated
change that had to land identically across multiple independent locations
and did not. According to the account published by Doug Seven, who worked
through the incident's public post-mortem material, Knight deployed new
routing code manually to eight production servers between July 27 and 31,
2012, and "one of Knight's technicians did not copy the new code to one of
the eight SMARS computer servers," with no second technician reviewing the
deployment to catch the gap (dougseven.com/2014/04/17/knightmare-a-devops-cautionary-tale/,
verified 2026-08-02). The seven correctly updated servers behaved as
intended when a new flag was activated the next trading day. the eighth
server, still carrying eight year old dormant order routing logic that
repurposed the same flag for a different, obsolete purpose, misinterpreted
the activation and began an uncontrolled trading loop, producing a loss of
roughly 460 million dollars in 45 minutes. This is not a class level code
smell in Fowler's original sense, it is a deployment level instance of the
identical structural problem, one logical change that had to be replicated
correctly across many independent locations with nothing in the system
verifying completeness, and it is cited here as the clearest publicly
documented case of what the coordination failure at the heart of Shotgun
Surgery costs when the discipline that should catch a missed location does
not exist.

Chain of Responsibility based middleware and filter architectures, the
Jakarta Servlet Filter chain being the standard specified example, exist in
large part to prevent cross cutting logic, authentication, logging,
compression, from becoming a Shotgun Surgery problem where every servlet
would otherwise need its own copy of that logic edited in lockstep. The
servlet specification defines filters as components that can be composed
into a chain and applied declaratively to any servlet without that servlet's
own code changing, the architectural answer to exactly the coordination cost
described in dimension 3, moving what would otherwise be N scattered call
sites down to one filter definition applied N times through configuration
rather than through N separate edits. This is a documented specification
level design decision rather than an incident, and it is listed here as
production use because it demonstrates the pattern of avoidance rather than
the pattern of the smell itself, exactly the relationship dimension 13
explores between this smell and the design patterns commonly used to
prevent it.

## 10. Consequences

The positive consequence of correctly diagnosing Shotgun Surgery is entirely
about what happens after the fix, covered in full in dimension 14, so this
dimension is honest that leaving the smell in place, which is what
"consequences of the smell" actually asks about, has essentially no upside.
The nearest thing to a genuine benefit of the scattered shape is that each
individual decision site stays small and locally readable in isolation, a
single switch statement of three cases is not, by itself, hard to read, and
for a codebase that genuinely never adds a fourth case that local simplicity
is real and durable, exactly why dimension 4's non-applicability list exists.

The negative consequences compound with every addition to the discriminator
set. Coordination cost rises linearly with the number of scattered decision
sites for every single change, not once but every time, so a codebase that
adds a new payment method four times a year pays the multi file coordination
tax four times a year forever, not once. Correctness risk rises because
nothing checks that the scattered sites remain consistent, so a partial
update, one site changed, a sibling site missed, produces a bug that is
often silent rather than crashing, a shipping fee that is wrong for one
carrier, a status badge that shows the wrong color, exactly the shape of
defect that survives code review because the diff never shows what was
missing. Onboarding cost rises because a new engineer cannot learn "how
payment methods work" from reading one file, they have to reconstruct the
scattering set by search, and that reconstructed mental model decays the
moment anyone forgets to update it uniformly on the next change. Test
maintenance cost rises for the identical reason, since a test suite that
verifies payment method behavior correctly also has to be updated at every
one of the same scattered sites, or the tests themselves drift out of sync
with the production code, its own instance of the same smell applied to
test code.

## 11. Failure modes and misuse

Symptom, a bug report describing behavior that is correct for most variants
of a concept and wrong for exactly one. Cause, one of the scattered decision
sites was updated when the concept last changed and a sibling site was
missed, the single most common concrete way this smell manifests as an
actual defect rather than only as maintenance friction. Fix, consolidate the
scattered sites into the registry or Strategy shape from dimension 8 before
adding the next variant, rather than patching the one missed site and
leaving the rest of the scattering in place, since patching only the symptom
guarantees the same class of bug recurs on the next addition.

Symptom, a pull request that touches six unrelated looking files for what
the ticket describes as one small feature. Cause, the feature happens to
require adding a new value to a scattered discriminator set, and each of the
six files is one of the scattered decision sites for that discriminator.
Fix, treat the size and shape of the diff as the diagnostic signal itself,
not as evidence the ticket was under scoped, and use it as the trigger to
schedule the consolidation described in dimension 14 rather than accepting
scattered six file diffs as the normal cost of doing business.

Symptom, code review repeatedly catches, or worse repeatedly fails to catch,
a missed update to one of the scattered sites. Cause, the scattering set has
grown past what any one reviewer reliably holds in memory, which typically
happens once a discriminator has more than four or five variants spread
across more than three files. Fix, the same consolidation, but this symptom
specifically signals that manual review discipline has already stopped
being a sufficient safety net, so relying on more careful review rather than
on structural consolidation is treating a structural problem as a discipline
problem.

The most common misuse of the fix itself, rather than of the smell, is
over-consolidation, forcing two variants into one shared table entry when
they actually differ for a real domain reason, described in dimension 4's
non-applicability list. Symptom, a new special case has to be bolted onto
the shared registry with an exception flag or a conditional inside what was
supposed to be uniform data. Cause, the consolidation collapsed a
distinction that mattered, treating divergent domain logic as if it were the
same restated fact. Fix, split the offending variant back out rather than
adding exception handling on top of a wrongly unified abstraction, since
piling conditionals onto a forced abstraction reproduces the readability
cost the consolidation was meant to remove, only now hidden inside one file
instead of visible across several.

A second misuse is introducing a registry or Strategy abstraction for a
discriminator with only two variants and no realistic prospect of a third,
which trades zero real coordination savings for a permanent layer of
indirection every reader now has to traverse to see what a two case
conditional would have shown directly. This is the dimension 4
non-applicability boundary manifesting as a code review finding rather than
as a design decision made in advance.

## 12. Trade-off matrix

| Force | Shotgun Surgery, unconsolidated | Registry or lookup table | Strategy pattern | Polymorphic dispatch |
|---|---|---|---|---|
| Coordination cost per new variant | High, N files touched | Low, one entry added | Low, one class added | Low, one class added |
| Runtime overhead | None | One map lookup | One map lookup plus virtual call | One virtual call, none extra |
| Type safety for missing case | None, silent gap possible | Depends on language, can validate at load | Compiler enforced in typed languages | Strongest, compiler enforced |
| Fit when variants differ only in data | Poor | Excellent | Overkill | Poor, forces classes for pure data |
| Fit when variants differ in behavior | Poor | Poor, data cannot express behavior | Excellent | Excellent |
| Fit when discriminator is external, untyped data | Neutral, matches naturally | Excellent | Good, needs a factory | Needs a factory, one decision site |
| Non engineers can add a variant | No | Yes, if externalized to config | No | No |
| Readability for a fixed, tiny variant set | Good, local and simple | Adds indirection for little gain | Adds indirection for little gain | Adds indirection for little gain |

## 13. Related and incompatible patterns

Divergent Change is this smell's named opposite in Fowler's own catalog, and
the pairing is diagnostic rather than incidental. Both describe a mismatch
between the axis a class is organized around and the axis along which real
requirements actually change, Divergent Change concentrates many unrelated
reasons to change onto one class, Shotgun Surgery spreads one reason to
change across many classes. A codebase can, and often does, exhibit both at
once on different axes, a class that already absorbs too many unrelated
responsibilities, Divergent Change, while simultaneously the specific concept
of payment methods is scattered outward from it, Shotgun Surgery, into
several sibling classes.

Duplicate Code is a frequent false positive for this smell. the surface
symptom, several files that repeat similar looking blocks, looks identical
whether the repeated block is genuinely one fact restated per variant
(Shotgun Surgery, fix with a registry or Strategy) or the same logic copy
pasted with no variant discriminator driving it at all (Duplicate Code, fix
with Extract Function or Pull Up Method). Distinguishing the two before
choosing a refactoring matters, because applying a registry style fix to
plain copy paste duplication, or applying Extract Method to genuine
per-variant behavior, produces an abstraction that fits the wrong shape of
problem.

Feature Envy and Message Chains often co-occur with Shotgun Surgery inside
the individual scattered decision sites, because a decision site that
reaches into another object's internals to decide which variant branch to
take is exhibiting Feature Envy locally even before the scattering across
files is considered, and a decision site chained through several
intermediate lookups to reach the discriminator value exhibits Message
Chains. Fixing the scattering with a registry frequently resolves the
Feature Envy at the same time, since the registry becomes the one place that
legitimately needs to know the variant's full data.

Parallel Inheritance Hierarchies is a structurally related but distinct
smell, where the scattering is not across unrelated files but across two
class hierarchies that must be extended in lockstep, subclassing one
hierarchy always forces a matching subclass in the other. It shares Shotgun
Surgery's coordination cost exactly, but its fix, described under its own
entry, generally moves the paired hierarchy's behavior into the first
hierarchy rather than into a shared registry, because the discriminator there
is a class itself, not a data value.

Chain of Responsibility, Strategy, Observer, and Template Method are the
design patterns most often used, deliberately, to prevent this smell from
forming in the first place, rather than to fix it after the fact, and
dimension 9's Servlet Filter example is Chain of Responsibility playing
exactly that preventive role. These patterns are compatible with, and often
the destination of, the refactorings in dimension 14 rather than competitors
to them.

This entry lists no incompatible patterns, because Shotgun Surgery is a smell
describing an absence of structure rather than a structure with participants
that could conflict with another pattern's participants, so there is no
pattern whose presence is definitionally blocked by this smell's presence.

## 14. Refactoring path in and out

Introducing the smell into code that does not yet have it happens, almost
always, by accident rather than by a deliberate step, so this half of the
dimension is framed as the accumulation path that produces the smell rather
than as a sequence anyone would choose. A discriminated concept starts with
exactly one variant, so there is nothing to scatter. A second variant is
added, and the smallest local diff at that moment is usually to add a second
branch to whichever conditional already exists near the first variant's
logic, rather than to design a shared abstraction for a set that, at two
members, does not yet obviously need one. This is individually reasonable.
Fowler's own point in naming the smell is that no single one of these
additions looks wrong when it happens, the wrongness is only visible in
hindsight once the third, fourth, and fifth variant have each repeated the
same locally reasonable choice in a different, unrelated file.

Removing the smell follows a fixed sequence built from Fowler's own named
refactorings. First, enumerate every scattered decision site for the
discriminator, using search on every literal value the discriminator takes,
since an incomplete enumeration at this step produces an incomplete
consolidation later. Second, choose the implementation variant from
dimension 8 that fits whether the variants differ in data, in behavior, or in
both. Third, for a registry or lookup table target, apply Move Field and Move
Method, in Fowler's 1st edition naming, or their 2nd edition renaming to Move
Function, to relocate each scattered fact into one shared structure, one
decision site at a time, keeping the codebase green after each single move
rather than moving everything at once. Fourth, once every decision site
reads from the shared structure instead of restating it, apply Inline
Function or delete the now redundant conditional bodies entirely, since a
decision site that only forwards to the shared structure with no remaining
logic of its own has completed its job and should not remain as an extra
indirection layer. Fifth, for a Strategy or polymorphic target instead,
apply Extract Class to give each variant its own type, then Replace
Conditional with Polymorphism to let the discriminator's type itself select
behavior rather than a stored string value doing so.

The refactoring is safe to run in small steps because each individual move,
one decision site relocated at a time, is independently behavior preserving
and independently testable, exactly what makes Shotgun Surgery one of the
smells most amenable to incremental fixing under a live production codebase
rather than requiring a dedicated rewrite branch.

## 15. Testing and verification

Testing code that already carries Shotgun Surgery has a specific weakness
that testing consolidated code does not, characterization tests written
against the scattered version tend to test each decision site in isolation,
one test file per scattered site, which means the test suite mirrors the
scattering rather than catching it. A test suite structured this way can be
completely green while one scattered site silently disagrees with the
others, because no single test asserts that all the sites agree with each
other, only that each site matches its own expected value independently.

Before consolidating, write one cross cutting test that specifically asserts
agreement across every scattered site for the same discriminator value,
verifying that isValidCarrier, shippingFee, carrierDisplayName, and
trackingUrl all treat "ups" consistently, before touching any of the
underlying code. This test has two jobs. it documents the current, correct
behavior as a safety net for the refactoring in dimension 14, and it becomes
a regression test that would have caught the exact class of missed-site bug
described in dimension 11, since after consolidation there is structurally
only one place left for that value to come from, so the test starts
asserting something the type system, or the map lookup, now enforces on its
own.

After consolidating into a registry or Strategy shape, testing gets
materially easier along the axis that matters, adding a new variant now
requires exactly one new test case rather than N test cases spread across N
files, and a missing entry in the registry produces a clear, immediate
failure, either a compiler error for a Strategy interface not fully
implemented, or a defined not found lookup failure for a registry, rather
than a silent behavioral gap discovered later in production. Property based
testing fits the consolidated shape well, since a property such as "every
registered carrier has a non negative fee and a non empty display name" can
be asserted once over every entry in the map, in a way that is meaningless
to state against N independent, unrelated conditional chains.

## 16. Observability signals

The smell itself produces no runtime signal, since correctly synchronized
scattered code and consolidated code behave identically once a change is
fully and correctly propagated, so observability here targets the moment of
incomplete propagation rather than the smell's steady state. Log or alert on
any code path that reaches a default, unknown, or fallback branch of a
discriminated conditional in production, since a request carrying a
discriminator value that one decision site accepts as valid while another
rejects as unknown is the direct runtime symptom of a missed scattered site,
and it is silent unless something specifically watches for it.

A static observability signal, checked at build or review time rather than
at runtime, is a linter or a small custom script that counts occurrences of
each discriminator literal across the codebase and flags any value whose
count differs from the count of its siblings, since a discriminator that
appears in five files for "ups" and only four for "dhl" is direct,
mechanical evidence of a missed site, and this kind of check is
inexpensive to write once a scattering set is identified because it needs
only string search, not semantic analysis.

Once consolidated, the healthy signal is structural rather than a metric,
the registry, table, or Strategy map has exactly as many entries as the
domain has variants, verifiable by comparing its size against an independent
source of truth, a database row count, an external API's enumeration
endpoint, or a product specification, and any drift between those two counts
is the consolidated equivalent of the missed-site bug the unconsolidated
version could produce silently.

## 17. Security and privacy implications

Shotgun Surgery carries a real, if indirect, security implication whenever
one of the scattered decision sites governs an authorization or validation
check rather than only a display or fee value. If access control logic for
a resource type is scattered across multiple entry points, an admin API, a
public API, a background job, each independently deciding whether a given
role or discriminator value is permitted, adding a new role or resource type
carries the same missed-site risk described in dimension 11, except the
silent gap this time is a permission that is enforced everywhere except one
overlooked entry point, a directly exploitable authorization bypass rather
than a cosmetic display bug. This is not a hypothetical extension of the
smell, it is the same structural mechanism dimension 11 describes, applied
to security sensitive logic instead of business logic, and it is the
strongest concrete argument for treating a scattered authorization
discriminator as a high priority consolidation target ahead of a purely
cosmetic one such as badge color.

There is no privacy implication specific to the smell itself beyond what
already applies to whatever data the scattered decision sites happen to
touch, consolidating scattered logic into one registry does not, on its own,
change what personal data is read or where it is stored, so this dimension
is deliberately brief. the smell's privacy surface is inherited entirely from
the domain data involved, not created by the scattering pattern.

## 18. References

1. Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 1st
   edition, Addison-Wesley, 1999, chapter 3, "Bad Smells in Code", the
   Shotgun Surgery entry, smell catalog credited to Kent Beck.
2. Martin Fowler, *Refactoring. Improving the Design of Existing Code*, 2nd
   edition, Addison-Wesley, 2018, chapter 3, "Bad Smells in Code".
3. sourcemaking.com, "Shotgun Surgery",
   https://sourcemaking.com/refactoring/smells/shotgun-surgery, verified
   2026-08-02.
4. sourcemaking.com, "Divergent Change",
   https://sourcemaking.com/refactoring/divergent-change, verified
   2026-08-02.
5. Wikipedia, "Code smell", Application level smells section,
   https://en.wikipedia.org/wiki/Code_smell, verified 2026-08-02.
6. Martin Fowler, "CodeSmell", https://martinfowler.com/bliki/CodeSmell.html,
   verified 2026-08-02.
7. refactoring.com, "Move Function",
   https://refactoring.com/catalog/moveFunction.html, verified 2026-08-02.
8. Pete Hodgson, "Feature Toggles (aka Feature Flags)", published on
   martinfowler.com, https://martinfowler.com/articles/feature-toggles.html,
   verified 2026-08-02.
9. Doug Seven, "Knightmare. A DevOps Cautionary Tale",
   http://dougseven.com/2014/04/17/knightmare-a-devops-cautionary-tale/,
   verified 2026-08-02.
10. Jakarta Servlet specification, Filter interface and filter chain
    composition, the mechanism the servlet standard uses to apply cross
    cutting logic declaratively rather than editing every servlet.

## Code examples

Three languages are shown, Python, TypeScript, and Go, since each shows the
same before and after shape in a class based dynamic language, a structurally
typed transpiled language, and a statically compiled language with a
different idiomatic answer, a data class, a plain interface, and a struct
plus map. Every example uses the same scenario, a shipping carrier, an order
status, or a payment method, with the discriminator's rules scattered across
several functions in the before section and consolidated into one shared
structure in the after section, and every example asserts the two versions
agree before printing anything, so the refactoring is proven behavior
preserving by the example itself, not only claimed to be.

### Python

```python
# Before. adding a new carrier means editing four separate functions,
# each holding its own copy of the same enumeration. This is the smell.
def is_valid_carrier_before(code):
    return code in ("ups", "fedex", "dhl")


def shipping_fee_before(code, weight_kg):
    if code == "ups":
        return 4.5 + weight_kg * 1.10
    if code == "fedex":
        return 5.0 + weight_kg * 1.05
    if code == "dhl":
        return 3.8 + weight_kg * 1.20
    raise ValueError(f"unknown carrier {code}")


def carrier_display_name_before(code):
    if code == "ups":
        return "UPS"
    if code == "fedex":
        return "FedEx"
    if code == "dhl":
        return "DHL"
    raise ValueError(f"unknown carrier {code}")


def tracking_url_before(code, tracking_id):
    if code == "ups":
        return f"https://www.ups.com/track?id={tracking_id}"
    if code == "fedex":
        return f"https://www.fedex.com/track?id={tracking_id}"
    if code == "dhl":
        return f"https://www.dhl.com/track?id={tracking_id}"
    raise ValueError(f"unknown carrier {code}")


# After. every fact about a carrier lives in one Carrier record.
# Adding USPS means adding one entry to CARRIERS, nowhere else.
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Carrier:
    code: str
    display_name: str
    base_fee: float
    per_kg: float
    tracking_url: Callable[[str], str]


CARRIERS = {
    "ups": Carrier("ups", "UPS", 4.5, 1.10,
                    lambda tid: f"https://www.ups.com/track?id={tid}"),
    "fedex": Carrier("fedex", "FedEx", 5.0, 1.05,
                      lambda tid: f"https://www.fedex.com/track?id={tid}"),
    "dhl": Carrier("dhl", "DHL", 3.8, 1.20,
                    lambda tid: f"https://www.dhl.com/track?id={tid}"),
}


def is_valid_carrier_after(code):
    return code in CARRIERS


def shipping_fee_after(code, weight_kg):
    c = CARRIERS[code]
    return c.base_fee + weight_kg * c.per_kg


def carrier_display_name_after(code):
    return CARRIERS[code].display_name


def tracking_url_after(code, tracking_id):
    return CARRIERS[code].tracking_url(tracking_id)


if __name__ == "__main__":
    for code in ("ups", "fedex", "dhl"):
        assert is_valid_carrier_before(code) == is_valid_carrier_after(code)
        assert shipping_fee_before(code, 2.0) == shipping_fee_after(code, 2.0)
        assert carrier_display_name_before(code) == carrier_display_name_after(code)
        assert tracking_url_before(code, "X1") == tracking_url_after(code, "X1")
    print(shipping_fee_after("fedex", 2.0), carrier_display_name_after("dhl"))
```

Run with `python3 shotgun_surgery.py`. Verified to print `7.1 DHL` on CPython
3, no dependencies required.

### TypeScript

```typescript
// Before. adding a new order status means editing four separate
// functions, each re-listing the same set of status strings.
type StatusBefore = "pending" | "paid" | "shipped" | "cancelled";

function isTerminalBefore(status: StatusBefore): boolean {
  if (status === "shipped") return true;
  if (status === "cancelled") return true;
  return false;
}

function badgeColorBefore(status: StatusBefore): string {
  if (status === "pending") return "gray";
  if (status === "paid") return "blue";
  if (status === "shipped") return "green";
  if (status === "cancelled") return "red";
  throw new Error(`unknown status ${status}`);
}

function emailTemplateBefore(status: StatusBefore): string {
  if (status === "pending") return "order-received";
  if (status === "paid") return "payment-confirmed";
  if (status === "shipped") return "shipment-sent";
  if (status === "cancelled") return "order-cancelled";
  throw new Error(`unknown status ${status}`);
}

function sortWeightBefore(status: StatusBefore): number {
  if (status === "pending") return 0;
  if (status === "paid") return 1;
  if (status === "shipped") return 2;
  if (status === "cancelled") return 3;
  throw new Error(`unknown status ${status}`);
}

// After. every fact about a status lives in one record. Adding
// "refunded" means adding one entry to STATUSES, nowhere else.
interface StatusDef {
  terminal: boolean;
  badgeColor: string;
  emailTemplate: string;
  sortWeight: number;
}

const STATUSES: Record<string, StatusDef> = {
  pending: { terminal: false, badgeColor: "gray", emailTemplate: "order-received", sortWeight: 0 },
  paid: { terminal: false, badgeColor: "blue", emailTemplate: "payment-confirmed", sortWeight: 1 },
  shipped: { terminal: true, badgeColor: "green", emailTemplate: "shipment-sent", sortWeight: 2 },
  cancelled: { terminal: true, badgeColor: "red", emailTemplate: "order-cancelled", sortWeight: 3 },
};

function lookup(status: string): StatusDef {
  const def = STATUSES[status];
  if (!def) throw new Error(`unknown status ${status}`);
  return def;
}

const isTerminalAfter = (status: string) => lookup(status).terminal;
const badgeColorAfter = (status: string) => lookup(status).badgeColor;
const emailTemplateAfter = (status: string) => lookup(status).emailTemplate;
const sortWeightAfter = (status: string) => lookup(status).sortWeight;

function main() {
  const statuses: StatusBefore[] = ["pending", "paid", "shipped", "cancelled"];
  for (const s of statuses) {
    console.assert(isTerminalBefore(s) === isTerminalAfter(s));
    console.assert(badgeColorBefore(s) === badgeColorAfter(s));
    console.assert(emailTemplateBefore(s) === emailTemplateAfter(s));
    console.assert(sortWeightBefore(s) === sortWeightAfter(s));
  }
  console.log(badgeColorAfter("shipped"), emailTemplateAfter("cancelled"));
}

main();
```

Compiled with `npx tsc --strict --target es2020 --module commonjs
shotgun_surgery.ts`, no errors, then run with `node shotgun_surgery.js`.
Verified to print `green order-cancelled` on Node under TypeScript 7.0.2.

### Go

```go
package main

import "fmt"

// Before. adding a new payment method means editing three separate
// switch statements, each holding its own copy of the method set.
func isSupportedBefore(method string) bool {
	switch method {
	case "card", "paypal", "bank_transfer":
		return true
	}
	return false
}

func feePercentBefore(method string) float64 {
	switch method {
	case "card":
		return 0.029
	case "paypal":
		return 0.034
	case "bank_transfer":
		return 0.005
	}
	panic("unknown method " + method)
}

func receiptLabelBefore(method string) string {
	switch method {
	case "card":
		return "Credit or Debit Card"
	case "paypal":
		return "PayPal"
	case "bank_transfer":
		return "Bank Transfer"
	}
	panic("unknown method " + method)
}

// After. every fact about a payment method lives in one struct.
// Adding "apple_pay" means adding one entry to methods, nowhere else.
type paymentMethod struct {
	feePercent   float64
	receiptLabel string
}

var methods = map[string]paymentMethod{
	"card":          {0.029, "Credit or Debit Card"},
	"paypal":        {0.034, "PayPal"},
	"bank_transfer": {0.005, "Bank Transfer"},
}

func isSupportedAfter(method string) bool {
	_, ok := methods[method]
	return ok
}

func feePercentAfter(method string) float64 {
	m, ok := methods[method]
	if !ok {
		panic("unknown method " + method)
	}
	return m.feePercent
}

func receiptLabelAfter(method string) string {
	m, ok := methods[method]
	if !ok {
		panic("unknown method " + method)
	}
	return m.receiptLabel
}

func main() {
	for _, m := range []string{"card", "paypal", "bank_transfer"} {
		if isSupportedBefore(m) != isSupportedAfter(m) {
			panic("mismatch")
		}
		if feePercentBefore(m) != feePercentAfter(m) {
			panic("mismatch")
		}
		if receiptLabelBefore(m) != receiptLabelAfter(m) {
			panic("mismatch")
		}
	}
	fmt.Println(feePercentAfter("paypal"), receiptLabelAfter("bank_transfer"))
}
```

Run with `go run main.go`. Verified to print `0.034 Bank Transfer` on the
locally installed Go toolchain, no dependencies required.
