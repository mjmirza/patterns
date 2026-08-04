---
name: Magic Numbers
slug: magic-numbers
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Magic Literals, Unnamed Numeric Constant, Literal Constant Smell, Magic Constant]
first_described: "McConnell 1993 (Code Complete, 1st edition); catalogued as a refactoring target by Fowler 1999"
maturity: canonical
related: [replace-magic-literal, extract-constant, enum-pattern, configuration-object, value-object]
incompatible_with: []
verified: 2026-08-02
---

# Magic Numbers

## 1. Name, aliases, and lineage

The canonical name in the software engineering literature is Magic Numbers,
extended in more recent style guides and linter documentation to Magic
Literals, a broader label that also covers unexplained string and boolean
constants embedded directly in code. This entry treats the numeric case as the
primary subject, since it is the older and more precisely named concern, and
notes the literal generalization where it changes the analysis.

The earliest widely cited written caution against unexplained numeric literals
appears in Steve McConnell's *Code Complete*, Microsoft Press, first edition,
1993, in the discussion of naming and using variables, where McConnell argues
that a literal value with no explanatory name forces a reader to either trust
the value blindly or reverse-engineer its meaning from surrounding code. The
term magic number itself predates the book. It was in informal use among C
and assembly programmers through the 1980s to describe file format signature
bytes and other hardcoded values, a usage that survives today in the Unix
convention of file magic numbers checked by the `file` command and recorded
in `/usr/share/misc/magic`, a distinct but related sense of the term that
this entry does not cover further.

The pattern's status as a named, catalogued refactoring target was formalized
by Martin Fowler, in *Refactoring. Improving the Design of Existing Code*,
Addison-Wesley, first edition, 1999, under the refactoring Replace Magic
Number with Symbolic Constant, later folded into the broader Replace Magic
Literal entry in the refactoring.com online catalog that accompanies the
book's second edition
([refactoring.com, Replace Magic Literal](https://refactoring.com/catalog/replaceMagicLiteral.html),
verified 2026-08-02). Fowler's catalog entry is the reference most working
programmers cite when they name the fix, which is why this entry treats
Fowler 1999 as the point where magic numbers moved from folk wisdom into a
formally catalogued code smell with a named, mechanical remedy.

A third lineage runs through secure coding standards rather than style
guides. The CERT C Coding Standard, maintained by the CERT Division of
Carnegie Mellon University's Software Engineering Institute, states the same
concern as a numbered rule, DCL06-C, Use meaningful symbolic constants to
represent literal values
([SEI CERT C Coding Standard, DCL06-C](https://cmu-sei.github.io/secure-coding-standards/sei-cert-c-coding-standard/recommendations/declarations-and-initialization-dcl/dcl06-c),
verified 2026-08-02), which frames the problem not only as a readability
concern but as a maintenance hazard, because a value repeated by hand in
multiple places will eventually be updated in some places and not others.

## 2. Problem and context

A magic number is a numeric literal that appears directly in executable code,
in a comparison, an arithmetic expression, an array size, a loop bound, or a
function argument, without a name that explains what the value represents or
why that particular value was chosen. The number `86400` compiles and runs
identically to a named constant `SECONDS_PER_DAY`, but only one of the two
tells a reader anything. The problem is not that the number is wrong. Often
it is correct and stays correct for years. The problem is that its meaning
lives only in the head of whoever wrote it, and that knowledge does not
travel with the code.

The context in which this becomes damaging is any codebase that outlives its
original author's memory, which in practice is nearly every codebase past
its first few weeks. A reviewer reading `if (retries > 3)` cannot tell
whether 3 is a deliberately tuned backoff limit, an arbitrary placeholder
left from a first draft, or a value copied from a different system with
different failure characteristics. A maintainer who needs to change the
retry policy has to first determine every place `3` appears in that role,
distinguish those occurrences from every unrelated `3` in the file (an array
index, a column count, an HTTP status digit), and change only the correct
set. The literal itself carries no marker that would let tooling, or a human
skimming quickly, separate the meaningful occurrences from the coincidental
ones.

The problem compounds when the same conceptual value is needed in more than
one place. Two independently typed occurrences of `86400` in two files are
not guaranteed to stay equal. Nothing in the language enforces it. The
duplication is invisible until the day someone changes one occurrence for a
daylight-saving-time bug fix and misses the other, and the two subsystems
disagree about how long a day is.

## 3. Forces

Immediacy versus intent. Writing the literal `0.075` directly at the point of
use is faster in the moment than defining and naming a constant elsewhere.
The pattern exists because that immediate convenience is real, and the
anti-pattern exists because the convenience is purchased against the cost
paid by every future reader of that line.

Locality versus discoverability. A literal used exactly once, at exactly the
point where it is needed, has perfect locality. A named constant defined
elsewhere requires the reader to jump to a second location to learn the
value, but in exchange it becomes discoverable by search, by IDE
find-usages, and by anyone auditing every place a particular business rule
is encoded.

Precision versus abstraction. Some numeric literals are not business rules at
all but mathematical facts, most visibly `0`, `1`, and `-1` used as
identities, increments, or sentinel comparisons. Naming `1` as `INCREMENT`
adds a layer of indirection over a value whose meaning is already total and
unlikely to change, and this entry's applicability section treats that case
separately from a genuine magic number.

Single-source-of-truth versus performance folklore. In compiled languages a
`const` or equivalent is typically resolved at compile time with zero
runtime cost over the equivalent literal, so this force is close to fully
resolved in the constant's favor in most modern toolchains. It is included
here because the belief that named constants are slower persists as folk
wisdom in some communities and occasionally drives someone back toward
inlined literals for a reason that no longer holds under a modern optimizer.

Team calibration versus rigid enforcement. A team that bans every bare
numeral, including array index 0 and multiplication by 2, produces code
cluttered with single-use constants like `const TWO = 2` that add
indirection without adding meaning. The forces above are in tension
precisely because the right answer depends on whether a specific literal
encodes a decision or expresses a mathematical identity, and no purely
syntactic rule can make that distinction perfectly, which is why every
serious linter for this smell ships a configurable ignore list rather than a
blanket ban.

## 4. Applicability and non-applicability

Treat a numeric literal as a magic number, and extract it, when any of the
following hold.

- The value encodes a business rule, a policy threshold, or a decision that
  could plausibly change, such as a retry limit, a discount percentage, a
  timeout duration, a page size, or a minimum age.
- The same value, or a value that must always equal it, appears more than
  once in the codebase, even if the current occurrences happen to agree.
- The value is not self-explanatory from its literal form. `1000` used as a
  millisecond-to-second conversion factor is not obvious without a comment
  or a name, and `Math.PI` used in a circle-area formula from `3.14159` is
  not obvious that it is intended to be exactly the mathematical constant.
- A future reader, unfamiliar with the code, would need to ask why this
  number is used to understand the line.
- The value crosses a module or team boundary, so that a change to it must
  be coordinated, and a named symbol gives that coordination a single point
  of reference.

Explicit non-applicability, the list this repository treats as the more
valuable half of the dimension. Do not extract a constant, and leave the
literal in place, when any of the following hold.

- The literal is `0` or `1` used as a mathematical or structural identity,
  such as array indexing from zero, an increment or decrement step, a
  boolean-like sentinel in a language without a boolean type, or the base
  case of a recursive or iterative computation. Naming these
  (`const ZERO = 0`) does not add information; it adds a layer that must be
  mentally unwrapped back to the same value. Checkstyle's MagicNumberCheck
  and ESLint's `no-magic-numbers` both default to ignoring at minimum `-1`,
  `0`, and `1` for exactly this reason
  ([Checkstyle, MagicNumberCheck](https://checkstyle.sourceforge.io/checks/coding/magicnumber.html),
  verified 2026-08-02;
  [ESLint, no-magic-numbers](https://eslint.org/docs/latest/rules/no-magic-numbers),
  verified 2026-08-02).
- The literal is a well-known, stable mathematical or physical constant used
  in a formula where the formula itself is the documentation, such as `2`
  in a formula for a circle's circumference immediately adjacent to a
  `radius` variable, or a language's own numeric literal for pi, e, or the
  speed of light drawn from a standard library rather than typed by hand.
- The literal is a test fixture value inside a unit test, where the number's
  specific value is arbitrary by design and the test's assertion, not a
  named constant, is the documentation of intent. Extracting every test
  literal into a shared constant file often reduces test readability by
  forcing the reader to jump elsewhere to see what value is actually being
  asserted.
- The literal is version, protocol, or format-defined and will never change
  by policy, such as `4` for IPv4 or a fixed-width binary format's byte
  offsets defined by an external specification the code is parsing. Naming
  such values is still often good practice, but the applicability judgment
  differs. the reader's why is answered by the external spec, not by a
  business decision internal to the codebase, so a comment citing the spec
  section can be equally or more valuable than a symbolic name.
- The code is genuinely one-off, throwaway, or exploratory, where the cost of
  a future maintainer misreading the value is lower than the cost of
  interrupting the current train of thought to name it. This is a judgment
  call about the code's expected lifetime, not a rule, and it does not
  excuse literals that later get promoted into shipped, maintained code
  without ever being named.

## 5. Structure

Magic numbers are not a structural pattern in the sense of the Gang of Four
catalog. there are no interacting objects, only a single literal token
sitting where a name should be. The structure worth naming is the structure
of its correction, since the fix is what a reader actually needs to recognize
and apply.

- **The literal site**, the location in source where the bare numeral
  appears, embedded in an expression, a default parameter, an array
  dimension, or a comparison.
- **The symbolic constant**, the named binding that replaces the literal at
  its declaration site, typed as narrowly as the language allows (`const`,
  `final`, `enum`, `readonly`, or a module-level frozen binding), placed
  where its scope matches the scope of the concept it represents.
- **The reference site or sites**, every place in the code that now reads
  the name instead of the raw number, which after the fix is one to many,
  whereas the un-refactored version had one to many *independent* literal
  occurrences with no structural link between them.
- **The unit or meaning annotation**, present in the mature form of the fix,
  where the constant's name or its type encodes not just the value but its
  unit and domain, for example `TIMEOUT_MS` rather than `TIMEOUT`, so a
  reader does not have to guess whether the number is milliseconds or
  seconds.

## 6. ASCII structure diagram

```
BEFORE, the anti-pattern

  file_a.ts                    file_b.ts                  file_c.ts
  +----------------+           +----------------+         +----------------+
  | if (age >= 18)  |          | if (age < 18)   |         | minAge = 18     |
  +----------------+           +----------------+         +----------------+
        18                           18                          18
   three independent literal occurrences, no structural link,
   no shared source of truth, no name explaining "18"


AFTER, the fix applied

  constants.ts
  +--------------------------------------+
  | export const ADULT_AGE_YEARS = 18;   |
  +--------------------------------------+
                    ^
        +-----------+-----------+
        |           |           |
   file_a.ts    file_b.ts   file_c.ts
   uses          uses         uses
   ADULT_AGE_YEARS  ADULT_AGE_YEARS  ADULT_AGE_YEARS

   one declaration site, three reference sites, one name that
   answers "why 18" without leaving the call site
```

## 7. Dynamics

The anti-pattern has no interesting runtime dynamics. a magic number behaves
identically to the equivalent named constant once compiled or interpreted,
which is exactly what makes it dangerous. The dynamics worth diagramming are
the two failure sequences that recur when the pattern goes uncorrected.

```
Sequence 1, silent divergence under duplicated literals

  developer A            developer B             production
  edits file_a.ts        edits file_b.ts          behavior
  changes 18 -> 21   (unaware file_b has      file_a now enforces 21
  (raises drinking     its own literal 18)     file_b still enforces 18
  age rule)                                    system is internally
                                                inconsistent, no error
                                                raised, no test fails
                                                unless a test happens
                                                to compare the two paths


Sequence 2, the search-and-guess maintenance cost

  maintainer needs      greps for "18" in       finds N occurrences,
  to change the retry   the codebase             most are unrelated
  limit from 3 to 5      (no named symbol            (array sizes, HTTP
                          to search for)              codes, other ages)
                                                  manually inspects each
                                                  one to classify it,
                                                  risk of missing one or
                                                  changing the wrong one
```

## 8. Implementation variants

The mechanical fix is the same refactoring in every language. introduce a
named, immutable binding at an appropriately scoped location, and replace
every meaningful occurrence of the literal with a reference to that binding.
The variants below differ in how the language expresses named and immutable,
and in how far the fix can be pushed beyond a bare constant.

- **Simple named constant.** A single `const`, `final`, `let` (with a
  module-private convention), or equivalent binding at file or module scope.
  This is the baseline fix and is sufficient whenever the value is used in
  one conceptual role throughout the codebase.
- **Enumeration.** When several related magic numbers form a closed set of
  named alternatives, for example HTTP status code families or a small set
  of retry strategies, an enum (or, in languages without a native enum, a
  frozen object or a sum type) both names the values and makes the closed
  set explicit to the type checker, catching an invalid numeric value at
  compile time rather than only documenting the valid ones.
- **Configuration object or settings module.** When a cluster of related
  magic numbers together describe one tunable policy, such as a retry
  policy with a max-attempts count, a base delay, and a backoff multiplier,
  grouping them into a single named configuration structure documents the
  relationship between the values, not only each value in isolation, and
  gives future tuning a single object to change or inject.
- **Unit-carrying value type.** In languages with a strong type system, the
  most complete variant replaces a bare numeric constant with a small value
  type that carries the unit in its type, for example a `Duration` or
  `Money` type constructed from the constant, so that a caller cannot
  accidentally pass the raw number where a differently-unit value was
  expected. This variant trades a small amount of ceremony for a class of
  unit-confusion bug becoming a compile error rather than a runtime defect,
  and is the same class of fix relevant to the unit-confusion failure mode
  discussed in dimension 11.
- **Externalized configuration.** When the value is genuinely meant to be
  changed by an operator without a code change and redeploy, for example a
  feature's rate limit, the corrected form moves the value out of the
  compiled constant entirely into an environment variable, a feature flag
  service, or a configuration file, with a named, typed accessor in code
  and a documented default. This variant is not always the right choice. it
  trades a compile-time guarantee for runtime flexibility, and introduces
  the operational question of what happens if the external value is absent
  or malformed at startup.

## 9. Known production uses

Static analysis enforcement of this rule exists as shipped, actively
maintained features in widely deployed tools rather than as an academic
suggestion, which is itself the clearest evidence the pattern is treated as
a real, recurring production concern.

- **ESLint's core `no-magic-numbers` rule**, part of the ESLint project
  since v1.7.0 and still shipped in current ESLint releases, flags numeric
  literals outside a configurable ignore list (`ignoreArrayIndexes`,
  `ignoreDefaultValues`, `enforceConst`, and related options), and is used
  across a large share of JavaScript and TypeScript codebases as part of
  standard lint configurations
  ([ESLint, no-magic-numbers](https://eslint.org/docs/latest/rules/no-magic-numbers),
  verified 2026-08-02).
- **Checkstyle's `MagicNumberCheck`**, part of the Checkstyle static
  analysis tool for Java, widely used in enterprise Java build pipelines,
  flags bare numeric literals and, by default, exempts `-1`, `0`, `1`, and
  `2`, encoding the applicability boundary from dimension 4 directly into
  its default configuration
  ([Checkstyle, MagicNumberCheck](https://checkstyle.sourceforge.io/checks/coding/magicnumber.html),
  verified 2026-08-02).
- **The SEI CERT C Coding Standard's DCL06-C**, maintained by Carnegie
  Mellon University's Software Engineering Institute and used as a
  reference standard in safety- and security-critical C development,
  states the rule as a numbered recommendation with compliant and
  noncompliant code examples, and discusses the trade-off between
  `const`-qualified objects, enumeration constants, and preprocessor
  macros as three distinct mechanisms for the fix in C specifically
  ([SEI CERT C Coding Standard, DCL06-C](https://cmu-sei.github.io/secure-coding-standards/sei-cert-c-coding-standard/recommendations/declarations-and-initialization-dcl/dcl06-c),
  verified 2026-08-02).
- **Martin Fowler's refactoring catalog**, accompanying *Refactoring.
  Improving the Design of Existing Code*, documents Replace Magic Literal
  as a named, mechanical refactoring with worked before-and-after code, and
  is the reference most IDE vendors point to when describing an automated
  introduce-constant or extract-constant refactoring feature, which is the
  mechanism by which this specific fix reached mainstream IDE tooling
  rather than staying a manual technique
  ([refactoring.com, Replace Magic Literal](https://refactoring.com/catalog/replaceMagicLiteral.html),
  verified 2026-08-02).

## 10. Consequences

Positive, from applying the fix (naming the constant).

- A single source of truth for a value used in more than one place, so a
  future change is made once and takes effect everywhere consistently.
- Self-documenting call sites, where the reader learns the meaning of a
  value without leaving the line they are reading.
- A searchable, greppable, IDE-navigable anchor for every use of a concept,
  which turns finding every place a rule is enforced from a
  judgment-heavy text search into an exact reference search.
- A single point where a comment, a citation to a specification, or a link
  to the ticket that set the value can live, rather than that context being
  lost or duplicated at every literal occurrence.
- In languages with a static type system, the option to give the constant a
  narrower and more precise type than the number's raw type, catching
  category errors, such as passing a byte count where a millisecond count
  was expected, at compile time.

Negative, from leaving the anti-pattern unfixed (the literal in place).

- Silent divergence, as illustrated in dimension 7, when the same
  conceptual value is duplicated by hand and one occurrence is updated
  without the others.
- Increased code review cost, because a reviewer must ask why an
  unfamiliar literal was chosen for every occurrence rather than reading a
  name and moving on.
- Increased onboarding cost for new team members, who must reconstruct the
  business rationale behind a bare number from commit history, chat logs,
  or a colleague's memory, none of which is guaranteed to still exist.
- Fragile, error-prone maintenance, because changing the value requires a
  manual, unreliable search-and-classify pass across the codebase rather
  than a single edit.
- A false sense of simplicity. A codebase with many inline literals often
  looks shorter and simpler on a diff, which can make magic numbers a
  systemic problem that accumulates gradually, each individual instance too
  small to justify stopping to fix, until the codebase has hundreds of
  unexplained numbers and no practical way to safely change any of them.

There is also a real, if smaller, cost on the other side, named honestly
because a pattern that names no cost has been described wrongly. Extracting
every literal, including the ones covered by the non-applicability list in
dimension 4, adds indirection. a reader following `MAX_RETRY_COUNT` back to
its declaration to learn it is `3` has done strictly more work than reading
`3` directly, if `3` was already self-explanatory in context. The
anti-pattern is real, but so is its overcorrection, discussed further in
dimension 11.

## 11. Failure modes and misuse

**Symptom.** Two subsystems silently disagree about a rule that is supposed
to be shared, and the disagreement is discovered only by an end user hitting
inconsistent behavior, not by any test or build failure.
**Cause.** The same conceptual value was typed as an independent literal in
each subsystem instead of sourced from one shared constant, so nothing links
the two occurrences and nothing detects when one is edited without the
other.
**Fix.** Extract a single shared constant or configuration value at the
appropriate shared scope (a shared module, a shared package, or an
externalized configuration key), and update both call sites to reference it,
so a future change is structurally forced to apply to both.

**Symptom.** A unit-confusion defect ships to production. A duration is off
by a factor of 1000, a currency amount is off by a factor of 100, or a
distance is off by a large, systematic factor.
**Cause.** A bare numeric conversion factor, such as `1000` for
milliseconds-to-seconds or `100` for cents-to-dollars, was multiplied or
divided inline at one call site with no name and no unit indication, so a
second call site performing the equivalent conversion in the wrong direction
(multiplying where it should divide, or vice versa) was not caught by any
check, because both the correct and the incorrect literal are valid numbers
to the compiler. This is the same broad class of failure documented in
NASA's Mars Climate Orbiter mission failure review, where a spacecraft was
lost after ground software produced small forces in pound-seconds while the
trajectory model expected newton-seconds, an unnamed and unchecked unit
assumption baked into a numeric interface rather than a shared, verifiable
value
([NASA, Mars Climate Orbiter Mishap Investigation Board Phase I Report, 1999](https://llis.nasa.gov/llis_lib/pdf/1009464main1_0641-mr.pdf),
verified 2026-08-02).
**Fix.** Replace the bare conversion factor with a named, unit-carrying
constant or, in a typed language, a small value type that makes the unit
part of the type rather than a convention the programmer must remember at
every call site, per the unit-carrying value type variant in dimension 8.

**Symptom.** A linter rule intended to catch magic numbers instead produces
a large volume of low-value warnings, and the team either disables the rule
entirely or reflexively wraps every flagged literal, including array
indices and loop increments, in a single-use named constant, without
distinguishing meaningful values from structural ones.
**Cause.** Overcorrection. This is the applicability boundary from
dimension 4 being ignored in either direction, either by leaving the
detection tool at an overly aggressive default, or by the team treating
the linter's flag as sufficient reason to extract a constant without asking
whether the value is actually a business decision or a mathematical
identity.
**Fix.** Configure the detection tool's ignore list to match the team's
actual applicability judgment (most tools default to ignoring `-1`, `0`,
and `1`, and allow further additions), and treat a flagged literal as a
prompt to ask whether this number encodes a decision rather than as an
automatic instruction to extract a constant.

**Symptom.** A named constant is introduced, but its name is as unhelpful as
the literal it replaced, for example `const NUMBER = 18`, or the constant's
name describes the value rather than its meaning, for example
`const EIGHTEEN = 18`.
**Cause.** The mechanical step of the refactoring (introduce a named
binding) was performed without the semantic step (choose a name that
explains why this value is used here), so the code has traded one
unexplained token for another unexplained token with extra indirection.
**Fix.** Name the constant for the concept it represents in the domain, not
for its numeric value. use `ADULT_AGE_YEARS`, not `EIGHTEEN`, so that a
future change to the legal age in a jurisdiction that defines adulthood at
21 changes the value without requiring the name to also change.

**Symptom.** A magic number silently changes meaning across a codebase's
history because the constant it was extracted into was scoped too broadly,
and a second, unrelated feature began reusing the same named constant for a
coincidentally identical value that later needed to diverge.
**Cause.** Two conceptually distinct values happened to be numerically equal
at the time of extraction (for example, a maximum retry count and a maximum
concurrent connection count both happened to be `3`), were merged into one
shared constant to avoid duplication, and later needed independent values,
forcing a de-duplication refactor under time pressure.
**Fix.** Scope a constant to the single concept it represents, not to the
numeric value it currently holds. two values that are equal today but
conceptually distinct should be two separate named constants, even if that
means accepting the appearance of duplication, because the duplication is
of the number, not of the concept.

## 12. Trade-off matrix

| Force | Magic number left inline | Named constant (dimension 8, simple) | Configuration object | Externalized configuration |
|---|---|---|---|---|
| Readability at call site | Low, no context | High, name explains intent | High, plus relationship to sibling values | Medium, requires a lookup at runtime to know current value |
| Single source of truth | None, duplication risk | Yes, within the process | Yes, within the process | Yes, across processes and deploys |
| Change without redeploy | No | No | No | Yes |
| Compile-time safety | None | Type of the constant, if typed | Type of the object, if typed | Usually none, validated at load time at best |
| Setup and ceremony cost | Zero | Low, one declaration | Medium, group and name a related set | High, external store, access layer, failure handling for absence |
| Appropriate for a mathematical identity such as 0 or 1 | Yes, per dimension 4 | Usually unnecessary indirection | Not applicable | Not applicable |
| Appropriate for an operator-tunable business policy | No, hides the policy | Adequate if rarely changed | Good if several related values | Best, matches the actual change cadence |
| Risk of overcorrection | Low by definition | Medium if applied to identities | Low | Low, but adds an operational failure mode (missing or malformed config) |

## 13. Related and incompatible patterns

**Replace Magic Literal**, Fowler's named refactoring, is the mechanical
procedure that fixes this anti-pattern. this entry is the problem, and
Replace Magic Literal is its solution, described operationally in
dimension 14.

**Extract Constant**, the IDE-tooling name for the same mechanical move in
most modern editors, composes directly with this anti-pattern as the
automated version of the manual refactoring.

**Enum Pattern** composes with this anti-pattern whenever the magic numbers
in question form a closed, named set of alternatives rather than a single
independent value, turning a family of related magic numbers into one typed
declaration, per the enumeration variant in dimension 8.

**Configuration Object** and **Value Object** both compose with this
anti-pattern as escalations of the simple named-constant fix, applied when
either several related magic numbers travel together as one policy, or a
single magic number's unit needs to be enforced by the type system rather
than by convention, respectively.

**Feature Flag** patterns compose with the externalized-configuration
variant of the fix, when the underlying magic number is not merely a value
that should be named but a value that different environments or user
cohorts should be able to see different values of at runtime.

No pattern in this repository is fully incompatible with fixing magic
numbers. naming a constant is a strict improvement in explanatory power over
an unnamed literal in every applicable case listed in dimension 4, so this
entry lists no incompatible patterns. The tension is not with another
pattern but with the non-applicability boundary described in dimension 4,
where applying the fix to a mathematical identity or a self-documenting
formula constant is itself a misuse, covered in dimension 11.

## 14. Refactoring path in and out

Introducing the fix, step by step, following the shape of Fowler's Replace
Magic Literal.

1. Identify a numeric literal whose meaning is not obvious from its
   immediate context, using the applicability checklist in dimension 4 to
   decide whether it is worth naming.
2. Search the codebase for every other occurrence that represents the same
   conceptual value, not merely the same numeral, since a coincidentally
   equal but conceptually distinct number should not be merged, per the
   fifth failure mode in dimension 11.
3. Choose a scope for the new constant that matches the scope of the
   concept, not the scope of convenience. a value used only within one
   function belongs at that function's enclosing module, not in a
   project-wide shared constants file, and a value shared across modules
   belongs at the narrowest shared scope that still reaches every user.
4. Declare the constant with the narrowest immutability guarantee the
   language offers (`const`, `final`, `readonly`, a frozen enum member),
   and name it for the concept, including its unit where the value has one.
5. Replace each identified occurrence of the literal with a reference to
   the new constant, one occurrence at a time, running the test suite or
   re-verifying behavior after each replacement rather than as one large
   batch, so that any occurrence that turns out not to actually share the
   same meaning is caught in isolation rather than mixed into a large diff.
6. Where the language and codebase conventions support it, add a
   configurable lint rule (dimension 9) so that new magic numbers of the
   same kind are flagged going forward rather than relying on manual
   vigilance to catch the next occurrence.

Removing the fix, when a named constant has stopped earning its place, is
the rarer direction, and it belongs in this entry per the repository's
policy on documenting the removal path, not only the introduction path.

1. Confirm the constant is used in exactly one place and its value is
   unlikely to be duplicated in the future, most commonly a value that has
   turned out, after the fact, to be a mathematical identity or a
   self-evident formula constant rather than a business decision, per
   dimension 4's non-applicability list.
2. Confirm removing the name does not remove useful context that currently
   lives only in the constant's declaration, such as a comment citing a
   specification or a ticket. if such context exists, move it to an inline
   comment at the literal's new location rather than discarding it.
3. Inline the literal at its single remaining call site, and delete the now
   unused declaration, verifying with the codebase's own dead-code or
   unused-export tooling that nothing else references the removed symbol.

## 15. Testing and verification

Magic numbers themselves are not directly unit-testable as a code smell.
what is testable is the presence or absence of the fix, and the correctness
of the value once named. Three practical techniques apply.

- **Static analysis as a testing gate.** ESLint's `no-magic-numbers`,
  Checkstyle's `MagicNumberCheck`, and equivalent rules in other language
  toolchains' linters and static analyzers can run as part of a test or
  build pipeline, failing the build on a newly introduced, unconfigured
  numeric literal, which turns the question of whether the team forgot to
  name a value into a mechanically enforced check rather than a code
  review judgment call
  ([ESLint, no-magic-numbers](https://eslint.org/docs/latest/rules/no-magic-numbers),
  verified 2026-08-02;
  [Checkstyle, MagicNumberCheck](https://checkstyle.sourceforge.io/checks/coding/magicnumber.html),
  verified 2026-08-02).
- **Golden-value tests against the named constant, not the raw number.**
  Once a value is named, tests that assert business behavior should
  reference the constant rather than restate the literal, for example
  `expect(minAge).toBe(ADULT_AGE_YEARS)` rather than
  `expect(minAge).toBe(18)`, so that a deliberate future change to the
  constant does not also require finding and editing every test that
  independently hardcoded the old number.
- **Consistency tests across duplicated occurrences, during migration.**
  While a codebase is being migrated away from duplicated magic numbers
  toward a shared constant, a temporary test asserting that every known
  independent occurrence still equals the same value is a useful safety
  net that catches the exact silent-divergence failure mode described in
  dimension 11 before the migration is complete, and can be deleted once
  the duplication is fully removed.

## 16. Observability signals

A magic number, once shipped, produces no distinctive runtime signal of its
own. it behaves identically to a named constant of the same value. The
observability concern is therefore at build and review time rather than at
runtime, and the signals worth tracking are process signals.

- **Lint rule violation count over time**, tracked as a metric in CI, for
  the team's chosen magic-number detection rule, as a leading indicator of
  whether the anti-pattern is accumulating or being actively kept in check.
- **A rising ratio of duplicated literal values detected by a
  copy-paste or duplication scanner**, which frequently correlates with
  magic-number duplication specifically, since a duplicated block of code
  containing a business-rule literal is exactly the shape that produces
  the silent-divergence failure mode.
- **At runtime**, the only useful signal is indirect. an assertion or
  invariant check comparing two values that are supposed to always be
  equal (for example, two subsystems' independently configured timeout
  values) firing in production is a strong, if belated, signal that a
  magic number was duplicated rather than shared, and such an invariant
  check is itself a defensive technique worth adding wherever the failure
  mode in dimension 11 is plausible and expensive.

## 17. Security and privacy implications

Magic numbers carry a modest but real security implication, distinct from
their maintainability cost. A security-relevant threshold expressed as a
bare literal, such as a password minimum length, a rate limit, a token
expiry duration, or a maximum file upload size, is exactly as easy to
silently duplicate and drift as any other magic number, but the consequence
of drift is a security control rather than a cosmetic inconsistency. two
independently hardcoded rate limits that drift apart can leave one code
path with a materially weaker limit than the team believes is in force
everywhere. This is the reasoning behind CERT C's framing of DCL06-C as a
recommendation with security relevance rather than purely a style
preference, since the standard's own example set includes buffer-size and
threshold-style literals whose miscoordination has direct memory-safety
consequences in C
([SEI CERT C Coding Standard, DCL06-C](https://cmu-sei.github.io/secure-coding-standards/sei-cert-c-coding-standard/recommendations/declarations-and-initialization-dcl/dcl06-c),
verified 2026-08-02).

There is no privacy implication specific to this pattern. a magic number
does not itself constitute or expose personal data, and this entry states
that plainly rather than inventing a concern, per the repository's
judgement-versus-sourced-claim rule. A magic number that happens to be a
literal date of birth, account identifier, or similarly sensitive constant
hardcoded into source is a separate, more serious defect (a hardcoded
secret or hardcoded personal data pattern), not an instance of this
anti-pattern, though the same extract-and-name remediation habit that fixes
ordinary magic numbers is also the habit that tends to surface such values
for review before they ship.

## 18. References

1. McConnell, Steve. *Code Complete*, first edition, Microsoft Press, 1993.
   Discussion of variable naming and unexplained literal values in the
   chapter on using data.
2. Fowler, Martin. "Replace Magic Literal." refactoring.com, catalog entry
   accompanying *Refactoring. Improving the Design of Existing Code*,
   Addison-Wesley. https://refactoring.com/catalog/replaceMagicLiteral.html,
   verified 2026-08-02.
3. ESLint. "no-magic-numbers." ESLint core rules documentation.
   https://eslint.org/docs/latest/rules/no-magic-numbers, verified
   2026-08-02.
4. Checkstyle. "MagicNumberCheck." Checkstyle coding checks documentation.
   https://checkstyle.sourceforge.io/checks/coding/magicnumber.html,
   verified 2026-08-02.
5. Software Engineering Institute, Carnegie Mellon University. "DCL06-C.
   Use meaningful symbolic constants to represent literal values." SEI CERT
   C Coding Standard.
   https://cmu-sei.github.io/secure-coding-standards/sei-cert-c-coding-standard/recommendations/declarations-and-initialization-dcl/dcl06-c,
   verified 2026-08-02.
6. NASA. *Mars Climate Orbiter Mishap Investigation Board, Phase I Report*,
   November 10, 1999.
   https://llis.nasa.gov/llis_lib/pdf/1009464main1_0641-mr.pdf, verified
   2026-08-02. Cited for the general class of unit-confusion failure
   discussed in dimension 11, not as a claim that the mission failure
   involved a literal source-code magic number in the sense this entry
   defines.

## Code examples

### TypeScript

```typescript
// magic-numbers.ts

// Before, magic numbers with no explanation.
function badLatePenalty(daysLate: number, amountDue: number): number {
  if (daysLate > 30) {
    return amountDue * 0.15;
  }
  if (daysLate > 7) {
    return amountDue * 0.05;
  }
  return 0;
}

// After, named constants carry the business meaning.
const GRACE_PERIOD_DAYS = 7;
const SEVERE_LATE_THRESHOLD_DAYS = 30;
const MODERATE_LATE_FEE_RATE = 0.05;
const SEVERE_LATE_FEE_RATE = 0.15;

function latePenalty(daysLate: number, amountDue: number): number {
  if (daysLate > SEVERE_LATE_THRESHOLD_DAYS) {
    return amountDue * SEVERE_LATE_FEE_RATE;
  }
  if (daysLate > GRACE_PERIOD_DAYS) {
    return amountDue * MODERATE_LATE_FEE_RATE;
  }
  return 0;
}

const cases: Array<[number, number, number]> = [
  [0, 1000, 0],
  [10, 1000, 50],
  [45, 1000, 150],
];

for (const [days, amount, expected] of cases) {
  const actual = latePenalty(days, amount);
  console.log(`daysLate=${days} amount=${amount} -> ${actual} (expected ${expected})`);
  if (actual !== expected) {
    throw new Error(`mismatch for daysLate=${days}`);
  }
}
console.log("all cases passed");
```

Compiled and run with `npx tsc --strict --target es2020 --module commonjs
magic-numbers.ts && node magic-numbers.js`. Output showed
`daysLate=0 amount=1000 -> 0 (expected 0)`,
`daysLate=10 amount=1000 -> 50 (expected 50)`, and
`daysLate=45 amount=1000 -> 150 (expected 150)`, followed by
`all cases passed`.

### Python

```python
"""magic_numbers.py"""

# Before, magic numbers with no explanation.
def bad_late_penalty(days_late: float, amount_due: float) -> float:
    if days_late > 30:
        return amount_due * 0.15
    if days_late > 7:
        return amount_due * 0.05
    return 0.0


# After, named constants carry the business meaning.
GRACE_PERIOD_DAYS = 7
SEVERE_LATE_THRESHOLD_DAYS = 30
MODERATE_LATE_FEE_RATE = 0.05
SEVERE_LATE_FEE_RATE = 0.15


def late_penalty(days_late: float, amount_due: float) -> float:
    if days_late > SEVERE_LATE_THRESHOLD_DAYS:
        return amount_due * SEVERE_LATE_FEE_RATE
    if days_late > GRACE_PERIOD_DAYS:
        return amount_due * MODERATE_LATE_FEE_RATE
    return 0.0


if __name__ == "__main__":
    cases = [(0, 1000, 0), (10, 1000, 50), (45, 1000, 150)]
    for days, amount, expected in cases:
        actual = late_penalty(days, amount)
        print(f"daysLate={days} amount={amount} -> {actual} (expected {expected})")
        assert actual == expected, f"mismatch for daysLate={days}"
    print("all cases passed")
```

Run with `python3 magic_numbers.py`. Output showed
`daysLate=0 amount=1000 -> 0.0 (expected 0)`,
`daysLate=10 amount=1000 -> 50.0 (expected 50)`, and
`daysLate=45 amount=1000 -> 150.0 (expected 150)`, followed by
`all cases passed`.

### Go

```go
package main

import "fmt"

// Before, kept as a comment for contrast, is not compiled.
// func badLatePenalty(daysLate int, amountDue float64) float64 {
//     if daysLate > 30 {
//         return amountDue * 0.15
//     }
//     if daysLate > 7 {
//         return amountDue * 0.05
//     }
//     return 0
// }

// After, named constants carry the business meaning.
const (
	GracePeriodDays         = 7
	SevereLateThresholdDays = 30
	ModerateLateFeeRate     = 0.05
	SevereLateFeeRate       = 0.15
)

func latePenalty(daysLate int, amountDue float64) float64 {
	if daysLate > SevereLateThresholdDays {
		return amountDue * SevereLateFeeRate
	}
	if daysLate > GracePeriodDays {
		return amountDue * ModerateLateFeeRate
	}
	return 0
}

func main() {
	cases := []struct {
		days     int
		amount   float64
		expected float64
	}{
		{0, 1000, 0},
		{10, 1000, 50},
		{45, 1000, 150},
	}

	for _, c := range cases {
		actual := latePenalty(c.days, c.amount)
		fmt.Printf("daysLate=%d amount=%.0f -> %.0f (expected %.0f)\n", c.days, c.amount, actual, c.expected)
		if actual != c.expected {
			panic(fmt.Sprintf("mismatch for daysLate=%d", c.days))
		}
	}
	fmt.Println("all cases passed")
}
```

Run with `go run magic_numbers.go`. Output showed
`daysLate=0 amount=1000 -> 0 (expected 0)`,
`daysLate=10 amount=1000 -> 50 (expected 50)`, and
`daysLate=45 amount=1000 -> 150 (expected 150)`, followed by
`all cases passed`.

Java, Rust, and Swift are omitted from the worked examples. The pattern and
its fix are language-independent and translate directly (a `static final`
field in Java, a `const` item in Rust, a `static let` or top-level `let` in
Swift), so a fourth idiom-for-idiom example would repeat the same three-line
lesson already shown above without demonstrating a language-specific
variant of the fix.
