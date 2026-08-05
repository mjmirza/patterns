---
name: Repeated Switches
slug: repeated-switches
family: 02-code-smells
category: Object-Orientation Abusers
aliases: [Scattered Switches, Duplicated Type Switches, Parallel Switch Statements]
first_described: "Fowler 2018, Refactoring, Improving the Design of Existing Code, second edition, renamed and re-scoped from the 1999 first edition smell Switch Statements"
maturity: canonical
related: [switch-statements, factory-method, primitive-obsession, shotgun-surgery, divergent-change, data-clumps]
incompatible_with: []
verified: 2026-08-05
---

# Repeated Switches

## 1. Name, aliases, and lineage

The canonical name used in this entry is Repeated Switches. It names a
specific and narrower situation than its older sibling entry in this
repository, Switch Statements, and the difference between the two is the
whole point of treating them as two separate smells rather than one.

The 1999 first edition of Martin Fowler's book, written with Kent Beck, John
Brant, William Opdyke, and Don Roberts, catalogued a smell called Switch
Statements. Its complaint was about a single switch, or a chain of `if` and
`instanceof` checks doing the same job, that dispatches on a type code inside
one method. The fix offered there, Replace Conditional with Polymorphism, is
documented on Fowler's own maintained catalog with a worked example of bird
species and plumage, at
https://refactoring.com/catalog/replaceConditionalWithPolymorphism.html,
verified 2026-08-05.

The 2018 second edition of the same book restructured its smell catalogue and
narrowed the Switch Statements entry into a case that specifically concerns
one switch appearing once, while introducing Repeated Switches for a
different and, in production experience, more damaging shape. the same set
of case labels, over the same underlying type code, written out again in
more than one place in the code. A single switch on an order status inside
one billing function is Switch Statements. The exact same set of order
statuses, in the same order, checked separately inside a shipping function,
a reporting function, and a notification function, four times over, is
Repeated Switches. This entry's authors were not able to independently
confirm the precise chapter number and the exact wording of the second
edition's restatement against a live web source at the time of writing, only
the well documented existence of the restructuring itself and the strong
match between the description carried forward from the first edition, "the
same switch statement scattered about a program in different places, use
polymorphism", against a public course summary of the first edition's smell
list at https://github.com/HugoMatilla/Refactoring-Summary, verified
2026-08-05. That summary's own wording for the older, single entry already
describes the scattered case exactly, which is consistent with the second
edition later giving that specific shape its own name. This attribution
detail is flagged here rather than smoothed over, in keeping with the
honesty rule this repository applies to every claim a reader might check.

Practitioners refer to the same shape under a handful of working names.
Scattered Switches emphasizes the geography of the problem, the cases are
spread across files rather than concentrated in one. Duplicated Type
Switches emphasizes that the duplication is not of arbitrary code but
specifically of a discriminant and its enumeration. Parallel Switch
Statements is the phrase used most often in code review comments, because
the switches usually run down the same list of cases in the same order,
side by side, as if drawn from a shared template that nobody wrote down.

This repository groups Repeated Switches under Object-Orientation Abusers,
the same category label used for its sibling Switch Statements and for
Refused Bequest and Alternative Classes with Different Interfaces elsewhere
in this family. As those entries note, that category grouping is a widely
used secondary teaching convention rather than a direct quotation from
either edition of the book, and it is repeated here on the same honesty
basis, as engineering categorization rather than a sourced claim.

A short test separates this smell from its sibling and recurs through every
dimension below. Count the number of distinct places in the code, files,
methods, or modules, where a conditional keyed on the same discriminant
appears. One place is the older Switch Statements smell, or possibly no
smell at all, see dimension 4. Two or more places, where the set of cases
has to stay in lockstep across all of them by hand, is Repeated Switches.

## 2. Problem and context

A codebase accumulates a type code, an enum, a string discriminant, or a
`kind` field on a tagged union, that represents a small closed family of
variants a business actually cares about. Payment method. Order status.
Shape kind. Subscription tier. Node kind in a parser. Early on there is one
switch over that discriminant, in one function, and it is easy to read.

The pressure that creates Repeated Switches is ordinary and comes from
outside the code. A second concern arrives that needs to know the same
variant to make its own decision. Billing already switches on payment method
to compute a processing fee. Now the checkout page needs a display label per
payment method, so a second switch appears, written fast, by copying the
case labels from the first one because they are right there and correct.
Then a settlement report needs the number of business days each method
takes to clear, and a third switch appears the same way. Nobody sat down and
decided to duplicate a decision four times. Four different people, on four
different days, each made a small, locally reasonable choice, to switch on
the value they already had rather than to ask whether a decision surface
already existed somewhere else for it.

The felt symptom in review is that the code reads fine, function by
function. Each switch is short, each case obviously correct in isolation.
The smell only shows up when a fifth variant is added, a new payment method,
a new order status, a new shape, and the person adding it finds one switch
by searching for the enum's declaration, edits it, ships, and has no
mechanical way of knowing that three other switches elsewhere also need the
new case, because nothing links them together beyond a value they happen to
share. This is the same failure mode traditionally described for Shotgun
Surgery, one abstract change forcing edits in many places, except the
duplication runs through the shape of a decision rather than through a block
of duplicated statements, which is why Duplicate Code detectors and
copy-paste linters usually miss it entirely, and why plain code review misses
it too unless the reviewer happens to remember every other switch on the
same discriminant.

The context in which this becomes a real problem, not a stylistic quibble,
has three ingredients present at once. The discriminant is open, meaning new
variants are added over the product's life, not a fixed and permanently
closed set. The decisions keyed on it are spread across genuinely different
concerns, billing, display, settlement, rather than living in one obviously
cohesive module. And the team is more than one person, or the same person
returning to the code after enough time has passed to have forgotten where
every switch lives. Remove any one of those three and the smell either
cannot occur, an enum that never grows a new case cannot be forgotten
somewhere, or it stops mattering in practice, one developer holding the
whole small codebase in their head will notice the third switch by
recollection rather than by tooling.

## 3. Forces

Consistency across the codebase competes directly against locality of
change. Consolidating every decision keyed on a discriminant into a single
authoritative place, a class hierarchy, a lookup table, a factory, makes
consistency mechanical, adding a case in one spot is the only way to add it
at all. The cost is that the single place must now know about every
concern that reads the discriminant, billing, display, settlement, which
can pull unrelated responsibilities into one artifact and make that
artifact large and change prone for reasons that have nothing to do with
each other. A change to how settlement days are computed should not, ideally,
require touching the same file that governs the display label, yet
consolidating everything into one polymorphic hierarchy by class often does
exactly that, because the hierarchy's shape is fixed at the level of the
discriminant, not at the level of each concern.

Coupling direction is the second force. Where the underlying type is owned
by the same team and can be extended freely, polymorphism can be pushed onto
the type itself, adding a virtual method per concern. Where the type is
owned elsewhere, a value from a third party library, a database row shape, a
wire format the team does not control, polymorphism on the type is not
available, and the resolution has to live in code the calling team owns,
which pulls toward the Visitor pattern or an external dispatch table
instead, at the cost of an extra layer of indirection every reader has to
learn.

Compile time safety competes against runtime flexibility. A closed,
compiler enforced discriminant, a sealed hierarchy in Kotlin or Java, a
discriminated union in TypeScript, an enum matched exhaustively in Rust or
Swift, buys a guarantee that every site handling the discriminant is
revisited, forcibly, the moment a new variant is added, because the build
fails until it is. That guarantee is only available in languages with sum
types or sealed hierarchies and exhaustiveness checking, so in a language
without that feature, Go and older JavaScript both lack it, the same safety
has to be re-created by hand, through a single lookup table or a lint rule,
and the discipline required to keep it that way is a social force, not a
mechanical one.

Cost of change over the life of the discriminant is the last force worth
naming plainly. A discriminant that adds one new variant a decade does not
justify the design and review overhead of a full polymorphic consolidation.
A discriminant that grows every quarter, because the business keeps adding
payment providers or shipping carriers, earns that overhead back quickly,
because every missed site is a production incident waiting for the next
release. Repeated Switches favors long lived, frequently extended
discriminants and is close to a non issue for a discriminant that is
effectively frozen.

## 4. Applicability and non-applicability

Reach for a fix to this smell when the same discriminant is matched, by
value, in three or more places across the codebase, and at least one of
those places was demonstrably missed at least once when a new case was
added, whether that miss showed up as a bug report, a silent fallthrough, or
a reviewer catching it by memory rather than by tooling. It also applies
proactively, before any miss has happened yet, when a second independent
switch on the same discriminant is about to be added and the author can see
that a third is coming, because a growing family of concerns is clearly
going to want the same decision.

It applies with particular force when the discriminant is genuinely open,
new payment providers, new integrations, new document types, arriving on a
cadence the team does not fully control, because every new case is a fresh
opportunity to miss a site.

The non-applicability list matters more here than the applicability list,
and skipping it is the most common way this smell gets over-corrected into
something worse than the original duplication.

Do not apply a fix when the discriminant is genuinely and permanently
closed, three shipping methods that will never change because they are
fixed by a physical carrier contract, and every place that switches on it
does something different enough that a shared abstraction would have to
grow an interface method for each concern anyway, at which point the
supposed consolidation is a thin wrapper around the same switch, moved, not
removed. A short, stable, low change frequency discriminant with two
switches on it is not worth the design cost of a hierarchy.

Do not apply it when the branches do not actually share a shape. If one
switch returns a number, one triggers a side effect with different
argument counts per case, and one exists purely to log, forcing all three
into one polymorphic interface produces an interface with three unrelated
methods bolted onto every variant class, which pushes unrelated concerns
into the same file for no consistency benefit, the opposite of what the
fix is supposed to buy.

Do not apply it across a module boundary the team does not own on both
sides. If one of the repeated switches lives in a public library and
another lives in a downstream consumer, consolidating them into a shared
polymorphic hierarchy requires the downstream team to extend a type it does
not own, which is not possible in most closed class hierarchies, and forces
either the Visitor pattern with its own added complexity, or acceptance
that the duplication crossing that boundary is structural, not
accidental, and should be guarded rather than eliminated, see dimension 14.

Do not apply it to a discriminant with only two variants and no growth in
sight, a boolean disguised as an enum. The overhead of any of the
consolidation strategies below outweighs the risk of forgetting a case when
there is, in practice, only ever one other case to forget.

## 5. Structure

The smell itself has no participants in the sense a design pattern does,
it is an absence of structure, several independent call sites each holding
their own private copy of a decision. The structure below describes the
target shape after the primary fix, Replace Conditional with Polymorphism
consolidated across concerns, which this entry treats as the default
remediation and contrasts against the guard-only remediation in dimension 14.

Discriminant. The original value the switches all match on, a payment
method kind, an order status, a node kind. After the fix it typically
survives only as the runtime type tag implicit in which concrete class is
present, or as a lookup key into a single table, never as a value inspected
directly by more than one piece of calling code.

Decision Surface. The single artifact, an interface or an abstract base, that
declares one method per concern that used to be a separate switch. Fee
calculation, display name, settlement days, each becomes a method on this
surface rather than a case in three switches.

Variant Implementations. One concrete class, or one table row, per value the
discriminant used to take. Each implementation supplies its own answer for
every method on the Decision Surface, replacing its slice of every switch
at once.

Consumers. The billing code, the checkout page, the settlement report. After
the fix each consumer asks the Decision Surface for the answer it needs,
`method.feeCents(amount)`, rather than re-deriving the answer from the raw
discriminant.

Where polymorphism cannot be pushed onto the type itself, because the type
is owned elsewhere, the same four roles are re-expressed with a Visitor in
place of the Decision Surface, and each Visitor implementation plays the role
Variant Implementations play above, still consolidating what used to be N
scattered switches into one place, the Visitor's dispatch, even though the
underlying type never gains a virtual method.

## 6. ASCII structure diagram

```
BEFORE, the smell
                     +------------------+
   PaymentMethod --->|  billing.ts      |--- switch(method.kind) { ... }
        (kind)       +------------------+
                     +------------------+
                --->|  checkout.ts     |--- switch(method.kind) { ... }
                     +------------------+
                     +------------------+
                --->|  settlement.ts   |--- switch(method.kind) { ... }
                     +------------------+
   three independent switches, same case labels, no shared source of truth


AFTER, consolidated by polymorphism
   +-----------------------+
   |  PaymentRules         |  <-- Decision Surface (interface)
   |  feeCents()           |
   |  displayName()        |
   |  settlementDays()     |
   +-----------+-----------+
               ^
        implements
   +-----------+-----------+---------------------+
   |CreditCardRules        |PayPalRules           |BankTransferRules
   |feeCents() -> 2.9%+30c |feeCents() -> 3.4%+49c|feeCents() -> 0
   +-----------------------+-----------------------+---------------------+

   billing.ts, checkout.ts, settlement.ts all call rulesFor(method).X()
   one factory, rulesFor(), is the single place the discriminant is read
```

## 7. Dynamics

The dynamics of the smell are best understood as an event over time rather
than a single execution trace, because the defect only appears at the moment
a new variant is introduced, not while the existing variants run correctly.

```
t0  discriminant PaymentMethod has 2 variants, creditCard and payPal
    billing.ts switches on it, correct
t1  a second concern needs the discriminant
    checkout.ts adds its own switch, copies the 2 case labels, correct
t2  a third concern needs the discriminant
    settlement.ts adds its own switch, copies the 2 case labels, correct
t3  product adds a third variant, bankTransfer
    developer opens billing.ts, the file they were told to change, adds
    the bankTransfer case there, ships
    checkout.ts and settlement.ts are not touched, because nothing in the
    code links them to billing.ts or to each other
t4  a bankTransfer order reaches checkout.ts at runtime
    the switch has no bankTransfer case
    depending on the language this either throws, falls through to a
    default that silently returns the wrong value, or, in TypeScript
    without exhaustiveness checking enabled, compiles cleanly and returns
    undefined at runtime
    the failure surfaces in production, on the bankTransfer path only,
    which is exactly the path least likely to have been exercised in the
    manual test pass that shipped t3
```

After the fix, the same timeline collapses `t3` into one edit at the single
Decision Surface, and the compiler, or the exhaustiveness lint, refuses to
build until every method on that surface has a bankTransfer implementation,
so the failure at `t4` cannot occur, it is caught at the moment of the `t3`
edit instead, before shipping.

## 8. Implementation variants

Consolidate by class hierarchy. Give the discriminant's type a virtual
method per concern and one subclass per variant, the classic Replace
Conditional with Polymorphism shape documented on
https://refactoring.com/catalog/replaceConditionalWithPolymorphism.html,
verified 2026-08-05. Best fit when the team owns the type, the number of
concerns is small and stable, and the variants themselves carry real state,
a credit card's last four digits, a bank transfer's IBAN, that naturally
belongs on a per-variant object.

Consolidate by external Visitor. When the type cannot be extended, because
it comes from a third party library or has to stay a plain data shape for
serialization, move the per-concern dispatch into a Visitor that the type
accepts rather than a method the type owns. This is the variant used inside
compilers and language tooling, where the AST node types are shared across
many independent passes and none of those passes is allowed to add a method
to the node classes themselves. LLVM's `InstVisitor` template exists for
exactly this reason, and its own header comment states the trade plainly,
"Instruction visitors are used when you want to perform different actions
for different kinds of instructions without having to use lots of casts and
a big switch statement", with the added note that the template avoids the
virtual call overhead an interface based Decision Surface would pay, source
https://llvm.org/doxygen/InstVisitor_8h_source.html, verified 2026-08-05.

Consolidate by lookup table. In languages without cheap inheritance, or where
the per-variant behaviour is pure data plus small functions rather than
rich stateful objects, a single map or dictionary keyed by the discriminant,
each entry holding the small set of functions or values every concern
needs, achieves the same one-place-to-edit property without a class
hierarchy at all. This is the idiomatic shape in Go, which has no
inheritance and where struct embedding does not give the compiler
enforcement a sealed hierarchy would, demonstrated directly in the Go
sample under the code examples heading below.

Guard rather than eliminate, with sealed types and exhaustive matching.
Where consolidating every concern into one artifact would wrongly couple
unrelated code, the alternative is to leave the switches where they are but
make it structurally impossible to add a variant without the compiler
flagging every site. TypeScript achieves this with a discriminated union and
a `never`-typed exhaustiveness check in each switch's default branch, so
that adding a new union member produces a compile error at every switch that
has not been updated, described with the worked bird and shape examples at
https://www.typescriptlang.org/docs/handbook/2/narrowing.html, verified
2026-08-05. Java achieves the same guarantee natively as of JEP 441 by
combining a `sealed` interface with pattern matching for `switch`, where the
compiler rejects a switch over a sealed type unless every permitted subtype,
or a default, is present, illustrated with the `Shape`, `Rectangle`, and
`Circle` example on
https://docs.oracle.com/en/java/javase/21/language/pattern-matching-switch.html,
verified 2026-08-05. Rust and Swift both enforce the same property natively
for any `enum` matched with `match` or `switch` respectively, without an
opt-in feature. This variant is the correct choice whenever the
non-applicability reasons in dimension 4 rule out true consolidation, it
keeps the duplication but removes the danger.

## 9. Known production uses

LLVM's `InstVisitor<T>` class template is the compiler construction
community's standard answer to exactly this smell, applied to instruction
opcodes rather than a business enum. Its own source comment frames the
motivation as avoiding "lots of casts and a big switch statement" repeated
across the many independent optimisation and analysis passes that all need
to inspect the same instruction kinds, source
https://llvm.org/doxygen/InstVisitor_8h_source.html, verified 2026-08-05.
Every LLVM pass that needs per-opcode behaviour subclasses this visitor
instead of writing a fresh switch over `Instruction::getOpcode()`, which is
the consolidate-by-external-visitor variant from dimension 8 applied at
industrial scale, because no individual pass is permitted to add a virtual
method to the shared `Instruction` class hierarchy.

The Java language itself, from JDK 21 onward, treats the guard variant of
this fix as important enough to add as a core language feature rather than
leave to convention. JEP 441, "Pattern Matching for switch", finalized
pattern matching in `switch` specifically so that a `switch` over a
`sealed` type is checked for exhaustiveness by the compiler, closing the
class of bug where a new subtype is added and one of several `switch`
statements over that type's hierarchy is missed, documented with the direct
before-and-after comparison, an `instanceof` chain against the equivalent
exhaustive `switch`, on
https://docs.oracle.com/en/java/javase/21/language/pattern-matching-switch.html,
verified 2026-08-05. That the fix for Repeated Switches was worth adding
new switch syntax to a mainstream, widely deployed language is itself
evidence that the underlying problem is a genuine and recurring one in
production Java codebases, not a theoretical concern.

TypeScript's own handbook documents the discriminated union plus
`never`-typed exhaustiveness check as a first class idiom for exactly the
scattered switch case, showing that adding a new member to a `Shape` union,
`Triangle` alongside `Circle` and `Square`, produces a compile error, "Type
'Triangle' is not assignable to type 'never'", at every `switch` still
missing the new case, source
https://www.typescriptlang.org/docs/handbook/2/narrowing.html, verified
2026-08-05. This is the guard variant from dimension 8 applied at the
language design level rather than through library convention, and it
appears in the official teaching material for the language rather than in a
third party pattern catalog, which is a strong signal of how often
TypeScript teams reach for this shape in ordinary application code, `kind`
fields on network payloads, Redux-style action objects, form state
machines, being three of the most common real world sources of this exact
smell.

## 10. Consequences

Positive. A single site of truth for the discriminant's behaviour means a
new variant is added once, and either the compiler, in a language with
exhaustiveness checking, or a single review of the one consolidated
artifact, catches every place that still needs work. Duplication that a
diff tool or a copy paste detector would never flag, because the branches
differ in their bodies even though they share the same case labels, is
removed entirely by the polymorphic and lookup table variants. Reading a
single variant's full behaviour becomes possible in one place, the
`CreditCardRules` class or table row, rather than requiring a reader to
hunt down every switch that mentions credit cards across the whole
codebase.

Negative. Consolidation by class hierarchy couples every concern that used
to have its own independent switch into one artifact's set of virtual
methods, so a change to how settlement days are computed can now require a
touch to the same file that governs fee calculation, an increase in the
blast radius of an otherwise narrow change, and exactly the trade the forces
in dimension 3 describe. The guard variant, exhaustiveness checking, buys
safety without buying consolidation, so it leaves the actual duplication of
the case labels in place, three switches still exist, they are simply
guaranteed to be kept complete, which some teams correctly treat as a
partial fix rather than a full one. Any of the variants adds a layer of
indirection, a lookup call or a virtual dispatch, over the plain, if
dangerous, directness of reading a switch statement top to bottom, and for a
short lived discriminant this indirection is a net loss, per the
non-applicability list in dimension 4.

## 11. Failure modes and misuse

Symptom. A feature works for every payment method except the one added last
quarter, and only in one specific screen. Cause. The discriminant grew a new
variant, the switch owning the screen in question was never updated, and no
compiler or lint caught it because the language either lacks exhaustiveness
checking or the team never enabled the check available to it. Fix. Apply the
guard variant, sealed type plus exhaustive match, or the consolidation
variant, so the missing case becomes a build failure rather than a runtime
gap.

Symptom. A pull request that adds one new payment provider touches nine
unrelated files, and the reviewer cannot tell whether all nine were actually
necessary or whether the author found them by grepping for an existing
variant's name and hoping the list was complete. Cause. The switches were
never consolidated, so there is no single, enumerable list of "everywhere
this discriminant is handled", and completeness depends entirely on the
author's search skill and memory. Fix. Consolidate to a single Decision
Surface or lookup table, at which point adding a provider touches exactly
one file, the new variant's implementation, plus one line registering it.

Symptom. After consolidating with a class hierarchy, a change to the
receipt-printing logic for one payment method now requires touching the
same file as the fee calculation for that method, even though the two teams
that own receipts and fees never coordinate and did not ask for the
coupling. Cause. The consolidation was applied past the point where
dimension 4's non-applicability reasoning should have stopped it, the
concerns did not actually share a natural home, and forcing them into one
class merged two ownership boundaries that used to be, correctly,
separate. Fix. Split the Decision Surface back into two smaller ones, one
per genuinely separate concern, each still consolidated internally but no
longer sharing a single class per variant. This produces a design closer to
the Strategy pattern applied twice than to one large Visitor, and is the
correct outcome, not a partial failure.

Symptom. A Go codebase has a `switch kind {` in six places, a lint rule was
added requiring `default panic("unhandled kind")` in every one, and the
team believes this makes the switches safe, but a new variant added six
months later still causes five separate runtime panics in production over
the following week as each switch is hit in turn. Cause. A `default panic`
guard converts a silent wrong-answer bug into a loud crash, which is a real
improvement, but it is a runtime guard, not a compile time one, so it still
requires every code path to actually execute in production, or in a test
suite with full coverage of every switch site, before the gap is found. Fix.
Either move to the lookup table variant, where a missing entry can be
checked once, at the single call to `rulesFor`, exhaustively, against the
declared set of constants, in a single unit test, or adopt a linter that
performs static exhaustiveness analysis over Go's untyped enums, several
exist for Go, rather than relying on a runtime panic to surface the gap.

## 12. Trade-off matrix

| Approach | Consolidation | Compile time safety | Coupling risk | Best fit |
|---|---|---|---|---|
| Leave switches as is | none | none | none added | a closed, rarely changed discriminant, dimension 4 |
| Replace Conditional with Polymorphism, class hierarchy | full, one artifact | only if the language also has exhaustiveness checking on the hierarchy | high, unrelated concerns can be pulled together | team owns the type, concerns are genuinely related |
| Visitor pattern | full, one artifact | same as above, language dependent | lower than class hierarchy, the type stays untouched | type is owned elsewhere, or double dispatch is needed |
| Lookup table keyed by discriminant | full, one artifact | none by default, add a completeness test | low, entries can stay pure data | no inheritance available, Go and similar languages |
| Guard with sealed type plus exhaustive match | none, switches remain | full, compiler enforced | none added | concerns genuinely do not share a home, dimension 4 |
| Runtime default-case assertion or panic | none | none, fails at execution, not at build | none added | a stopgap, not a resting state, see dimension 11 |

## 13. Related and incompatible patterns

Switch Statements, this repository's sibling entry, is the single-site
version of the same underlying discriminant problem, and the two entries
share their primary fix, Replace Conditional with Polymorphism. Treat
Switch Statements as the smell to reach for when only one call site
switches on the discriminant, and Repeated Switches once a second
independent call site appears, because the second site is what changes the
cost-benefit calculation around consolidation, a single switch rarely
justifies a class hierarchy on its own.

Factory Method and Abstract Factory frequently sit beside the fix for this
smell rather than replacing it, because something still has to decide,
usually once, which concrete Variant Implementation to construct for a
given discriminant value, and that decision is itself often a single
small switch, deliberately kept, at the one place values are first turned
into objects, everywhere downstream then uses polymorphism rather than the
raw discriminant. This is the correct, narrow surviving switch, and it does
not count against a codebase for still having it.

Primitive Obsession is frequently the root cause one level upstream. A
discriminant that is a bare string or integer rather than a real type is
easier to accidentally re-derive with a fresh switch, because there is
nothing in the type system connecting the string `"creditCard"` scattered
through the codebase back to a single declared source of truth. Fixing
Primitive Obsession first, wrapping the discriminant in a real type or
enum, often surfaces every existing switch on it at once, because the
compiler or the IDE can now find every usage of the type.

Shotgun Surgery and Divergent Change are the two classical smells this one
most resembles in symptom, one logical change requiring edits in many
places, but Repeated Switches is the specific, mechanically recognisable
cause behind a subset of Shotgun Surgery cases, the subset where the many
places are all switches sharing one discriminant, rather than Shotgun
Surgery's broader and vaguer complaint about any kind of scattered change.

Data Clumps is incompatible with the naive reading of the consolidation fix
in one specific way worth naming. If the "same variant" is really a group
of related fields, a country plus a currency plus a locale, rather than one
clean discriminant, attempting to consolidate switches over that group
before first addressing the Data Clumps smell tends to produce a Decision
Surface with an unwieldy multi-argument key, which is a sign the two smells
need to be fixed in order, clumped fields first, into their own small
type, then the switches over the resulting single type.

## 14. Refactoring path in and out

Introducing the consolidation fix, step by step. First, locate every site
that switches or branches on the discriminant, by grepping for the enum,
type, or a representative case label's string value, and list them, this
list is the actual scope of the change and should be written down before
any code moves, because an incomplete list produces an incomplete
migration and a false sense that the smell is gone. Second, define the
Decision Surface, one method per distinct behaviour currently living in one
of the switches, naming each method after what it returns, not after the
switch it came from. Third, for each variant, create the implementation, a
class or a table entry, and move that variant's case body from each of the
original switches into the corresponding method on the new implementation,
one switch at a time, running the test suite after each switch is fully
migrated rather than after the whole set, so a mistake is caught against
one known-good switch's worth of change rather than several at once.
Fourth, once every original switch's cases have been moved, replace the
switch itself with a call through the Decision Surface obtained from a
single factory or lookup function, and delete the now-empty switch. Fifth,
if the language supports it, mark the discriminant's type as sealed or use
a discriminated union, so that even the single remaining factory function
that turns a raw value into a Variant Implementation is itself exhaustively
checked.

Introducing the guard-only fix, step by step, when consolidation is ruled
out by dimension 4. First, convert the discriminant from a bare string,
integer, or unsealed enum into a sealed hierarchy, a discriminated union,
or a language-enforced enum, whichever the language supports. Second, at
each existing switch, add the exhaustiveness mechanism the language
provides, a `never`-typed default in TypeScript, a bare `switch` over the
sealed type with no default case in Java, an unconditional `match` in Rust
or Swift, and delete any prior `default, throw` or `default, panic`, that
scaffolding is no longer needed once the compiler performs the check.
Third, add a new variant as a deliberate, separate change afterward, and
confirm in review that this single-line change to the type produces a
build failure at every one of the surviving switches, proving the guard
actually functions before relying on it in the next real addition.

Removing the fix, when it stops earning its place. The signal that a
consolidated Decision Surface has outlived its usefulness is the symptom
described in dimension 11, edits to one concern's method regularly forcing
review or coordination with an unrelated concern's owner. When that
happens, split the single Decision Surface back into two or more smaller
ones, one per concern that has proven, over real changes, to be
independently owned, each remaining internally consolidated, moving away
from one shared hierarchy toward several smaller Strategy-shaped
interfaces rather than reverting all the way back to scattered switches,
because the underlying discriminant-safety problem that motivated the fix
in the first place has not gone away because the coupling grew too
large.

## 15. Testing and verification

The consolidation fix makes one class of test dramatically easier and
introduces a small new obligation. It becomes possible to write a single
parameterised test that iterates over every declared variant and asserts
that the Decision Surface returns a defined, sane value for every method,
for every variant, which is a test that is structurally impossible to write
against scattered switches, because there is no one place enumerating "the
methods" to iterate over. This single test is worth more than the
individual unit tests for each old switch it replaces, because it is the
test that actually encodes "nothing was left unhandled", the exact property
the smell threatens.

Writing that completeness test concretely means, in a language without
compiler-enforced exhaustiveness, iterating over every value the language
itself considers a member of the enum or sealed type, calling the factory
function that turns each value into a Variant Implementation, and asserting
it does not throw and that every method on the Decision Surface returns
without error. In Go, where the earlier example used a plain map, this
test is a loop over the declared constants, `CreditCard`, `PayPal`,
`BankTransfer`, asserting `rulesFor` succeeds for each, which is the
practical replacement for the compile time exhaustiveness Go's type system
does not provide.

Where the guard variant is used instead of consolidation, the test
obligation shifts from a runtime assertion to a build time one, and the
correct verification is closer to a static check than a unit test, confirm
in continuous integration that the language's exhaustiveness feature is
actually active, `strict` mode enabled in the TypeScript compiler options,
for example, because an exhaustiveness check silently stops protecting the
codebase the moment strict mode is turned off for a file or a build target,
and that regression is invisible in code review unless someone reads the
compiler configuration itself.

The one thing worth naming as a testing anti-pattern specific to this
smell is testing each of the N original switches independently after
consolidation and calling the migration verified. That approach re-creates,
in the test suite, the exact same scattering the production code
eliminated, and a variant accidentally dropped from the Decision Surface
during the migration can still pass every one of those N separate tests if
each test happens to only exercise the variants that were migrated
correctly.

## 16. Observability signals

A codebase still carrying this smell shows a distinctive shape in its own
version control history before it ever shows up as a runtime metric. A
commit that adds a single new value to an enum, followed within days or
weeks by two or three separate follow-up commits each adding one missed
`case` somewhere else, each with a message resembling "fix missing X case
in Y", is the clearest available signal, because it is a direct record of
the smell causing real, sequenced production incidents rather than a
theoretical concern.

Once consolidated, the corresponding healthy signal is the opposite shape,
a commit adding a new variant touches exactly one new file, or one new
entry in one table, and no follow-up commits addressing a missed case
appear afterward for that variant. Grepping the codebase for the number of
distinct files matching the discriminant's name is a rough but genuinely
useful proxy metric to track over time, a rising count across releases,
for a discriminant that is not otherwise growing new concerns, is early
warning that the smell is re-accumulating even before any incident occurs.

At runtime, the signal a healthy consolidated system should emit is close
to silence, because every variant is handled by construction. The signal
an unconsolidated or badly guarded system emits is a spike in a specific,
narrow error class immediately following a deployment that adds a new
variant, an unhandled case exception, a default branch being hit, or a
value coming back as null or undefined where a caller expected a real
answer, and that spike should be correlated in monitoring against the
deploy marker for the enum change, because the two events happening close
together in time is itself diagnostic of this exact smell rather than a
generic bug.

## 17. Security and privacy implications

This entry's security surface is largely indirect, through the failure mode
rather than through the pattern itself, and stating that plainly is more
honest than inventing a direct concern where none exists. The one
concrete risk worth naming, when one of the scattered switches happens to
govern an authorization or access-control decision, and a new variant is
added to the discriminant, the specific danger of a missed case is not
merely a wrong display label, it can be a security check that silently
falls through a `default` branch and grants or denies access incorrectly
for the new variant, until the miss is noticed. A discriminant used for
both business logic and an access decision, a subscription tier that
governs both a display price and which features are turned on, is a strong
signal that the guard variant, compiler enforced exhaustiveness, deserves
priority over the plain consolidation variant, because a missing case there
fails safe only if the language forces every site to be revisited, and a
runtime default is not an acceptable substitute for that guarantee on a
security relevant discriminant.

There is no privacy-specific implication distinct from ordinary data
handling. Consolidating the discriminant's behaviour into fewer, more
readable places has a mild secondary benefit for privacy review, because it
is easier to audit one Decision Surface for whether any variant's
implementation touches personally identifiable data than it is to audit N
scattered switches for the same question, but this is a side effect of the
fix's general readability improvement, not a distinct property of the
pattern.

## 18. References

Fowler, Martin, with Kent Beck, John Brant, William Opdyke, and Don
Roberts. Refactoring, Improving the Design of Existing Code. First edition,
Addison-Wesley, 1999. The original Switch Statements smell and the Replace
Conditional with Polymorphism refactoring.

Fowler, Martin. Refactoring, Improving the Design of Existing Code. Second
edition, Addison-Wesley, 2018. Source for the restructured smell catalogue
that separates a single scattered switch from repeated, multi-site
switches. The precise chapter and page attribution for this specific entry
was not independently confirmed against a live web source at the time of
writing, see dimension 1, and is stated here as the book's second edition
in general rather than a page-level citation.

Fowler, Martin. Replace Conditional with Polymorphism. Refactoring catalog.
https://refactoring.com/catalog/replaceConditionalWithPolymorphism.html,
verified 2026-08-05.

Refactoring catalog index, listing every refactoring from the second
edition including Replace Type Code with Subclasses and Remove Flag
Argument. https://refactoring.com/catalog/, verified 2026-08-05.

HugoMatilla. Refactoring Summary, a public course summary of the first
edition smell and refactoring catalog, used here only to corroborate the
first edition's own wording for the scattered-switch description.
https://github.com/HugoMatilla/Refactoring-Summary, verified 2026-08-05.

LLVM Project. InstVisitor.h source, the InstVisitor class template and its
motivating comment about avoiding repeated switch statements over
instruction opcodes across compiler passes.
https://llvm.org/doxygen/InstVisitor_8h_source.html, verified 2026-08-05.

Oracle. Pattern Matching for Switch, Java SE 21 language documentation,
covering JEP 441 and the exhaustiveness requirement for a switch over a
sealed type.
https://docs.oracle.com/en/java/javase/21/language/pattern-matching-switch.html,
verified 2026-08-05.

TypeScript documentation. Narrowing, covering discriminated unions and
exhaustiveness checking with the never type.
https://www.typescriptlang.org/docs/handbook/2/narrowing.html, verified
2026-08-05.

Gamma, Erich, Richard Helm, Ralph Johnson, and John Vlissides. Design
Patterns, Elements of Reusable Object-Oriented Software. Addison-Wesley,
1994, chapter 5, the Visitor pattern, the structural basis for the
consolidate-by-external-visitor implementation variant in dimension 8.

## Code examples

The three samples below model the same scenario, a payment method
discriminant read by three independent concerns, fee calculation, display
name, and settlement time, each showing this repository's chosen fix for
its language.

TypeScript uses a discriminated union with exhaustiveness checking, the
guard variant from dimension 8, since TypeScript's `never` type makes that
variant close to free.

```typescript
type PaymentMethod =
  | { kind: "creditCard"; last4: string }
  | { kind: "payPal"; email: string }
  | { kind: "bankTransfer"; iban: string };

interface PaymentRules {
  feeCents(amountCents: number): number;
  displayName(): string;
  settlementDays(): number;
}

function assertNever(x: never): never {
  throw new Error(`Unhandled payment kind: ${JSON.stringify(x)}`);
}

function rulesFor(method: PaymentMethod): PaymentRules {
  switch (method.kind) {
    case "creditCard":
      return {
        feeCents: (amount) => Math.round(amount * 0.029) + 30,
        displayName: () => `Card ending ${method.last4}`,
        settlementDays: () => 2,
      };
    case "payPal":
      return {
        feeCents: (amount) => Math.round(amount * 0.034) + 49,
        displayName: () => `PayPal (${method.email})`,
        settlementDays: () => 1,
      };
    case "bankTransfer":
      return {
        feeCents: () => 0,
        displayName: () => `Bank transfer (${method.iban})`,
        settlementDays: () => 3,
      };
    default:
      return assertNever(method);
  }
}

const m: PaymentMethod = { kind: "creditCard", last4: "4242" };
const rules = rulesFor(m);
console.log(rules.feeCents(10000), rules.displayName(), rules.settlementDays());
```

Adding a fourth member to the `PaymentMethod` union without adding a matching
case to `rulesFor` makes the `default` branch's call to `assertNever` fail
to type check, at the exact site that was about to be forgotten, rather
than at runtime once a real bankTransfer-shaped value with the new kind
reaches production.

Java, from JDK 21, achieves the same guarantee natively through a `sealed`
interface and pattern matching for `switch`, JEP 441, so consolidation
happens through language enforced exhaustiveness rather than through a
hand written `never` sentinel.

```java
sealed interface PaymentMethod permits CreditCard, PayPal, BankTransfer {}
record CreditCard(String last4) implements PaymentMethod {}
record PayPal(String email) implements PaymentMethod {}
record BankTransfer(String iban) implements PaymentMethod {}

public class PaymentDemo {
    static int feeCents(PaymentMethod method, int amountCents) {
        return switch (method) {
            case CreditCard c -> (int) Math.round(amountCents * 0.029) + 30;
            case PayPal p -> (int) Math.round(amountCents * 0.034) + 49;
            case BankTransfer b -> 0;
        };
    }

    static String displayName(PaymentMethod method) {
        return switch (method) {
            case CreditCard c -> "Card ending " + c.last4();
            case PayPal p -> "PayPal (" + p.email() + ")";
            case BankTransfer b -> "Bank transfer (" + b.iban() + ")";
        };
    }

    public static void main(String[] args) {
        PaymentMethod m = new CreditCard("4242");
        System.out.println(feeCents(m, 10000) + " " + displayName(m));
    }
}
```

Removing the `case BankTransfer b` line from either switch above is a
compile error in Java 21, "the switch expression does not cover all
possible input values", because `PaymentMethod` is sealed to exactly three
permitted types and the switch has no default. This is the exhaustiveness
guarantee stated as fact in dimension 8, demonstrated directly rather than
only described.

Go has neither sealed hierarchies nor exhaustiveness checked switches, so
the idiomatic fix is the lookup table variant from dimension 8, one map
holding every concern's answer per variant, checked once by a completeness
test rather than by the compiler.

```go
package main

import "fmt"

type PaymentKind int

const (
	CreditCard PaymentKind = iota
	PayPal
	BankTransfer
)

type PaymentRules struct {
	FeeCents       func(amountCents int) int
	DisplayName    func(detail string) string
	SettlementDays int
}

var rulesByKind = map[PaymentKind]PaymentRules{
	CreditCard: {
		FeeCents:       func(a int) int { return a*29/1000 + 30 },
		DisplayName:    func(d string) string { return "Card ending " + d },
		SettlementDays: 2,
	},
	PayPal: {
		FeeCents:       func(a int) int { return a*34/1000 + 49 },
		DisplayName:    func(d string) string { return "PayPal (" + d + ")" },
		SettlementDays: 1,
	},
	BankTransfer: {
		FeeCents:       func(a int) int { return 0 },
		DisplayName:    func(d string) string { return "Bank transfer (" + d + ")" },
		SettlementDays: 3,
	},
}

func rulesFor(kind PaymentKind) (PaymentRules, error) {
	r, ok := rulesByKind[kind]
	if !ok {
		return PaymentRules{}, fmt.Errorf("unhandled payment kind: %v", kind)
	}
	return r, nil
}

func main() {
	r, err := rulesFor(CreditCard)
	if err != nil {
		panic(err)
	}
	fmt.Println(r.FeeCents(10000), r.DisplayName("4242"), r.SettlementDays)
}
```

A fourth Go constant added to the `iota` block with no matching entry added
to `rulesByKind` does not fail to build, `go vet` accepts the program, since
Go has no compile time enumeration exhaustiveness at all, so `rulesFor`
correctly returns the `error` value instead of a zero-valued
`PaymentRules`, and the completeness test described in dimension 15, one
loop asserting `rulesFor` succeeds for every declared constant, is the
mechanism that catches the gap before it reaches production, in place of a
compiler that Go does not provide for this case.
