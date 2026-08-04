---
name: Data Clumps
slug: data-clumps
family: 02-code-smells
category: Bloaters
aliases: [Parameter Clumps, Primitive Clumps, Shotgun Parameter List]
first_described: "Fowler, Beck, Brant, Opdyke, Roberts 1999, Refactoring, Improving the Design of Existing Code"
maturity: canonical
related: [primitive-obsession, long-parameter-list, extract-class, introduce-parameter-object, value-object, builder]
incompatible_with: []
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

The canonical name is Data Clumps. It was catalogued by Martin Fowler, Kent
Beck, John Brant, William Opdyke, and Don Roberts in the 1999 book
Refactoring, Improving the Design of Existing Code, in the chapter that lists
the twenty two named code smells the book teaches a reader to recognise
before teaching the refactorings that fix them. Fowler's own catalogue site,
maintained as the living companion to the second edition of the book, keeps
the same name and lists Introduce Parameter Object and Extract Class as the
primary cures, confirmed live at refactoring.com/catalog on 2026-08-02.

The name itself describes the shape of the problem rather than a mechanism.
A clump is a group of data items, almost always primitive types or strings,
that repeatedly appear together as a set across a codebase, as adjacent
parameters in several method signatures, as sibling fields in several
classes, or both at once. The word clump signals that the items travel
together but have never been given a name of their own, unlike a proper
Value Object or Data Transfer Object which has been deliberately extracted
and named.

No competing name has taken hold in the literature the way it has for some
other smells. Some teams informally call the parameter-list variant a
Shotgun Parameter List because a change to the group requires editing every
call site that carries it, echoing the unrelated smell Shotgun Surgery, but
that phrase is a private team habit, not a term with independent
attribution, and it is listed here only as an observed usage, not as a
sourced alias.

## 2. Problem and context

The smell shows up first in method signatures. A function that computes
whether an invoice is overdue starts by taking a single date. A second
function that computes the amount received in a period needs a start and an
end date, so it takes two. A third function that reports overdue amounts
needs the same two dates, so it repeats the pair. Nothing in the type system
records that startDate and endDate belong together. Six months later a
fourth function needs the same pair plus a third value, a grace period in
days, and the parameter list grows again, in the same order that happened to
be used the first time, because changing the order now would break every
existing call site.

The same shape recurs in class fields. A Customer class holds
addressLine1, addressLine2, city, state, postalCode, and country as six
separate string fields. A Supplier class, written by a different engineer
eighteen months later, needs an address too, and copies the same six
fields, because there was no Address type to reuse. Now a change to how a
postal code is validated, or the addition of a formatted single-line
address for shipping labels, must be made in two unrelated places, and a
third and fourth copy appear as the codebase grows, because nothing in the
code names the group as a single concept a new engineer could discover and
reuse.

The context in which the problem arises is procedural or lightly
object-oriented code where behaviour is written as free functions or thin
service methods over primitive data, rather than code organised around
domain objects that own their own invariants. It is also common in code
that grew by accretion, one parameter added at a time under deadline
pressure, where no single change felt large enough to justify stopping and
introducing a new type. The smell is therefore as much a signal about how a
codebase evolved as it is about its current state.

## 3. Forces

The pressure toward a data clump, rather than an object, is almost always
short-term velocity. Adding one more parameter to an existing function
signature is a small, local, reviewable diff. Introducing a new class,
moving several fields into it, and updating every call site is a larger
diff that touches more files and carries a higher chance of a merge
conflict on a team working in the same area concurrently. When a deadline
is close, the smaller diff wins, every time, and the clump grows by one
more field.

The pressure against a data clump, once it exists, is duplication of
behaviour and duplication of validation. If age and birthDate travel
together in five places, and only one of those five places checks that the
age is consistent with the birth date, the other four are latent bugs
waiting for the day someone edits one value without the other. Coupling is
also a real cost in the other direction from what intuition suggests.
Introducing the object initially LOOKS like it increases coupling, because
now several call sites depend on a new shared type instead of on nothing.
In fact it reduces coupling, because before the extraction each call site
was implicitly coupled to the fact that this particular ordered set of
primitives means the same thing everywhere it appears, an invisible
coupling with no compiler enforcement, and after the extraction that
coupling becomes visible and the compiler enforces it.

Cognitive load is the third force. A six-parameter method signature does
not tell a reader anything about which parameters belong together
conceptually. A signature that takes an Address object tells the reader, in
the type itself, that address is one coherent thing the function needs,
separate from whatever else it needs. The pattern favours discoverability
and type-enforced grouping over the small, local convenience of not having
to create a new file for a new class.

## 4. Applicability and non-applicability

Reach for the fix, extracting a value object or parameter object, when the
same set of two or more data items appears together in more than one
signature or more than one class, when the group has an identity of its own
in the domain language the team already uses in conversation, for example
address, date range, money, coordinates, when validation rules apply to the
group as a whole rather than to each field independently, for example a
date range where the end must not precede the start, or when the group is
likely to grow, because a bare parameter list resists growth far worse than
an object does.

Do not extract a group into an object in these cases.

The items travel together exactly once, in exactly one place. Two items
appearing side by side in a single function signature is not a clump, it is
simply that function's honest parameter list. The smell requires repetition
across at least two independent locations, per Fowler's own framing of the
smell as something you notice repeatedly, cited from
refactoring.com/catalog verified 2026-08-02.

The items are unrelated in meaning and only coincidentally adjacent, for
example a userId and a requestTimestamp that happen to be passed together
in one logging call but represent two orthogonal concerns with no shared
lifecycle or shared validation. Bundling unrelated data into one object to
satisfy a stylistic preference for fewer parameters creates a false
abstraction that is harder to reason about than the honest list it
replaced.

The language or the calling convention already gives the grouping a
first-class low-ceremony form that does the same job without a new named
type, for example a short-lived local tuple returned from a single
internal helper function that is never called from more than one place and
never crosses a module boundary. Extracting a full named class for a value
used in exactly one function body, never exposed in a public signature, is
premature ceremony, not a fix for a real clump.

The group's true home is genuinely still unclear, and creating the object
now would force a wrong abstraction that later has to be un-done. It is
sometimes correct to tolerate a clump for a short, bounded period while the
right domain concept is still being discovered, provided the team tracks it
rather than lets it silently calcify, which is the more common failure.

## 5. Structure

The smell itself has no participants in the way a design pattern does,
because it is an absence of structure rather than a structure. The
refactored state that removes the smell has three participants.

The Clumped Data Group is the set of two or more primitive or string
values that repeatedly travel together, for example startDate and endDate,
or line1, line2, city, state, postalCode, country.

The Extracted Value Object or Parameter Object is the new type created to
hold the group. It owns the fields, and it is the single place where any
invariant across the fields is enforced, for example that a DateRange's end
is never earlier than its start. Whether this new type is a true immutable
Value Object, compared by its contained values, or a mutable Data Transfer
Object used only to shorten a parameter list, is a design decision the team
makes based on whether the group represents a domain concept with its own
identity and behaviour, or merely a bundle of arguments for one call.

The Consuming Sites are every function signature, every constructor, and
every class field declaration that previously carried the individual
primitives and now carries the single extracted type instead. Each
consuming site is updated once, and every future consumer that needs the
same group takes a dependency on the extracted type rather than repeating
the primitives, which is the mechanism by which the duplication is
permanently closed off, not merely fixed at the sites that existed on the
day of the refactor.

## 6. ASCII structure diagram

```
BEFORE, the smell

  computeOverdueDays(startDate, endDate, gracePeriodDays)
  computeAmountReceived(startDate, endDate)
  computeAmountOverdue(startDate, endDate, gracePeriodDays)
                         ^         ^
                         |         |
              the same two primitives, repeated
              in three signatures, with no shared name


AFTER, the extraction

  +--------------------+
  |     DateRange      |
  |--------------------|
  | start: Date        |
  | end: Date          |
  |--------------------|
  | contains(d): bool  |
  | days(): int        |
  +--------------------+
         ^   ^   ^
         |   |   |
  +------+   |   +------+
  |          |          |
  computeOverdueDays(range, gracePeriodDays)
  computeAmountReceived(range)
  computeAmountOverdue(range, gracePeriodDays)

  each signature now depends on ONE named, validated type
  instead of on two unnamed primitives that happened to
  travel side by side
```

## 7. Dynamics

The runtime behaviour of the smell itself is unremarkable, values are simply
passed around as separate arguments, so the interesting dynamics are in how
the refactoring is carried out and in how the extracted type behaves once
introduced.

```
REFACTORING SEQUENCE (Introduce Parameter Object, applied incrementally)

1. identify the clump      . startDate, endDate appear together
                              in 3+ signatures across the codebase
2. create the new type     . class DateRange { start; end; }
3. add a NEW overload      . computeOverdueDays(DateRange, int)
                              old overload still exists, delegates to new
4. migrate ONE call site   . caller now builds a DateRange and calls
                              the new overload
5. repeat step 4           . one call site at a time, so the codebase
                              compiles and passes tests after every step
6. remove the old overload . once every call site has migrated,
                              the two-primitive signature is deleted
7. move behaviour inward   . any validation or derived computation that
                              read both primitives together, for example
                              "is this date inside the range", moves
                              from free functions into a method on the
                              new type itself, which is the point at
                              which the refactoring stops being a
                              mechanical extraction and starts producing
                              a real domain object
```

The value of step 3 through step 6, migrating incrementally behind a
temporary duplicate signature rather than changing every call site in one
commit, is that a large data clump often has dozens of call sites, and a
single atomic change across all of them is exactly the kind of large,
merge-conflict-prone diff that created the incentive to add one more
parameter at a time in the first place. The step-by-step sequence keeps
every intermediate commit in a shippable state, which is the same
discipline Fowler's own catalogue applies to every refactoring in the
book, described in the catalogue's general framing of each entry as a
sequence of small, separately-verifiable mechanical steps, verified live
at refactoring.com/catalog/introduceParameterObject.html on 2026-08-02.

## 8. Implementation variants

**Parameter Object, argument-list focused.** The new type exists purely to
shorten a signature. It may be a mutable struct or a simple record with no
behaviour beyond storing and returning its fields. This is the shallowest
variant, and the one Fowler's catalogue names Introduce Parameter Object
directly, illustrated on the catalogue page with exactly the startDate and
endDate example used above, verified live at
refactoring.com/catalog/introduceParameterObject.html on 2026-08-02.

**Value Object, domain-modelled.** The new type is immutable, compared by
value rather than by identity, validates its own invariants in its
constructor so an invalid instance can never exist, and grows methods that
express domain behaviour over the group, for example DateRange.overlaps or
Money.add. This is the deeper variant, closer in spirit to the Value Object
pattern from Eric Evans's Domain-Driven Design, and it is the correct
target when the clump represents a real domain concept rather than merely a
convenient argument bundle.

**Language-native record or data class.** Modern languages provide low
ceremony syntax that makes the extraction nearly free, which changes the
economics of the trade-off discussed in dimension 3. Java records, added in
Java 16 as a stable feature and documented as a way "to model plain data
aggregates with less ceremony than normal classes," verified live at
docs.oracle.com/en/java/javase/17/language/records.html on 2026-08-02,
generate the constructor, accessors, equals, hashCode, and toString in one
line. Python's dataclasses module, documented as providing "a decorator and
functions for automatically adding generated special methods such as
`__init__()` and `__repr__()` to user-defined classes," verified live at
docs.python.org/3/library/dataclasses.html on 2026-08-02, gives the same
low-ceremony extraction. Kotlin data classes and Swift structs offer the
equivalent. Where a language makes the extraction this cheap, there is
almost no engineering justification left for tolerating a repeated clump,
because the counter-argument that creating a class is too much overhead no
longer holds.

**Builder-mediated construction.** When the extracted group has many
optional fields, plain constructor extraction can trade a long parameter
list for a long constructor call with the same readability problem. PMD's
own rule documentation for excessive parameter counts lists the Builder
Pattern as one of several accepted mitigations alongside Parameter Objects,
verified live at docs.pmd-code.org/latest/pmd_rules_java_design.html on
2026-08-02, and this variant is common where a data clump also has several
genuinely optional members rather than a fixed required set.

## 9. Known production uses

The Stripe API's Customer, Charge, and PaymentIntent resources expose an
address object with the fields line1, line2, city, state, postal_code, and
country nested under a single address key rather than as six separate
top-level customer fields, verified live at
docs.stripe.com/api/customers/object on 2026-08-02, which shows the
address data clump treated as a first-class named object across one of the
most widely integrated payment APIs in the industry, rather than repeated
as loose fields on every resource that needs a billing or shipping
address.

Java's java.time package, introduced in Java 8 to replace the earlier
java.util.Date and Calendar design, groups the year, month, and day
primitives that had previously been passed around separately into
LocalDate, and groups a start and end instant into the Duration and
Period types, so that date arithmetic and range checks live as methods on
the grouped type rather than as free functions taking three or four loose
integers. Java records, the general-purpose mechanism for this style of
grouping in modern Java, are documented at
docs.oracle.com/en/java/javase/17/language/records.html, verified live on
2026-08-02, and are recommended by Oracle's own language guide
specifically for plain data aggregates.

PMD, the static analysis tool for Java used across a large share of the
Java open source and enterprise codebases, ships a rule named
ExcessiveParameterList in its design rule set, described as flagging that
methods with numerous parameters are a challenge to maintain and increase
the risk of bugs, and its documentation names Parameter Objects as one of
the accepted fixes, verified live at
docs.pmd-code.org/latest/pmd_rules_java_design.html on 2026-08-02. That a
mainstream static analysis tool ships a dedicated, configurable rule to
detect this exact shape, and has retained a rule for it across major
versions while deprecating an older, narrower predecessor rule named
UseObjectForClearerAPI in favour of the more general one, is itself
evidence that the smell is a recognised and actively maintained target of
automated detection in real codebases, not a purely academic concern.

## 10. Consequences

Positive consequences of fixing the smell. Validation moves to one place,
so an invariant across the group, for example that a date range's end is
not before its start, is checked once in the object's constructor rather
than inconsistently or not at all at each of several call sites. Signatures
shrink and become more self-documenting, because a parameter named range
communicates more than two parameters named startDate and endDate ever can
on their own. Behaviour that logically belongs to the group, formatting an
address as one line, computing the number of days in a range, can move
onto the new type, which is the mechanical trigger toward a richer domain
model described in Fowler's broader treatment of Feature Envy and the
Extract Class refactoring. Future growth of the group, adding a third
field to what was a pair, becomes a change in one place instead of an edit
to every call site, because new fields on an object are additive in a way
new parameters on a signature are not.

Negative consequences, honestly weighed. The fix introduces a new type,
which is a new name to learn, a new file in most language conventions, and
one more level of indirection a reader has to follow, from range.start
rather than directly from startDate. If the extraction happens too early,
before the group has proven it genuinely travels together across more than
one location, it produces a false abstraction that has to be un-done
later, which is itself extra work and extra churn. In languages without
lightweight record or data class syntax, the ceremony cost of the
extraction is real, and can tempt a team to keep tolerating the clump
specifically because the fix looks disproportionately expensive relative
to the immediate problem, which is a judgement call about the local
codebase rather than a claim that holds universally.

## 11. Failure modes and misuse

**The repeated primitive trio.** Symptom. The same three or four primitive
parameters keep appearing in new method signatures across the codebase,
always in the same relative order, and code review repeatedly approves
one more parameter changes without anyone raising it. Cause. No one has
stopped to name the group, because each individual addition looked too
small on its own to justify creating a new type, and the cost is only
visible in aggregate across many small decisions. Fix. Extract the
recurring group into a Parameter Object the next time a third or fourth
call site needs the same set, using the incremental migration sequence in
dimension 7 rather than a single disruptive rewrite.

**The desynchronised pair.** Symptom. A bug where one field of a related
pair was updated but the other was not, for example a shipping address's
city was changed but its postal code was left stale, producing a
mismatched pair that passes every individual field's own validation.
Cause. The pair or group exists in multiple independent copies across
classes, because no shared type owns both fields together, so an update
path that touches one copy has no mechanism to keep a second, unrelated
copy consistent. Fix. Consolidate the copies into a single Value Object
referenced from every location that needs it, so there is exactly one
place the fields live and exactly one update path.

**The over-eager extraction.** Symptom. A new object was introduced to
group two values, but it has no behaviour, no validation, and is used in
exactly one place, and reviewers now find that the extra file and extra
indirection make the code harder to read than the two-parameter version it
replaced. Cause. Extraction was applied reflexively as a stylistic habit
rather than in response to real repetition, which is the misuse direction
of this smell rather than the smell itself. The applicability guidance in
dimension 4 is explicit that a group appearing together exactly once is
not yet a clump. Fix. Inline the object back into its single call site, or
wait until a genuine second use appears before extracting again.

**The all-purpose bag.** Symptom. The newly extracted object grows into an
all-purpose bag that holds every field two or more otherwise unrelated
call sites happen to need, and it starts to be passed into functions that
use only two of its seven fields. Cause. The team over-corrected by
merging several distinct clumps into one type instead of recognising them
as separate concepts, which recreates coupling in a new form, now every
consumer of any one field is coupled to changes in every other field. Fix.
Split the over-broad object back into the smaller, cohesive groups it was
originally composed from, following the same recognise-then-extract
process applied a second time at finer granularity.

## 12. Trade-off matrix

| Force | Data Clump (unfixed) | Introduce Parameter Object | Extract Class (fields, with methods) | Builder |
|---|---|---|---|---|
| Signature readability | low, unnamed grouping | high, one named argument | high, and improves further as behaviour moves in | medium, readable at the call site but adds a construction step |
| Validation consistency | none enforced across the group | enforced once, in the object's constructor | enforced once, plus behaviour co-located | enforced once, at build time |
| Ceremony to introduce | none | low in most modern languages, near zero with records or data classes | medium, requires deciding what behaviour moves in | higher, requires a builder type alongside the object |
| Fit for many optional fields | poor, positional parameters get error-prone | poor, still one required shape | poor unless combined with a builder | strong, this is its specific purpose |
| Risk of premature abstraction | none, nothing was extracted | moderate if applied on a single-use group | higher, because Extract Class also invites adding behaviour that may not belong yet | moderate, adds structure for optionality that may not be needed |
| Coupling across call sites | high and invisible, implicit shared meaning with no compiler check | lower and visible, enforced by the type system | lowest, because both data and its rules live in one place | low, similar to Parameter Object once built |

## 13. Related and incompatible patterns

Data Clumps is closely related to Primitive Obsession, catalogued in the
same book, which is the broader smell of using raw primitive types where a
small domain type would be clearer, of which a repeated group of
primitives is one specific, highly recognisable case. It is also related
to Long Parameter List, a separate named smell in the same catalogue that
describes signatures that have grown too large regardless of whether the
excess parameters form a recognisable repeated group, and the two often
co-occur because the most common cause of a signature growing long is
exactly a data clump being added to one parameter at a time rather than as
a single object.

The primary composing pattern for the fix is Introduce Parameter Object,
which produces a shallow grouping type, and Extract Class, which produces
a richer type that also owns behaviour previously scattered as free
functions operating on the loose primitives. Value Object, from Eric
Evans's Domain-Driven Design vocabulary, describes the mature end state the
extracted type should aim for when the group represents a true domain
concept, immutable, compared by value, self-validating. Builder composes
with the fix rather than replacing it, when the extracted type has many
optional members, per dimension 12.

There is no pattern that is incompatible with fixing a data clump in the
sense of actively conflicting with it. The closest thing to an
incompatible force is a team or codebase convention that deliberately
favours flat, positional data over nested objects for a specific reason,
for example a wire format or a hot path where allocation of a new object
per call carries a measurable cost the team has profiled and decided to
avoid, in which case the clump is knowingly tolerated as a documented
trade-off rather than fixed, which is a legitimate and different outcome
from simply never noticing the clump existed.

## 14. Refactoring path in and out

Refactoring in, from a live data clump to a clean type, follows the
incremental sequence given in full in dimension 7. Identify the recurring
group across at least two call sites, create the new type behind a new
overload or a new constructor, migrate one caller at a time so the
codebase stays green throughout, remove the old signature once every
caller has moved, then move any validation or derived behaviour that read
the group together into methods on the new type itself. This last step is
the one most teams skip, stopping at a plain data-holding record and
leaving the logic that operates on it as free functions elsewhere, which
captures the signature-shortening benefit but leaves the
validation-consistency benefit from dimension 10 unclaimed.

Refactoring out, removing an extracted type that has stopped earning its
place, applies when the type has drifted to a single remaining consumer,
per the misuse case in dimension 11, or when the language's later
addition of a native lightweight construct, for example a language
gaining tuple destructuring or named parameters, has removed the original
justification for a heavyweight class. The reverse path is Inline Class,
the mirror refactoring to Extract Class in Fowler's catalogue, applied by
moving the extracted type's fields and any remaining behaviour back onto
the single consuming site, then deleting the now-empty type.

## 15. Testing and verification

Judgement heavy dimension. Once the group is extracted into its own type,
the invariants that used to be untested or inconsistently tested across
several call sites become directly and cheaply unit testable on the type
itself, in isolation from any of its consumers, for example a single test
suite for DateRange that asserts end must not precede start, independent
of every function that happens to accept a DateRange. This is a genuine
gain in test surface area per unit of test-writing effort, because one
focused test file replaces what would otherwise be the same invariant
re-verified, or more commonly not verified at all, inside every consuming
function's own tests.

What becomes harder to test is any code that constructs the object across
a serialization boundary, for example deserializing an Address from JSON,
where the previous flat-field version might have tolerated a missing field
by defaulting it silently at each of several call sites, and the new
constructor-validated version now fails fast at construction time in a
single place. This is usually the correct behaviour, failing fast rather
than silently, but it does mean any existing tests that relied on lenient
per-call-site handling of missing fields need to be rewritten against the
new, stricter construction path, and that migration cost should be
budgeted for rather than discovered mid-refactor.

## 16. Observability signals

Judgement heavy dimension. The smell itself produces no runtime signal to
monitor, it is a static code shape rather than a runtime behaviour, so
observability here is about the process of detecting and tracking it
rather than about a production dashboard. A static analysis rule such as
PMD's ExcessiveParameterList, described in dimension 9, run as part of a
continuous integration lint step, is the most direct detection signal, and
teams that want a repeatable early warning should configure that class of
rule with an explicit parameter-count threshold rather than relying on
reviewers to notice repetition by eye across files that a single reviewer
may never see side by side.

Once fixed, a healthy signal is a shrinking count of raw primitive
parameters per public method over time in the same lint report, tracked as
a trend rather than a single snapshot, since the point of the fix is
prevention of recurrence, not a one-time cleanup. An unhealthy signal is
the opposite trend, or a pattern where the same extracted type keeps
growing new optional fields long after its initial extraction, which is
the early sign of the over-broad-object misuse case described in
dimension 11.

## 17. Security and privacy implications

Judgement heavy dimension. Where the clumped data includes personally
identifiable information, an address, a full name split into given and
family name fields, a payment card's expiry month and year, consolidating
the group into a single named type creates one place to apply data
protection controls, field-level encryption, redaction in logs, or access
auditing, rather than needing to apply the same control independently at
every scattered call site that happened to carry the same primitives.
Stripe's own address object, cited in dimension 9, is a concrete instance
of exactly this pattern applied to sensitive billing data, where the
grouping makes it tractable to reason about and control access to the
whole address as one unit rather than as six independently flowing
strings.

In the reverse direction, leaving the clump unfixed increases the risk
that a data protection control is applied to some of the scattered copies
and missed on others, for example a log-scrubbing rule that redacts an
address object by type but cannot catch six anonymous string parameters
named line1 through country scattered across a dozen unrelated function
signatures with no common type signature to match against. Where the
pattern is silent is on any concern beyond this consolidation benefit,
extracting a clump into an object introduces no new attack surface of its
own, it neither adds nor removes an authentication or authorization
boundary, and any security property the fix appears to add is really a
consequence of having a single enforceable place for a rule that
previously had none.

## Code examples

Three languages where the fix is genuinely idiomatic in a different way.
TypeScript and Python both show the domain-modelled Value Object variant from
dimension 8, self-validating in its constructor. Go is used in place of Java
here because Java's runtime could not be executed in the environment this
entry was verified in, see the note at the end of this section. All three
examples below were compiled or run and their output is shown.

### TypeScript

```typescript
class DateRange {
  constructor(readonly start: Date, readonly end: Date) {
    if (end.getTime() < start.getTime()) {
      throw new Error("end before start");
    }
  }

  days(): number {
    const ms = this.end.getTime() - this.start.getTime();
    return Math.round(ms / (1000 * 60 * 60 * 24));
  }

  contains(d: Date): boolean {
    return d.getTime() >= this.start.getTime() && d.getTime() <= this.end.getTime();
  }
}

function computeOverdueDays(range: DateRange, gracePeriodDays: number): number {
  return Math.max(0, range.days() - gracePeriodDays);
}

const range = new DateRange(new Date("2026-01-01"), new Date("2026-02-15"));
console.log("days=", range.days());
console.log("overdue=", computeOverdueDays(range, 30));
console.log("contains=", range.contains(new Date("2026-01-20")));
try {
  new DateRange(new Date("2026-02-01"), new Date("2026-01-01"));
} catch (e) {
  console.log("rejected:", (e as Error).message);
}
```

Run with `tsc date_range.ts --target es2020` then `node date_range.js`.
Output.

```
days= 45
overdue= 15
contains= true
rejected: end before start
```

Before this refactoring, computeOverdueDays took a bare startDate and
endDate, each of type Date, and any of the three functions in dimension 6's
diagram could receive an end before a start with no error until the
arithmetic silently produced a negative day count. The constructor above is
the single place that invariant is now enforced.

### Python

```python
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DateRange:
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError("end before start")

    def days(self) -> int:
        return (self.end - self.start).days

    def contains(self, d: date) -> bool:
        return self.start <= d <= self.end


def compute_overdue_days(rng: DateRange, grace_period_days: int) -> int:
    return max(0, rng.days() - grace_period_days)


if __name__ == "__main__":
    rng = DateRange(date(2026, 1, 1), date(2026, 2, 15))
    print("days=", rng.days())
    print("overdue=", compute_overdue_days(rng, 30))
    print("contains=", rng.contains(date(2026, 1, 20)))
    try:
        DateRange(date(2026, 2, 1), date(2026, 1, 1))
    except ValueError as e:
        print("rejected:", e)
```

Run with `python3 date_range.py`. Output.

```
days= 45
overdue= 15
contains= True
rejected: end before start
```

The `@dataclass(frozen=True)` decorator is the Python instance of the
language-native record variant from dimension 8, and `__post_init__` is where
the cross-field invariant that a bare pair of date arguments could never
express is enforced, once, for every caller.

### Go

```go
package main

import (
	"errors"
	"fmt"
	"time"
)

type DateRange struct {
	Start time.Time
	End   time.Time
}

func NewDateRange(start, end time.Time) (DateRange, error) {
	if end.Before(start) {
		return DateRange{}, errors.New("end before start")
	}
	return DateRange{Start: start, End: end}, nil
}

func (r DateRange) Days() int {
	return int(r.End.Sub(r.Start).Hours() / 24)
}

func (r DateRange) Contains(d time.Time) bool {
	return !d.Before(r.Start) && !d.After(r.End)
}

func ComputeOverdueDays(r DateRange, gracePeriodDays int) int {
	overdue := r.Days() - gracePeriodDays
	if overdue < 0 {
		return 0
	}
	return overdue
}

func main() {
	start, _ := time.Parse("2006-01-02", "2026-01-01")
	end, _ := time.Parse("2006-01-02", "2026-02-15")
	rng, err := NewDateRange(start, end)
	if err != nil {
		panic(err)
	}
	fmt.Println("days=", rng.Days())
	fmt.Println("overdue=", ComputeOverdueDays(rng, 30))
	mid, _ := time.Parse("2006-01-02", "2026-01-20")
	fmt.Println("contains=", rng.Contains(mid))
	_, err = NewDateRange(end, start)
	fmt.Println("rejected:", err)
}
```

Run with `go run date_range.go`. Output.

```
days= 45
overdue= 15
contains= true
rejected: end before start
```

Go has no exceptions and no constructor enforcement, so `NewDateRange`
returns an error value rather than throwing, which is the idiomatic Go shape
for the same self-validating Value Object described in dimension 8. A plain
`DateRange{Start: end, End: start}` struct literal would still bypass the
check, which is why the type's zero-value constructor is unexported by
convention in real Go codebases that use this shape, and callers are steered
toward `NewDateRange`.

Java was not compiled for this entry. A `record DateRange(LocalDate start,
LocalDate end)` with a compact canonical constructor throwing
IllegalArgumentException on an invalid range is the idiomatic Java 16-plus
equivalent of the three examples above, and it was written and reviewed for
correctness, but `java` and `javac` in this environment reported no Java
Runtime available, so the claim that it compiles is not made here.

## 18. References

Fowler, Martin, Kent Beck, John Brant, William Opdyke, Don Roberts.
Refactoring, Improving the Design of Existing Code. Addison-Wesley, 1999.
Chapter 3, Bad Smells in Code, the Data Clumps entry.

Fowler, Martin. Refactoring catalog, Introduce Parameter Object.
https://refactoring.com/catalog/introduceParameterObject.html, verified
2026-08-02.

Fowler, Martin. Refactoring catalog, full listing.
https://refactoring.com/catalog/, verified 2026-08-02.

Fowler, Martin. RefactoringMalapropism.
https://martinfowler.com/bliki/RefactoringMalapropism.html, verified
2026-08-02, used to confirm the precise, narrow definition of refactoring
Fowler applies throughout the catalogue that this entry's dimension 7
relies on.

Stripe. Customers API reference, the address object.
https://docs.stripe.com/api/customers/object, verified 2026-08-02.

Oracle. The Java Language Specification companion guide, Record Classes.
https://docs.oracle.com/en/java/javase/17/language/records.html, verified
2026-08-02.

Python Software Foundation. dataclasses, Data Classes.
https://docs.python.org/3/library/dataclasses.html, verified 2026-08-02.

PMD. Java Design rules, ExcessiveParameterList and UseObjectForClearerAPI.
https://docs.pmd-code.org/latest/pmd_rules_java_design.html, verified
2026-08-02.

Evans, Eric. Domain-Driven Design, Tackling Complexity in the Heart of
Software. Addison-Wesley, 2003. Chapter 5, on Value Objects, used as the
sourced attribution for the domain-modelled variant described in
dimension 8 and the maturity target described in dimension 13.
