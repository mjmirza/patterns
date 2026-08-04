---
name: Duplicate Code
slug: duplicate-code
family: 02-code-smells
category: Bloaters
aliases: [Code Clone, Copy-Paste Code, Duplicated Code]
first_described: "Fowler, Beck 1999"
maturity: canonical
related: [extract-function, extract-class, template-method, pull-up-method, strategy]
incompatible_with: []
verified: 2026-08-02
---

# Duplicate Code

## 1. Name, aliases, and lineage

The canonical name is Duplicate Code, sometimes written Duplicated Code. It is
one of the original code smells catalogued by Kent Beck and Martin Fowler in
the "Bad Smells in Code" chapter of Martin Fowler, *Refactoring. Improving the
Design of Existing Code*, Addison-Wesley, 2nd edition, 2018, chapter 3 ([Fowler's
own page for the book confirms the 2018 second edition](https://martinfowler.com/books/refactoring.html),
verified 2026-08-02). Beck is credited as co-author of the smell catalogue in
the first edition, 1999, and the second edition keeps the same smell under the
same name while renaming several of the associated refactorings, notably
Extract Method to Extract Function ([the refactoring.com catalog for the second
edition lists Extract Function, Extract Class, Pull Up Method, Pull Up Field
and Pull Up Constructor Body among the operations used against this
smell](https://refactoring.com/catalog/), verified 2026-08-02).

The academic literature calls the same underlying artifact a code clone rather
than a smell, and studies it as a static-analysis target rather than a design
complaint. Wikipedia's summary of the research area states that duplicate code
is also known as code clones, that detection uses techniques including Baker's
algorithm, abstract syntax tree comparison, and locality-sensitive hashing, and
that duplication can arise from copy-and-paste programming, independent
parallel development by separate teams, automated code generation, and
tool-inserted boilerplate ([Wikipedia, Duplicate code](https://en.wikipedia.org/wiki/Duplicate_code),
verified 2026-08-02). The two literatures, design smells and clone detection,
describe the same phenomenon from different vantage points, one asking whether
the code should change shape, the other asking how to find copies at scale.

A useful distinction, drawn from the code-smell literature rather than a single
citation, separates three levels of sameness that get flattened into one word
in everyday conversation.

- **Exact duplication.** Token-for-token identical fragments, typically the
  product of copy-paste with no edits. The cheapest to find and the cheapest
  to fix, because a single extraction covers every instance without
  parameterization.
- **Near duplication, a clone with small edits.** Fragments that differ in
  a literal, a variable name, or a single line, while sharing the same shape.
  This is the harder case in practice, because the extraction needs a
  parameter or two to absorb the differences, and a badly chosen parameter set
  produces the coupled, sprawling abstraction that critics of over-eager
  deduplication warn about.
- **Structural or semantic duplication.** Two fragments that read differently
  but compute the same thing, for example one branch written with an early
  return and another written with a boolean flag, or the same business rule
  encoded once as a SQL constraint and once as an application-level check.
  This level is invisible to a textual clone detector and is only found by a
  reader, or by a semantic-diff tool that reasons about behaviour rather than
  tokens.

## 2. Problem and context

The same idea is written down twice, or more, in a codebase, so that changing
the idea means finding and editing every copy.

The situation is recognisable without needing the smell's name. Two functions
compute a discount in slightly different ways because one was pasted from the
other and adjusted for a new promotion. Two API handlers validate an email
address with the same regular expression typed out twice. A rule about which
customers qualify for free shipping lives once in a database trigger and once
in application code, and the two definitions have quietly drifted apart over
three years of unrelated changes. None of these fragments is wrong on its own.
The problem only becomes visible at the moment somebody has to change the
rule and either finds all the copies, at real cost and real risk of missing
one, or changes only the copy they can see and introduces an inconsistency
that nobody notices until a customer complains.

Duplication forms out of ordinary, defensible pressure, not out of neglect.
Copy-paste-and-adjust is the fastest way to ship a variant of existing
behaviour under a deadline, and it produces working code in minutes rather
than the hour an extraction might take. Two programmers, or two teams, working
on parallel features can independently reinvent the same validation or the
same formatting rule without either one knowing the other exists, especially
in a codebase too large for either to have read in full. Some duplication is
inserted by tools rather than people, a code generator that emits the same
boilerplate constructor in every generated class, or an IDE template that
scaffolds a repeated error-handling block. Wikipedia's summary lists exactly
these mechanisms, copy-and-paste, independent development, and automated
insertion, as the recognised causes of duplicate code arising in real
codebases ([Wikipedia, Duplicate code](https://en.wikipedia.org/wiki/Duplicate_code),
verified 2026-08-02).

The context in which this smell is worth acting on has three parts, and
missing any one of them is why blind deduplication so often makes things
worse rather than better, a point developed further in dimension 4.

- The duplicated fragments encode the same DECISION, the same piece of domain
  knowledge, not merely the same syntactic shape by coincidence. Two loops
  that both happen to iterate and print are not duplicate knowledge just
  because they look alike.
- The decision is likely to CHANGE again, so that a future edit will need to
  touch every copy, and missing one produces a real defect rather than a
  cosmetic inconsistency.
- There is a genuinely simpler place to put the single definition, one that
  every caller can reach without importing an unrelated concept, and without
  forcing callers that need slightly different behaviour to thread new flags
  through a shared function.

## 3. Forces

Duplicate Code sits at the center of a set of pressures that pull toward
different resolutions, and naming them plainly is what separates a
disciplined refactor from a reflexive one.

- **Maintenance cost versus short-term velocity.** A single definition changes
  in one place. Duplication lets each caller ship independently today, at the
  cost of every future change needing to be applied N times, with the risk
  scaling with N and with the time elapsed since the copies were made.
- **Coupling versus independence.** Extracting a shared function or class
  couples every caller to that one definition. When the callers' needs
  diverge later, that coupling becomes a liability, because a change for one
  caller can silently affect the others. Duplication, by contrast, keeps
  callers independent at the price of inconsistency.
- **The correct abstraction versus a premature one.** Removing duplication
  before the real shape of the variation is known produces an abstraction
  built from too few examples, one that then has to sprout parameters and
  conditionals to cover cases it did not originally anticipate. Sandi Metz
  makes this trade explicit, arguing that "duplication is far cheaper than
  the wrong abstraction," and that when an abstraction has become wrong, "the
  fastest way forward is back," meaning inline it and let each caller keep
  what it actually needs ([Sandi Metz, "The Wrong Abstraction," 2016](https://www.sandimetz.com/blog/2016/1/20/the-wrong-abstraction),
  verified 2026-08-02).
- **Readability versus indirection.** A single well-named function is often
  more readable than two inline copies scattered across a file, because the
  name documents intent. But an extraction reached for two callers with
  genuinely different intent buries that difference behind a name that has to
  lie a little to cover both, which is a readability cost of its own.
- **Cognitive load of tracking copies versus cognitive load of tracing
  indirection.** A reader following duplicated code sees everything the
  function does, in one place, at the cost of not knowing whether a sibling
  copy diverges. A reader following an extracted abstraction has to jump to
  another file to see what actually happens, at the benefit of knowing there
  is exactly one behaviour to reason about.
- **Operability and blast radius.** A bug fixed in one copy of duplicated
  logic and not the others produces an operational surprise, sometimes
  months later, in the specific code path nobody remembered to patch. A bug
  fixed in a single shared definition is fixed everywhere at once, for better
  when the fix is correct and for worse when the fix was itself wrong and now
  affects every caller simultaneously.

The pattern this smell points toward, extraction into a shared function or
class, favours the maintenance-cost, correctness-consistency, and blast-radius
forces. It sacrifices some independence between callers and accepts the risk
of a premature or leaky abstraction if applied before the true shape of
variation is understood.

## 4. Applicability and non-applicability

Act on duplicate code when the following hold, together.

- The same business rule, validation, calculation, or protocol detail is
  written more than once, and a change to that rule is plausible, not merely
  theoretical.
- At least three real instances exist, or a compelling reason exists to
  believe a third is imminent. This is the Rule of Three, attributed to Don
  Roberts and popularised by Martin Fowler's *Refactoring*, which holds that
  two instances of similar code do not by themselves justify refactoring, but
  a third instance is the point at which the maintenance cost of tolerating
  duplication starts to exceed the cost of extracting a shared abstraction
  ([Wikipedia, Rule of three (computer programming)](https://en.wikipedia.org/wiki/Rule_of_three_(computer_programming)),
  verified 2026-08-02).
- The duplicated fragments are, or can be made, genuinely identical in
  intent, not merely similar in appearance. Two fragments that happen to
  produce the same tokens for unrelated reasons are a coincidence, not a
  duplication worth removing.
- A shared home for the extraction exists, or can be created, that every
  caller can depend on without introducing a dependency cycle or forcing an
  unrelated concept into an unrelated module.

Do NOT deduplicate, or defer deduplication, in these situations, each with the
reason spelled out.

- **Two instances, not three.** Per the Rule of Three, extracting on the
  second occurrence is usually premature. The extraction is built from a
  sample of two, which is too small to know which parts are essential and
  which parts happened to be identical by accident, and a wrong guess bakes
  itself into a shared abstraction that then has to be un-baked later
  ([Wikipedia, Rule of three](https://en.wikipedia.org/wiki/Rule_of_three_(computer_programming)),
  verified 2026-08-02).
- **Coincidental similarity across unrelated domains.** Two validation
  functions that happen to both check "is this string non-empty and under 50
  characters" are not encoding the same business rule merely because the code
  is identical today. A username length rule and a coupon-code length rule
  can coincide in value without being the same concept, and coupling them
  through a shared function means a future change to one silently changes the
  other. Kent C. Dodds names this failure mode directly, describing the
  practice of pausing before abstracting as AHA, Avoid Hasty Abstractions, and
  recommending that engineers "optimize for change first" rather than for the
  absence of repeated tokens ([Kent C. Dodds, "AHA Programming," 2020](https://kentcdodds.com/blog/aha-programming),
  verified 2026-08-02).
- **The variation points are still unknown.** When the second and later
  instances of a fragment are expected to diverge further as more
  requirements arrive, waiting preserves the ability to see the real shape of
  the variation before committing to one. Metz's advice to prefer duplication
  over the wrong abstraction, and to inline rather than patch a wrong one,
  applies with full force here ([Sandi Metz, "The Wrong Abstraction"](https://www.sandimetz.com/blog/2016/1/20/the-wrong-abstraction),
  verified 2026-08-02).
- **Cross-team ownership boundaries.** Two teams that each own a copy of
  similar validation logic, in separate services, may be intentionally
  decoupled so that one team's release cadence never blocks or is blocked by
  the other's. Extracting a shared library here trades organisational
  independence for code-level consistency, and the trade is not automatically
  a win.
- **A platform or language limitation forces the copy.** When a language
  cannot express a genuinely shared abstraction without contorting the
  design, for example a build target that forbids a shared dependency, some
  duplication is the least bad option available, and Wikipedia's own summary
  of the topic concedes that in some circumstances duplication is "the most
  effective solution" given the constraints ([Wikipedia, Duplicate code](https://en.wikipedia.org/wiki/Duplicate_code),
  verified 2026-08-02).
- **Generated or vendored code.** Code produced by a generator, or copied
  wholesale from a third-party source and intentionally left unmodified so it
  can be re-synced later, is not a smell in the design sense even when a
  clone detector flags it. The fix belongs upstream, in the generator or the
  vendoring process, not in the generated output.
- **Test fixtures that favour local readability.** Some test suites
  intentionally duplicate setup code across test cases so that each test can
  be read and understood in isolation without following an indirection into a
  shared fixture. This trade favours local readability of a single test file
  over the maintenance cost of the duplication, and is a defensible choice
  within a codebase's own testing conventions, discussed further in dimension
  15.

## 5. Structure

Duplicate Code is a smell about the shape of existing code, not a pattern with
its own participants in the way a design pattern has collaborating roles. The
structure worth naming is the pattern this smell resolves into once acted on,
and the vocabulary for describing the duplication itself before that happens.

- **The fragment.** A run of statements, a function body, a class, or a query
  that is copied, exactly or with small edits, into more than one location.
- **The occurrence sites.** Each place the fragment, or a near-identical
  variant of it, currently lives. Every occurrence site is a maintenance
  liability until the fragment has one home.
- **The variation points.** The places where the occurrences differ from one
  another, a literal value, a condition, an order of operations. These become
  the parameters, the subclass hooks, or the strategy objects of whichever
  extraction resolves the duplication.
- **The extraction target.** The single new home for the fragment, most
  commonly a function reachable by every occurrence site (Extract Function),
  a class that owns both the shared data and the shared behaviour (Extract
  Class), a shared superclass method reached by moving identical code up an
  inheritance hierarchy (Pull Up Method or Pull Up Field), or an overridable
  hook when the occurrences share an outer shape but differ in one or two
  steps (Template Method, discussed in the `template-method` entry).
- **The call sites.** What the former occurrence sites become after
  extraction, each one replaced by a call into the extraction target, with
  its own variation points passed as arguments or resolved by dispatch.

## 6. ASCII structure diagram

```
Before. fragment duplicated at three occurrence sites

  +------------------+   +------------------+   +------------------+
  |  Occurrence A    |   |  Occurrence B    |   |  Occurrence C    |
  |  validate email  |   |  validate email  |   |  validate email  |
  |  (regex inline)  |   |  (regex inline,  |   |  (regex inline,  |
  |                  |   |   slightly diff) |   |   copy-pasted)   |
  +------------------+   +------------------+   +------------------+
        each copy edited independently, drifting apart over time


After. single extraction target, call sites replace occurrences

  +------------------+   +------------------+   +------------------+
  |  Call site A     |   |  Call site B     |   |  Call site C     |
  |  isValidEmail(x) |   |  isValidEmail(x) |   |  isValidEmail(x) |
  +--------+---------+   +--------+---------+   +--------+---------+
           \                      |                      /
            \                     |                     /
             v                    v                    v
                +--------------------------------------+
                |         isValidEmail(address)         |
                |   (the single authoritative rule)     |
                +--------------------------------------+
```

## 7. Dynamics

The dynamics of this smell describe a process over time, the drift of copies
apart from one another, followed by the process of resolving it.

```
Time 1. Fragment F is written once, at occurrence site A.

Time 2. A new requirement, similar to A's, arrives. Under deadline pressure,
         F is copied to occurrence site B and edited in place, rather than
         extracted and called from B. F(A) and F(B) are now near-identical.

Time 3. F(A) is patched, to fix a bug or add a case. F(B) is not touched,
         because the person patching F(A) does not know F(B) exists, or
         does not have time to hunt down every copy.

Time 4. F(A) and F(B) have now diverged in a way nobody decided on purpose.
         A third occurrence, F(C), is created the same way F(B) was.

Time 5, the fix, once dimension 4's applicability holds. The variation
         points across F(A), F(B), F(C) are identified. A single extraction
         target F is written that parameterises or dispatches on exactly
         those variation points. Each occurrence site is replaced by a call
         to F. Divergences discovered during extraction are resolved
         explicitly, as a deliberate decision, rather than left as silent
         drift.

Time 6. A future change to the rule is made once, in F, and every call site
         picks it up automatically on the next deploy.
```

The dynamics diagram makes explicit the two different kinds of cost this
smell produces. The cost before the fix is silent and grows with every
independent edit to any one copy. The cost at the fix is visible, a one-time
effort to reconcile the divergences honestly rather than average over them.

## 8. Implementation variants

The mechanical fix for duplicate code depends on where the duplication sits
and how the occurrences vary.

- **Extract Function, for duplication within or across the same scope.** The
  most common case, a fragment of statements is lifted into a named function,
  and each occurrence site becomes a call. Fowler's second edition renamed
  this refactoring from Extract Method to Extract Function to reflect that it
  applies whether or not the surrounding code is inside a class
  ([refactoring.com catalog](https://refactoring.com/catalog/), verified
  2026-08-02).
- **Extract Class, for duplication of both data and behaviour together.**
  When the same group of fields plus the methods that operate on them recur
  in more than one class, the group is lifted into its own class, and the
  original classes hold a reference to an instance of it instead of
  duplicating the fields and methods (`refactoring.com`, verified
  2026-08-02).
- **Pull Up Method and Pull Up Field, for duplication across sibling
  subclasses.** When two subclasses of the same superclass carry an
  identical method or field, moving it up to the superclass removes the
  duplication and makes it available to every current and future subclass in
  one place (`refactoring.com`, verified 2026-08-02).
- **Template Method, for near-identical algorithms that share an outer shape
  but differ in specific steps.** Rather than parameterising a single
  extracted function with flags for every point of variation, the shared
  skeleton is written once in a base class or higher-order function, with the
  differing steps left as overridable hooks. See the `template-method` entry
  for the full treatment.
- **Strategy or a parameter object, for duplication driven by a small,
  closed set of behavioural variants.** When the variation points are
  themselves behaviours rather than data, extracting them as first-class
  objects or closures, one per variant, avoids the branching that a single
  parameterised function would otherwise accumulate. See the `strategy`
  entry.
- **Consolidate Conditional Expression, for duplicated logic scattered
  across several conditional branches that all lead to the same result.**
  This refactoring merges the separate conditions into one, then extracts the
  merged condition into a well-named function, addressing a specific shape of
  duplication that plain Extract Function on the branch bodies would miss.
- **Pushing the single source of truth to data, not code.** Some duplication
  is best resolved not by extracting a function at all, but by moving the
  duplicated rule into a single piece of configuration or a database
  constraint that every code path reads, rather than encoding the rule
  redundantly in each language or service that needs it. This is the right
  variant when the duplication crosses language or process boundaries in a
  way that a shared function cannot, for example the email-validation rule
  duplicated between a browser-side JavaScript check and a server-side Java
  check, where a single shared regex constant, generated into both from one
  source file, removes the duplication without requiring either side to call
  into the other's runtime.
- **Language-idiomatic variants.** In languages with first-class functions,
  the variation point that would otherwise require a Strategy class or a
  Template Method subclass is often just a closure passed as a parameter,
  which is the idiom used in the code examples below. In languages with
  strong metaprogramming or macro systems, some duplication removal is done
  at compile time rather than run time, generating the repeated boilerplate
  from a single declarative source rather than writing or calling it by
  hand. This is a legitimate variant but is out of scope for the examples
  here, which stay to ordinary function and class extraction.

## 9. Known production uses

- **PMD's Copy/Paste Detector (CPD).** A widely deployed static-analysis tool
  purpose-built to find duplicate code across a codebase. Its own
  documentation describes three successive detection algorithms across its
  history, an initial implementation based on Michael Wise's Greedy String
  Tiling variant, a later rewrite using the Burrows-Wheeler transform, and the
  current implementation using the Karp-Rabin string-matching algorithm, and
  states that it supports Java, JSP, C, C++, C#, Go, Kotlin, Ruby, Swift, and
  a range of other languages ([PMD CPD user documentation](https://docs.pmd-code.org/latest/pmd_userdocs_cpd.html),
  verified 2026-08-02). The Maven PMD plugin's `cpd` goal, which wires CPD
  into ordinary Maven builds, defaults its `minimumTokens` threshold to 100
  tokens before a match is reported, and supports Java, JavaScript, and JSP
  out of the box, with `ignoreLiterals` and `ignoreIdentifiers` options for
  tuning how strict a match must be ([Apache Maven PMD Plugin, cpd-mojo
  documentation](https://maven.apache.org/plugins/maven-pmd-plugin/cpd-mojo.html),
  verified 2026-08-02).
- **jscpd.** A copy-paste detector for JavaScript, TypeScript, and a large
  number of other source formats, shipped as both a TypeScript implementation
  and a newer, faster Rust rewrite. Its documentation states it uses the
  Rabin-Karp string-matching algorithm to locate duplicated code blocks
  across files, supports over 220 source formats including cross-format
  detection inside Vue single-file components, Svelte, Astro, and Markdown,
  and integrates with third-party CI tooling including GitHub Super Linter,
  Codacy, and MegaLinter ([jscpd GitHub repository](https://github.com/kucherenko/jscpd),
  verified 2026-08-02).
- **The refactoring-guru catalog of code smells.** An independently maintained
  educational reference that lists Duplicate Code as one of its cataloged
  smells alongside Fowler and Beck's original set, describing its causes as
  including independent work by multiple programmers, subtle duplication that
  is hard to detect because the code looks different while doing the same
  thing, and deadline pressure that favours copy-paste over abstraction, and
  prescribing Extract Method, Pull Up Field, Form Template Method, and
  extraction of a shared superclass as the remedies depending on where the
  duplication sits, within one class, across sibling subclasses, or across
  unrelated classes ([refactoring.guru, Duplicate Code](https://refactoring.guru/smells/duplicate-code),
  verified 2026-08-02). This source independently confirms, from a different
  angle than Fowler's book, that the fix depends on the structural location
  of the duplication, matching dimension 8 above.
- **The DRY principle as an organising rule in software teams.** Andy Hunt
  and Dave Thomas's formulation, "every piece of knowledge must have a
  single, unambiguous, authoritative representation within a system," from
  *The Pragmatic Programmer*, 1999, is cited across the industry as the
  underlying rationale for treating duplicate code as worth acting on, rather
  than duplication being cited as a rule in itself. Teams that reference DRY
  in code review are, in effect, invoking this smell by name ([Wikipedia,
  Don't repeat yourself](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself),
  verified 2026-08-02).

## 10. Consequences

Positive, when the smell is genuinely present and the applicability
conditions in dimension 4 hold.

- A change to the underlying rule or behaviour is made exactly once, and
  every caller picks it up automatically, removing the class of bug where one
  copy is patched and a sibling copy is missed.
- The codebase's line count and surface area shrink, which reduces the total
  amount a reader has to hold in mind to understand a given concept.
- A single, well-named home for a piece of logic documents intent in a way
  that scattered inline copies cannot, because the name of the extraction
  target becomes searchable and referenceable.
- Test coverage concentrates. A single extraction target needs one thorough
  set of tests, rather than the same edge cases needing to be re-verified at
  every occurrence site, discussed further in dimension 15.

Negative, especially when the smell is acted on prematurely or the extraction
is built from too small or too coincidental a sample.

- **The wrong abstraction.** An extraction built from two superficially
  similar fragments that are not actually the same concept accumulates
  parameters and conditionals as it is stretched to cover cases it was never
  designed for, eventually becoming harder to read and change than the
  original duplication was. Sandi Metz's account of this failure and its cost
  is the canonical treatment ([Sandi Metz, "The Wrong Abstraction"](https://www.sandimetz.com/blog/2016/1/20/the-wrong-abstraction),
  verified 2026-08-02).
- **Increased coupling.** Every call site now depends on the single
  extraction target, so a change made for one caller's benefit can silently
  break, or subtly change the behaviour of, every other caller, an effect
  that duplication would have prevented by construction.
- **Reduced local readability.** A reader of a single call site now has to
  follow an indirection to another file or another part of the same file to
  see what actually happens, rather than reading the full behaviour inline.
  For a test suite in particular, this cost is often judged not worth paying,
  as discussed in dimension 4's test-fixture exception.
- **A shared bug becomes a shared bug everywhere at once.** Where duplication
  contained a defect to the copies that happen to be exercised by a given
  code path, a single extraction target with a bug in it is now wrong for
  every caller simultaneously, which can turn a narrow, contained incident
  into a broad one.
- **Sunk-cost pressure to keep a bad extraction.** Once effort has gone into
  building a shared abstraction, there is a natural reluctance to abandon it
  even after it is clearly wrong, which is exactly the trap Metz's advice, to
  inline and start over, is written to counter ([Sandi Metz, "The Wrong
  Abstraction"](https://www.sandimetz.com/blog/2016/1/20/the-wrong-abstraction),
  verified 2026-08-02).

## 11. Failure modes and misuse

**Symptom.** A shared utility function has grown a long list of boolean flag
parameters, several of which are only meaningful in combination with certain
other flags, and the function body is a maze of conditionals branching on
those flags.
**Cause.** Duplication was removed by parameterising a single function to
cover every occurrence, including occurrences whose variation was in
behaviour rather than in a simple value, so each new caller with a slightly
different need added another flag instead of prompting a rethink of the
abstraction's shape.
**Fix.** Split the function back along its true variation points, using
Template Method or Strategy so that each variant is a separate, readable
unit rather than a branch inside one function, or, per Sandi Metz's guidance,
inline the shared function entirely and let callers diverge again until a
cleaner shared shape becomes visible ([Sandi Metz, "The Wrong Abstraction"](https://www.sandimetz.com/blog/2016/1/20/the-wrong-abstraction),
verified 2026-08-02).

**Symptom.** Two services in different languages, or two layers of the same
application, both implement the same validation or business rule, and over
time a customer report reveals the two rules now accept, or reject, different
inputs.
**Cause.** The duplication crossed a language, process, or deployment
boundary that a single shared function cannot cross, and no other mechanism,
a shared schema, a shared configuration file, a generated constant, was put
in place to keep the two definitions synchronised, so each was edited
independently over time.
**Fix.** Identify the single source of truth for the rule and generate, or
otherwise mechanically derive, every other representation of it from that
source, rather than hand-maintaining parallel copies. Where generation is not
practical, add an automated cross-check, a test that asserts the two
representations agree on a shared set of example inputs, so drift is caught
at build time rather than by a customer.

**Symptom.** A clone-detection tool such as CPD or jscpd reports hundreds of
duplicate blocks, and the team either ignores the report entirely because
acting on all of it seems impractical, or spends a sprint mechanically
extracting every flagged block regardless of whether the flagged fragments
share real intent.
**Cause.** Treating a clone detector's output as a to-do list rather than as
a starting point for judgement. A textual detector finds identical or
near-identical tokens. It cannot tell coincidental similarity from shared
domain knowledge, which is exactly the distinction dimension 4 draws between
worth fixing and not worth fixing.
**Fix.** Use the detector's report as a triage input, then apply the
applicability criteria from dimension 4 to each flagged cluster by hand,
extracting only the clusters that encode a real, changeable decision with a
plausible third occurrence or more, and explicitly marking, in the tool's own
suppression mechanism where one exists, the clusters judged to be
coincidental or intentionally independent.

**Symptom.** A method extracted to remove duplication is called from a dozen
sites, and a bug fix intended for one caller's edge case silently changes
behaviour for the other eleven, discovered only when an unrelated feature's
tests start failing.
**Cause.** The extraction was built without an explicit inventory of every
call site's actual requirements, so a change made with only the reporting
caller in mind was applied to a shared function whose other callers had
requirements the person making the change did not know about.
**Fix.** Before changing a widely shared extraction, enumerate its call sites
and confirm the change is correct for all of them, not only the one that
prompted the change. If callers have started to diverge in what they need
from the shared function, that divergence is itself evidence the extraction
should be split, per the first failure mode above.

## 12. Trade-off matrix

Compared against three named alternatives to deduplicating. leaving the
duplication in place, choosing Template Method specifically, and choosing
Strategy specifically.

| Force | Extract Function/Class (general dedup) | Leave duplication in place | Template Method | Strategy |
|---|---|---|---|---|
| Maintenance cost on future change | Lowest, one edit reaches every caller | Highest, every copy must be found and edited | Low for the shared skeleton, isolated for each variant step | Low for the shared skeleton, isolated for each variant behaviour |
| Coupling introduced | Every caller now depends on one shared definition | None, callers stay fully independent | Callers coupled through inheritance from a common base | Callers coupled through a shared interface, not inheritance |
| Risk of the wrong abstraction | High if built from fewer than three real, non-coincidental instances | None, by definition | Lower, because the skeleton stays fixed and only hook steps vary | Lower, because each strategy is a separate, independently testable unit |
| Best fit for the shape of variation | A single value or a small closed set of values differs between occurrences | Variation is unknown or still forming | The outer algorithm shape is identical, only specific steps differ | The variation is itself a swappable behaviour, chosen at runtime or per caller |
| Readability at the call site | High, one function name replaces N inline copies | Lower, reader must trust that copies agree, or check | Moderate, reader follows into the base class to see the skeleton | Moderate, reader follows into the strategy interface to see the contract |
| Cost to reverse if wrong | Moderate, inline the function back at each call site | None to reverse, nothing was changed | Higher, requires restructuring the inheritance hierarchy | Lower, requires only swapping the injected strategy or adding a new one |

## 13. Related and incompatible patterns

- **Extract Function and Extract Class** are the direct refactoring moves this
  smell resolves into for exact or near-exact duplication confined to a
  single scope or a single group of data plus behaviour. They compose
  directly with this entry and are usually the first refactoring reached for.
- **Template Method** composes with this smell when the duplicated fragments
  share an outer algorithmic shape but differ in specific steps. Extracting a
  single flat function for such cases tends to produce the flag-parameter
  failure mode described in dimension 11, so Template Method is preferred
  once that shape is recognised. See the `template-method` entry.
- **Pull Up Method** composes with this smell specifically when the
  duplication sits in sibling subclasses of a shared superclass, moving the
  identical method or field up one level rather than extracting it sideways
  into a new, unrelated helper.
- **Strategy** composes with this smell when the variation point across
  occurrences is a behaviour rather than a value, and is generally preferred
  over a heavily flag-parameterised Extract Function once the number of
  variants or their internal complexity grows past a small handful. See the
  `strategy` entry.
- **The DRY principle** is the underlying rationale most often invoked when
  arguing this smell should be fixed, but DRY is a principle about knowledge,
  not about tokens, and citing it to justify extracting two coincidentally
  identical fragments that encode unrelated decisions is a misapplication of
  the principle it claims to follow ([Wikipedia, Don't repeat yourself](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself),
  verified 2026-08-02).
- **AHA, Avoid Hasty Abstractions**, and the Rule of Three are the two named
  counter-pressures against this smell, not incompatible with it so much as a
  timing discipline on when to act on it. Both hold that acting too early,
  on too few instances, produces worse code than tolerating the duplication a
  while longer ([Kent C. Dodds, "AHA Programming"](https://kentcdodds.com/blog/aha-programming);
  [Wikipedia, Rule of three](https://en.wikipedia.org/wiki/Rule_of_three_(computer_programming)),
  both verified 2026-08-02).
- **Shotgun Surgery**, a separate code smell where a single conceptual change
  requires editing many unrelated places, is the failure mode that
  unresolved duplication produces over time. A codebase riddled with
  duplicate code is, from the perspective of the person making a change, a
  codebase suffering from shotgun surgery, and fixing the duplication is
  often the direct fix for that smell too.
- **Speculative Generality**, another separate code smell describing
  abstractions built for imagined future needs that never arrive, is the
  smell that an over-eager fix for duplicate code most often produces,
  because a shared extraction built to cover every conceivable future
  variant, rather than the variants that actually exist today, is
  speculative generality wearing the disguise of deduplication.

## 14. Refactoring path in and out

Introducing the fix, from duplicated code to a single shared home.

1. Confirm the applicability conditions from dimension 4 hold. At least three
   real, non-coincidental occurrences, encoding the same decision, with a
   plausible future change to that decision.
2. Enumerate every occurrence site and, for each, note exactly how it differs
   from the others. This inventory becomes the list of variation points the
   extraction must account for, and doing it explicitly is what prevents the
   flag-parameter failure mode from dimension 11.
3. Choose the extraction shape from dimension 8 based on the shape of the
   variation. A single value differing calls for Extract Function with a
   parameter. A shared algorithm skeleton with differing steps calls for
   Template Method. A swappable behaviour calls for Strategy.
4. Write the extraction target with a test suite that covers every
   occurrence site's current behaviour, including the differences just
   inventoried, before touching any call site. This is the safety net that
   makes the following step mechanical rather than risky.
5. Replace each occurrence site with a call into the extraction target, one
   occurrence at a time, running the existing test suite after each
   replacement, per the Extract Function refactoring's own mechanics
   ([refactoring.com catalog](https://refactoring.com/catalog/), verified
   2026-08-02).
6. Where the inventory from step 2 revealed the copies had already silently
   diverged, in a way nobody intended, surface that divergence explicitly as
   a decision for the team. Do not average it away silently inside the new
   extraction.

Removing the fix, when an extraction has become the wrong abstraction and
Metz's advice applies.

1. Recognise the symptom, a shared function or class with a long or growing
   list of conditional flags, or a base class whose subclasses increasingly
   override or bypass its shared behaviour rather than reusing it.
2. Pick one caller of the shared abstraction, inline the abstraction's
   current behaviour at that one call site, ignoring the flags or branches
   that do not apply to this caller, and delete the now-unused code path from
   the inlined copy.
3. Repeat for each caller, one at a time, running tests after each inline,
   until every caller has its own local copy of only the behaviour it
   actually needs.
4. Once every caller has been inlined, delete the original shared
   abstraction. The codebase is now back to duplicate code, deliberately, as
   a known and accepted starting point, per Metz's guidance that the fastest
   way forward is back ([Sandi Metz, "The Wrong Abstraction"](https://www.sandimetz.com/blog/2016/1/20/the-wrong-abstraction),
   verified 2026-08-02).
5. Let the now-separate copies evolve independently until a new, truer shape
   of shared behaviour becomes visible from real requirements, then reapply
   the refactoring-in path above from a better-informed starting point.

## 15. Testing and verification

Removing duplicate code by extraction makes one thing distinctly easier to
test. Once N occurrence sites collapse into a single extraction target, the
target's edge cases, empty input, boundary values, error paths, need to be
tested exactly once, and every call site inherits that coverage for free,
rather than each occurrence site needing its own duplicated set of test cases
to reach the same confidence.

What becomes harder is verifying that the extraction is actually equivalent
to every occurrence it replaced, particularly for near-duplicates whose small
differences might encode an intentional behavioural distinction rather than
an accidental one. The refactoring path in dimension 14 addresses this
directly, by writing the extraction target's tests from the union of every
occurrence site's existing test coverage before any call site is touched, so
that a behavioural regression at any one call site is caught immediately
rather than discovered later in production.

Characterization tests, tests written against the current, possibly
undocumented behaviour of existing duplicated code before it is touched, are
the standard technique for the case where the occurrence sites have no
existing test coverage at all. Writing a characterization test for each
occurrence site, capturing its actual current behaviour including any subtle
divergence from its siblings, before extracting, turns an otherwise risky
refactor into one with a clear, mechanical safety net. Any test failure after
extraction identifies exactly which divergence was lost.

Test suites themselves are a documented exception to reflexive deduplication,
discussed in dimension 4. Many teams deliberately tolerate duplicated setup
code across individual test cases because a test that can be read and
understood in full without following an indirection into a shared fixture is,
for the specific purpose of a test, more valuable than a test suite with zero
duplication. This is a judgement call about the priorities of test code
specifically, distinct from the general case, and worth stating explicitly in
a team's own testing conventions rather than assumed silently.

## 16. Observability signals

Duplicate code is, by nature, a static property of source rather than a
runtime behaviour, so the primary observability signal is a build-time
metric, not a production dashboard metric.

- **Duplication percentage or duplicate block count, reported by a
  clone-detection tool run in CI.** Tools such as PMD CPD and jscpd both
  produce machine-readable reports, XML, CSV, JSON, or SARIF depending on the
  tool, suitable for tracking as a trend over time and for failing a build
  when a newly introduced block exceeds a team's chosen threshold
  ([PMD CPD documentation](https://docs.pmd-code.org/latest/pmd_userdocs_cpd.html);
  [jscpd repository](https://github.com/kucherenko/jscpd), both verified
  2026-08-02).
- **A rising trend in duplication percentage over successive releases,
  tracked rather than eyeballed once.** A single snapshot of a duplication
  report says little on its own. A trend that climbs release over release is
  the signal that copy-paste is becoming the team's default move under time
  pressure, worth raising in retrospective rather than waiting for a
  production incident to notice.
- **Bug reports whose fix requires touching more than one file for what
  should be a single logical change.** This is a lagging, human-observed
  signal rather than a metric a dashboard can compute directly, but it is the
  clearest evidence that duplication is causing real cost, and a useful
  practice is to note, in the pull request that fixes such a bug, how many
  separate copies had to be patched, so the pattern becomes visible over time
  in code review history even without a dedicated tool.
- **Code review comments repeatedly pointing at the same block of logic
  across unrelated pull requests.** A reviewer noticing that a block looks
  like the validation logic in a different module, more than once, across
  different authors and different pull requests, over a period of weeks, is
  an informal but reliable signal that a real, changeable decision has been
  duplicated and is worth extracting.

## 17. Security and privacy implications

Duplicate code carries a specific, well-documented security cost. Wikipedia's
summary of the topic states plainly that when duplicated code contains a
security vulnerability, vulnerabilities replicate across copies, meaning a
single flaw discovered and patched in one occurrence can remain live and
exploitable in every sibling copy that was not independently found and fixed
([Wikipedia, Duplicate code](https://en.wikipedia.org/wiki/Duplicate_code),
verified 2026-08-02). This is a direct, observable consequence of the
maintenance-cost force from dimension 3, made concrete for the specific case
where the thing left unpatched is a vulnerability rather than an ordinary
bug. A security-relevant fragment, an authentication check, an input
sanitisation routine, an access-control decision, is exactly the kind of
logic where the applicability conditions in dimension 4 are almost always
met, because such logic encodes a decision that is both critical and likely
to need revision as new threats or requirements are discovered, and the
consequence of an unpatched copy is materially worse than an unpatched
ordinary bug. Teams auditing security-sensitive code paths should treat any
duplicated instance of authentication, authorisation, cryptographic, or input
validation logic as a priority extraction target regardless of whether the
Rule of Three's threshold of three occurrences has technically been reached,
because the cost asymmetry between a missed patch in ordinary logic and a
missed patch in security logic justifies acting earlier than the general
rule would otherwise suggest.

Beyond the vulnerability-replication risk, duplicated data-handling code, for
example two separate implementations of a routine that redacts or encrypts
personally identifiable information before logging, carries a privacy-specific
version of the same problem. A change to a data-retention rule, or to which
fields count as sensitive, applied to one copy and not the other, can result
in personal data being logged, retained, or transmitted in one code path
while correctly protected in another, an inconsistency that is often only
discovered during a compliance audit or, worse, a breach investigation, well
after the divergence occurred.

## 18. References

1. Martin Fowler, *Refactoring. Improving the Design of Existing Code*,
   2nd edition, Addison-Wesley, 2018, Chapter 3, "Bad Smells in Code."
   Publication confirmed at [martinfowler.com/books/refactoring.html](https://martinfowler.com/books/refactoring.html),
   verified 2026-08-02.
2. Refactoring catalog, 2nd edition, listing Extract Function, Extract Class,
   Pull Up Method, Pull Up Field, and Pull Up Constructor Body.
   [refactoring.com/catalog](https://refactoring.com/catalog/), verified
   2026-08-02.
3. Wikipedia, "Duplicate code," covering causes, detection techniques, and
   the vulnerability-replication and privacy-risk consequences of
   duplication. [en.wikipedia.org/wiki/Duplicate_code](https://en.wikipedia.org/wiki/Duplicate_code),
   verified 2026-08-02.
4. Wikipedia, "Rule of three (computer programming)," attributing the rule to
   Don Roberts and its popularisation to Martin Fowler.
   [en.wikipedia.org/wiki/Rule_of_three_(computer_programming)](https://en.wikipedia.org/wiki/Rule_of_three_(computer_programming)),
   verified 2026-08-02.
5. Wikipedia, "Don't repeat yourself," citing Andy Hunt and Dave Thomas, *The
   Pragmatic Programmer*, 1999, and the definition that every piece of
   knowledge must have a single, unambiguous, authoritative representation
   within a system. [en.wikipedia.org/wiki/Don%27t_repeat_yourself](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself),
   verified 2026-08-02.
6. Sandi Metz, "The Wrong Abstraction," 2016, on preferring duplication over
   a wrong abstraction and inlining as the fastest way back.
   [sandimetz.com/blog/2016/1/20/the-wrong-abstraction](https://www.sandimetz.com/blog/2016/1/20/the-wrong-abstraction),
   verified 2026-08-02.
7. Kent C. Dodds, "AHA Programming," 2020, on Avoid Hasty Abstractions and
   optimising for change over the absence of repeated tokens.
   [kentcdodds.com/blog/aha-programming](https://kentcdodds.com/blog/aha-programming),
   verified 2026-08-02.
8. PMD Copy/Paste Detector (CPD) user documentation, on its Karp-Rabin based
   detection algorithm and supported languages.
   [docs.pmd-code.org/latest/pmd_userdocs_cpd.html](https://docs.pmd-code.org/latest/pmd_userdocs_cpd.html),
   verified 2026-08-02.
9. Apache Maven PMD Plugin, cpd-mojo documentation, on the minimumTokens
   default of 100 and supported language values.
   [maven.apache.org/plugins/maven-pmd-plugin/cpd-mojo.html](https://maven.apache.org/plugins/maven-pmd-plugin/cpd-mojo.html),
   verified 2026-08-02.
10. jscpd repository documentation, on its Rabin-Karp based detection
    algorithm, supported formats, and CI integrations.
    [github.com/kucherenko/jscpd](https://github.com/kucherenko/jscpd),
    verified 2026-08-02.
11. refactoring.guru, "Duplicate Code," an independently maintained summary
    of the smell's causes and remedies, cross-checked against Fowler's
    catalog rather than used as a source of original prose.
    [refactoring.guru/smells/duplicate-code](https://refactoring.guru/smells/duplicate-code),
    verified 2026-08-02.

## Code examples

The three examples below show the same duplication, a slightly-varying
discount calculation copy-pasted across three call sites, and its resolution
via Extract Function with the variation points passed as parameters. Each
example was run against its own toolchain and its output is noted.

### TypeScript

```typescript
// Before, the same discount logic copy-pasted three times, each edited
// slightly for its own case, and already drifting apart.

function checkoutRegular(price: number): number {
  let discount = 0;
  if (price > 100) {
    discount = price * 0.1;
  }
  return price - discount;
}

function checkoutMember(price: number): number {
  let discount = 0;
  if (price > 100) {
    discount = price * 0.15; // members get a better rate
  }
  return price - discount;
}

function checkoutVip(price: number): number {
  let discount = 0;
  if (price > 50) { // VIP threshold silently drifted to 50
    discount = price * 0.15; // and this copy forgot the VIP-only 0.2 rate
  }
  return price - discount;
}

// After, the three variation points (threshold, rate) named explicitly,
// the shared calculation extracted once.

interface DiscountTier {
  readonly threshold: number;
  readonly rate: number;
}

const REGULAR: DiscountTier = { threshold: 100, rate: 0.10 };
const MEMBER: DiscountTier = { threshold: 100, rate: 0.15 };
const VIP: DiscountTier = { threshold: 50, rate: 0.20 };

function applyDiscount(price: number, tier: DiscountTier): number {
  const discount = price > tier.threshold ? price * tier.rate : 0;
  return price - discount;
}

function main(): void {
  const price = 120;
  console.log("regular", applyDiscount(price, REGULAR));
  console.log("member", applyDiscount(price, MEMBER));
  console.log("vip", applyDiscount(price, VIP));
}

main();
```

Run with `npx tsc --target es2020 --module commonjs duplicate-code.ts && node
duplicate-code.js`. Compiled and ran cleanly, producing this output.

```
regular 108
member 102
vip 96
```

### Python

```python
"""Before, the same email-validation rule duplicated across three call
sites, one of which quietly diverged from the other two.
"""

import re


def register_user(email: str) -> bool:
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if re.match(pattern, email) is None:
        return False
    return True


def update_billing_email(email: str) -> bool:
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if re.match(pattern, email) is None:
        return False
    return True


def invite_teammate(email: str) -> bool:
    pattern = r"^[^@]+@[^@]+$"  # drifted, no longer requires a dot
    if re.match(pattern, email) is None:
        return False
    return True


# After, a single authoritative rule, called from every occurrence site.

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return EMAIL_PATTERN.match(email) is not None


def register_user_fixed(email: str) -> bool:
    return is_valid_email(email)


def update_billing_email_fixed(email: str) -> bool:
    return is_valid_email(email)


def invite_teammate_fixed(email: str) -> bool:
    return is_valid_email(email)


if __name__ == "__main__":
    cases = ["a@b.com", "not-an-email", "a@b"]
    for case in cases:
        print(case, "->", is_valid_email(case))
```

Run with `python3 duplicate_code.py`. Executed cleanly, producing this
output.

```
a@b.com -> True
not-an-email -> False
a@b -> False
```

### Go

```go
// Before, three HTTP handlers each write the same JSON error envelope,
// copy-pasted, with the status-code handling starting to diverge.
//
// After, a single writeError helper, called from every handler, shown
// below since Go favours one authoritative implementation over comments
// documenting a since-deleted duplicate.

package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

type errorEnvelope struct {
	Error string `json:"error"`
	Code  int    `json:"code"`
}

// writeError is the single extraction target every handler now calls,
// replacing three copies of this same json.Marshal-and-write sequence.
func writeError(w http.ResponseWriter, status int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	body, _ := json.Marshal(errorEnvelope{Error: message, Code: status})
	_, _ = w.Write(body)
}

func createOrderHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeError(w, http.StatusMethodNotAllowed, "POST required")
		return
	}
	fmt.Fprintln(w, "order created")
}

func cancelOrderHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeError(w, http.StatusMethodNotAllowed, "POST required")
		return
	}
	fmt.Fprintln(w, "order cancelled")
}

func refundOrderHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeError(w, http.StatusMethodNotAllowed, "POST required")
		return
	}
	fmt.Fprintln(w, "order refunded")
}

func main() {
	fmt.Println("handlers registered, each sharing one writeError target")
}
```

Run with `go run duplicate_code.go`. Compiled and ran cleanly, producing this
output.

```
handlers registered, each sharing one writeError target
```

Java and Rust were not run for this entry. Both toolchains are present on
this machine per the repository's tool table, but the TypeScript, Python, and
Go examples above already cover three languages from the required set, one
functional-style closure-driven extraction (TypeScript), one
regex-configuration-driven extraction (Python), and one shared-helper
extraction in a language with no closures over mutable package state used
here (Go), so a fourth and fifth language were not added, per the
instruction to prefer depth of the required minimum over redundant breadth.
