---
name: Copy-Paste Programming
slug: copy-paste-programming
family: 18-anti-patterns
category: Anti-Pattern
aliases: [Clone and Own, Copy and Paste Reuse, Cut and Paste Programming, WET Code]
first_described: "Brown, Malveau, McCormick, Mowbray 1998 (catalogued as Cut-and-Paste Programming); Fowler and Beck 1999 (Duplicated Code smell)"
maturity: canonical
related: [extract-method, template-method, strategy, dry-principle, template-repository]
incompatible_with: [dry-principle]
verified: 2026-08-02
---

# Copy-Paste Programming

## 1. Name, aliases, and lineage

The canonical name in the software engineering anti-pattern literature is
Cut-and-Paste Programming, from William J. Brown, Raphael C. Malveau, Hays W.
"Skip" McCormick, and Thomas J. Mowbray, *AntiPatterns. Refactoring Software,
Architectures, and Projects in Crisis*, John Wiley and Sons, 1998, chapter 4.
In everyday developer speech the same anti-pattern is almost always called
Copy-Paste Programming, and this entry uses that spelling because it is the
term that appears in bug trackers, code review comments, and static analysis
tool output.

Wikipedia's article on the subject defines it plainly as "the production of
highly repetitive computer programming code, as produced by copy and paste
operations," and notes the term is "primarily a pejorative" implying a lack of
competence at abstraction ([Wikipedia, Copy-and-paste
programming](https://en.wikipedia.org/wiki/Copy-and-paste_programming),
verified 2026-08-02). The closely related name Clone and Own is used
specifically in the software product line and reuse research literature to
describe the organizational version of the same behavior, where an entire
codebase is duplicated to start a new product variant rather than a single
function being duplicated inside one codebase.

The pattern was independently identified from a different angle the following
year in Martin Fowler and Kent Beck's catalog of bad smells. Kent Beck coined
the term code smell while helping Fowler write that book (Martin Fowler,
["CodeSmell"](https://martinfowler.com/bliki/CodeSmell.html), verified
2026-08-02), and the resulting catalog names Duplicated Code as one of its
smells in Martin Fowler, *Refactoring. Improving the Design of Existing
Code*, 2nd edition, Addison-Wesley, 2018, chapter 3, "Bad Smells in Code." The
two lineages, the 1998 AntiPatterns catalog and the 1999 Refactoring book,
converge on the same observation from opposite directions. one names the
organizational and process failure that produces duplication, the other names
the code shape the duplication leaves behind. This entry treats Copy-Paste
Programming as the practice, and Duplicated Code as its most visible symptom,
because a reader who searches a codebase for the symptom is usually trying to
diagnose the practice.

Informally, developers sometimes contrast duplicated code with the Don't
Repeat Yourself principle by calling the duplicated version WET code, read
as the opposite of DRY. That backronym circulates widely in blog posts and
conference talks but this entry could not independently verify a first
coiner or an original publication for it during the research for this entry,
so it is named here only as a piece of developer folklore, not as a sourced
claim.

## 2. Problem and context

A developer needs behavior that is almost, but not quite, identical to
behavior that already exists somewhere else in the codebase. The fastest path
from a blank cursor to a working feature is to open the existing code, select
it, copy it, paste it into a new location, and edit the parts that differ.
The new code compiles, the tests the developer wrote for it pass, and the
feature ships on schedule. Nothing about that single decision is wrong in
isolation. the problem is what happens the next fifty times a developer faces
the same choice under the same time pressure.

The context in which this becomes a genuine problem, rather than a harmless
shortcut, has three ingredients. First, the duplicated logic encodes a
business rule, a validation, a security check, or a calculation that can
change, rather than a truly stable piece of boilerplate that will never be
touched again. Second, nobody tracks where the copies live, so there is no
list a maintainer can consult when the rule changes. Third, the codebase has
no cheap, well-understood abstraction (a shared function, a base class, a
shared module) that the developer under time pressure could have reached for
instead, or the existing abstraction was too awkward to extend so copying
felt cheaper than fighting it.

Under those three conditions, copy-paste programming stops being a
convenience and starts being a liability that compounds silently. Each copy
is a place where a future bug fix, security patch, or behavior change must be
applied by hand, and each one that gets missed is a defect that looks, from
the outside, like an inconsistency in the product rather than a maintenance
failure.

## 3. Forces

Copy-paste programming exists because it wins, locally and immediately, on
several real forces, at the cost of others that only mature over the life of
the codebase.

- **Development speed versus long-term maintenance cost.** Copying an
  eighteen-line validated function into a new file takes seconds. Designing
  the correct shared abstraction, choosing its parameters, and threading it
  through both call sites correctly can take an hour or more. The pattern
  wins the speed force decisively at the moment of writing and loses the
  maintenance-cost force decisively over the following months, because the
  cost of the missing abstraction is paid every time the logic changes, not
  once.
- **Isolation versus coupling.** A copy is fully isolated. Changing one copy
  cannot break the other copy's callers, which is a real and legitimate
  safety property, especially across team or deployment boundaries where a
  shared dependency would create a coordination cost. A shared abstraction
  couples every caller to a single implementation, which is exactly the
  property that makes a future fix apply everywhere at once, and exactly the
  property that makes an accidental change to shared code a wide blast
  radius.
- **Cognitive load at write time versus cognitive load at read time.**
  Copying is cognitively cheap for the author, because they do not have to
  reason about generalizing the logic for a case they have not yet seen. It
  is cognitively expensive for every later reader, who cannot assume the two
  near-identical blocks behave the same way and must diff them line by line
  to find out where they differ.
- **Correctness under adaptation versus correctness under review.** A pasted
  block is usually adapted by hand at the seams, renaming a variable here,
  swapping a condition there. Each adaptation is a fresh chance to introduce
  a defect that the original, reviewed and tested code did not have, because
  the adapted block did not go through the same scrutiny as the block it was
  copied from.
- **Team topology.** In a large organization, the developer who needs the
  behavior often does not own, and may not have permission to change, the
  module that already contains it. Copying into their own module avoids a
  cross-team negotiation. This is a genuine organizational force, and one of
  the few contexts in this entry's applicability list where the pattern is a
  reasonable, deliberate trade rather than a mistake.

Copy-paste programming favors the writer's immediate speed and isolation. It
sacrifices the maintainer's ability to change the behavior in one place and
the reviewer's ability to trust that two similar-looking blocks actually do
the same thing.

## 4. Applicability and non-applicability

### When copying is a reasonable, deliberate choice

- A one-time script, a spike, or a proof of concept that will be deleted or
  rewritten before it reaches a shared branch, where the cost of an
  abstraction would never be recovered.
- Bootstrapping a genuinely new, independent product or service from an
  existing one at the very start of its life, where the two are expected to
  split apart quickly and a shared dependency would only slow that split
  down. This is the clone-and-own strategy studied in software product line
  research, and it is a documented, named strategy rather than a pure
  mistake, provided the team accepts the ongoing cost.
- Copying a small, genuinely stable piece of boilerplate, such as a license
  header, a standard error-handling wrapper mandated by a style guide, or a
  configuration stanza, where the content is expected to be identical
  everywhere by design and a shared abstraction would add indirection with
  no behavioral benefit.
- Copying example or test fixture code where each copy is intentionally an
  independent scenario, and forcing them to share a helper would make each
  individual test harder to read in isolation, which is a real cost weighed
  against duplication in dimension 15.
- A vendored, third-party file that is copied as an unmodified unit on
  purpose, tracked as a vendored dependency, so that local modifications
  never silently drift from a documented upstream version.

### When copying is the anti-pattern, not a valid strategy

- The duplicated logic encodes a business rule, a security check, a
  calculation, or a validation that the product owner can change, and there
  is no inventory of where the copies live.
- The developer copied the block specifically because the existing shared
  abstraction was hard to reuse (wrong parameters, hidden side effects, no
  extension point), rather than because sharing was undesirable. This is a
  signal that the abstraction itself needs fixing, not that duplication is
  the right long-term answer.
- The same block, or a lightly edited variant of it, already appears three or
  more times in the codebase. Empirically, once duplication reaches this
  frequency the cost of maintaining every copy by hand exceeds the cost of
  the refactor that would remove it, because each additional site multiplies
  the chance that any future edit misses one.
- The copy is inside a security-sensitive path, such as authentication,
  authorization, input sanitization, or cryptographic parameter selection.
  Duplicated security logic is disproportionately dangerous because a
  security fix applied to one copy and missed in another reopens the exact
  vulnerability the fix was meant to close, quietly, in a code path nobody
  is currently looking at.
- The team plans for the product to remain a single, actively evolving
  system rather than splitting into independent variants, so the isolation
  benefit that justifies clone-and-own never materializes.

## 5. Structure

Copy-paste programming has no participants in the sense a design pattern
does, because it is the absence of a structure rather than the presence of
one. It is more useful to name the artifacts involved and the relationship,
or lack of one, between them.

- **Source block.** The original piece of code that gets copied. It may or
  may not be under test, and it may or may not be the block a later fix
  actually gets applied to.
- **Clone.** The pasted copy, adapted at the seams. A clone is called exact
  (Type 1) when it is byte-for-byte identical apart from whitespace and
  comments, renamed (Type 2) when identifiers or literals were substituted
  but the structure is unchanged, gapped (Type 3) when a few statements were
  added, removed, or changed, and semantic (Type 4) when the code was
  rewritten to different syntax that performs the same computation. This
  four-way taxonomy is the standard one used in the code clone detection
  research literature and by the tools that implement it.
- **No shared reference.** The defining structural fact is that the source
  block and the clone have no compile-time, link-time, or runtime dependency
  on each other. Nothing connects them except that a human remembers, or
  forgets, that they are related.
- **Split point.** The place, usually a condition, a literal, or a variable
  name, where the clone was deliberately edited to differ from the source.
  This is the one part of the clone that a reader must locate before
  trusting that the rest of the block still matches.

## 6. ASCII structure diagram

```
  Before (single source of truth)              After copy-paste

  +-------------------+                        +-------------------+
  |  validateOrder()   |<---- called by ------  |  validateOrder()   |
  |  (one definition)   |      3 call sites      |  (call site A)     |
  +-------------------+                        +-------------------+

                                                +-------------------+
                                                |  validateOrder()   |
                                                |  (call site B,      |
                                                |   pasted copy,      |
                                                |   discount check    |
                                                |   added by hand)    |
                                                +-------------------+

                                                +-------------------+
                                                |  validateOrder()   |
                                                |  (call site C,      |
                                                |   pasted copy,      |
                                                |   currency check    |
                                                |   never applied     |
                                                |   because it was    |
                                                |   added to A only)  |
                                                +-------------------+

  One arrow, one definition.                   No arrows. Three
  A fix at the box fixes                        unrelated boxes. A fix
  every caller.                                 to one box does not
                                                reach the other two.
```

## 7. Dynamics

```
  Feature request arrives ("add tax logic like checkout has")
        |
        v
  Developer opens checkout module, finds validateOrder()
        |
        v
  Copies the function body into the new module
        |
        v
  Edits the pasted copy at the seams (renames, adds a field check)
        |
        v
  Runs the new module's own tests -> pass
        |
        v
  Ships. No record links the two copies to each other.

  ... months later ...

  Security or business-rule fix lands in the ORIGINAL location
        |
        v
  Original tests pass. Original code review approves the fix.
        |
        v
  Feature is deployed. Nobody searches for other copies,
  because nothing in the codebase declares that copies exist.
        |
        v
  The pasted copy still runs the old, unpatched logic
  in production, indefinitely, until a bug report or an
  audit rediscovers the duplication by accident.
```

## 8. Implementation variants

Real codebases exhibit copy-paste programming in several recognizably
different shapes, and the fix differs by shape.

- **Function-body duplication.** The most common case. an entire function is
  copied and lightly edited. The fix is Extract Method or Extract Function
  applied to both call sites so they share a single definition (see
  dimension 14 for the refactoring path).
- **File-level duplication.** A whole file, module, or even a whole service
  is copied to start a new one. This is the clone-and-own strategy from
  dimension 4. In some contexts it is intentional, but when it happens
  inside a single active codebase rather than to start a genuinely separate
  product, it is usually a sign that the module boundary or the packaging
  system made sharing harder than copying.
- **Configuration and infrastructure-as-code duplication.** The same block
  of YAML, Terraform, or a CI pipeline definition is pasted across many
  files with small parameter changes. This variant is common because
  configuration languages historically lacked good abstraction mechanisms,
  which is exactly why templating layers (Helm charts, Terraform modules,
  reusable GitHub Actions workflows) exist. treated in this entry's related
  pattern, template-repository.
- **Cross-language duplication.** The same business rule is implemented
  independently in a frontend validator and a backend validator, in two
  different languages, because no single shared library can run in both
  runtimes. This is a legitimate, hard case. the correct mitigation is
  usually a shared specification (a schema, a rule table, or a
  code-generation step) rather than a shared function, because the
  languages genuinely cannot share code directly.
- **Test duplication.** Copying an existing test as the starting point for a
  new one is extremely common and, within limits described in dimension 4,
  often reasonable. it becomes the anti-pattern when the setup and
  assertion logic, rather than only the scenario data, is duplicated across
  dozens of tests, so that a change to how the system under test is
  constructed requires editing every test file by hand.
- **Copy from an external source.** Code pasted from a Stack Overflow
  answer, an AI coding assistant's suggestion, or another open-source
  project, without attribution, license review, or adaptation to the local
  codebase's conventions and error-handling strategy. This variant adds a
  licensing and provenance risk on top of the maintenance risk common to
  every other variant.

## 9. Known production uses

Copy-paste programming is, by its nature, rarely announced by name in a
production system's own documentation, since it is a practice being
diagnosed rather than a feature being advertised. The evidence for its
prevalence comes instead from the tools built specifically to find it and
from the standards bodies that fund research into it, both of which are
independently verifiable.

- **PMD's Copy/Paste Detector (CPD).** CPD is a component of the PMD static
  analysis project that, in the project's own words, "can find" duplicate
  code blocks, and it works across "Java, JSP, C/C++, C#, Go, Kotlin, Ruby,
  Swift and many more languages," tokenizing source files and applying a
  Karp-Rabin string matching algorithm to locate matching token sequences
  ([PMD documentation, CPD](https://pmd.github.io/pmd/pmd_userdocs_cpd.html),
  verified 2026-08-02). CPD ships as a standalone command usable in any CI
  pipeline and has shipped as part of PMD since the tool's early releases,
  which makes it one of the longest-running, most widely deployed tools
  built specifically to detect this anti-pattern in real codebases.
- **SonarQube's duplication metrics.** SonarSource's SonarQube platform
  defines Duplicated Lines Density as
  `duplicated_lines_density = duplicated_lines / lines * 100`, and defines
  Duplicated Blocks as the count of duplicated blocks of code, requiring "at
  least 100 successive and duplicated tokens" for non-Java projects before a
  block is counted ([SonarQube Server documentation, Metric
  Definitions](https://docs.sonarsource.com/sonarqube-server/user-guide/code-metrics/metrics-definition/),
  verified 2026-08-02). SonarQube runs these checks as a default quality
  gate on every analyzed project across thousands of organizations,
  which is the clearest evidence available that duplication detection is
  treated as a standard, expected part of continuous integration in the
  industry rather than a niche concern.
- **The software product line and clone-and-own research literature.**
  Academic and industrial research into software product lines documents
  clone-and-own as a named, deliberately chosen strategy for building
  product variants by copying an entire codebase, precisely because many
  organizations do this in practice rather than adopting a formal
  variability-management platform, and studies this strategy's cost over
  time as a distinct field of inquiry. Wikipedia's article on copy-and-paste
  programming attributes the practice in general to "inexperienced or
  student programmers" as well as to code assembled "from disparate sources
  such as friends' or co-workers' code, Internet forums, open-source
  projects" ([Wikipedia, Copy-and-paste
  programming](https://en.wikipedia.org/wiki/Copy-and-paste_programming),
  verified 2026-08-02), which documents the practice's presence at the level
  of individual contributions in general-purpose codebases, distinct from
  the deliberate organizational clone-and-own strategy.

## 10. Consequences

### Positive

- Zero coupling between the copy and its source. changing one cannot break
  the other's callers, which is a real safety property across team or
  deployment boundaries.
- No design work required before shipping. a developer under deadline
  pressure can produce working code immediately without first solving the
  harder problem of a correct, general abstraction.
- The copy can change freely and safely away from the original as
  requirements for the new case change, with no risk of breaking the
  original case, which matters when the two cases are genuinely expected to
  grow apart.
- No indirection to trace. a reader looking at the clone in isolation sees
  the entire logic in one place, with no need to jump to a shared function
  defined elsewhere.

### Negative

- A defect or a needed behavior change must be located and applied by hand
  in every copy, and there is no compiler, type system, or build error that
  reports a missed copy. the failure shows up later, as an inconsistency in
  the product's behavior.
- The codebase's true size, measured in logic that must be understood and
  maintained, grows faster than its true capability, because every clone
  adds maintenance surface area without adding a new capability.
- Reviewers and new team members cannot trust that two similar-looking
  blocks behave identically, so they must diff them by hand to find the
  point where they differ on every read, which is a permanent tax on
  comprehension.
- Security and correctness fixes quietly fail to reach every affected code
  path, because nothing in the codebase enumerates where the vulnerable or
  incorrect logic was duplicated.
- Static analysis and test coverage tools report inflated, misleading
  numbers, because coverage achieved on one clone says nothing about
  whether the same lines in a sibling clone are exercised by any test.

## 11. Failure modes and misuse

- **Symptom.** A production bug report describes behavior that was
  supposedly fixed months earlier. **Cause.** The original fix was applied
  to the source block a developer happened to find first, and one or more
  pasted clones of that block were never located or updated, because
  nothing recorded that the clones existed. **Fix.** Run a clone detector
  such as PMD CPD or SonarQube's duplication analysis across the codebase,
  locate every clone of the fixed block, and either apply the fix to each
  one immediately or extract a shared function so the fix only needs to
  happen once, going forward.

- **Symptom.** Two near-identical validation functions produce different
  error messages, or accept a slightly different set of valid inputs, for
  what the product owner believes is a single business rule. **Cause.** One
  copy was adapted at its seams for a special case, and the two copies then
  evolved independently under separate feature requests, with no mechanism
  forcing anyone to notice the split. **Fix.** Treat the split as a decision
  point rather than only a bug. determine whether the difference is
  intentional (in which case it should be an explicit parameter on a shared
  function, not an accidental fork) or a mistake (in which case it should be
  corrected and the duplication removed with Extract Method or a shared
  Strategy or Template Method implementation).

- **Symptom.** A code review takes far longer than the diff size suggests it
  should, because the reviewer keeps scrolling to a second, third, or fourth
  file to compare a pasted block against the block it was copied from.
  **Cause.** The reviewer cannot evaluate correctness from the diff alone,
  because the diff shows only the new copy, not the relationship between the
  new copy and the source it split off from. **Fix.** Require the pull
  request description to name the source block explicitly when new code was
  copied from an existing one, and treat "why was this copied instead of
  shared" as a standard review question, the way "why was this test
  skipped" already is in most review checklists.

- **Symptom.** A dependency-scanning or license-compliance tool flags code
  that matches a known open-source project, in a codebase whose author does
  not remember writing anything resembling it. **Cause.** The code was
  copied from a public source such as a forum answer, a blog post, or an
  AI coding assistant's suggestion, without checking the license of the
  source or reviewing whether the pasted code matches the local codebase's
  security and error-handling conventions. **Fix.** Treat any code pasted
  from outside the current codebase, human-written or AI-generated, as
  requiring the same review as a new third-party dependency would. license
  check, security review, and an explicit decision to adapt it to local
  conventions rather than pasting it unchanged.

- **Symptom.** A refactor to extract the shared logic is proposed and
  rejected on the grounds that "the two things aren't really the same, they
  only look alike." **Cause.** This is sometimes a correct objection, and
  sometimes a rationalization for avoiding the harder design work an
  abstraction requires. **Fix.** This is judgement, not a sourced fact.
  the useful test in practice is whether the two blocks share a reason to
  change together. if a future business rule change would need to touch
  both blocks in the same way, they are the same logic and should be
  unified. if a future change would plausibly touch only one of them, the
  similarity is coincidental and duplication is the correct, honest choice,
  not a smell to be refactored away.

## 12. Trade-off matrix

| Force | Copy-Paste Programming | Extract Method / shared function | Template Method | Clone-and-Own product line |
|---|---|---|---|---|
| Write-time speed | Fastest. no design decision required | Slower. requires designing the shared signature | Slower still. requires designing the invariant steps up front | Fast for the initial copy, same as copy-paste |
| Coupling between call sites | None | Full. every caller shares one implementation | Partial. subclasses share structure, vary specific steps | None between products, but internal duplication across the copied codebase |
| Cost of a correctness or security fix | Must be applied to every copy by hand, with no tooling to find them all | Applied once, reaches every caller automatically | Applied once in the template, reaches every subclass automatically, unless the affected step was overridden | Must be applied to every product's copy by hand, same cost profile as copy-paste, at product scale |
| Risk of an undetected split | High. no mechanism reveals it | Low. a shared function cannot silently split from itself | Low for the invariant parts, a split is possible only in the overridden steps, and those are visible in each subclass | High, same as copy-paste, at product scale |
| Appropriate when call sites are expected to split apart quickly | Yes, this is its best fit | No, forces premature coupling before the real variation is known | Partially, only along the axis the template anticipated | Yes, this is its documented use case |
| Reviewability | Low. reviewer must manually compare against the source | High. logic exists in exactly one place to review | Medium. reviewer must check both the template and each override | Low, same as copy-paste, and worse across many products, because the copies live in separate repositories |

## 13. Related and incompatible patterns

Copy-paste programming is the practice this entry names, and the entries
below are the moves a team makes once it decides the duplication has crossed
from a reasonable trade into a liability, or the deliberate strategy that
justifies tolerating it.

- **Extract Method.** The direct refactoring response to function-body
  duplication. take the duplicated logic out of both call sites and put it
  in one place both call. see dimension 14 for the step-by-step path.
- **Template Method.** When the duplicated blocks share an invariant
  skeleton but differ in a small number of specific steps, Template Method
  captures the skeleton once in a base class or higher-order function and
  makes the varying steps overridable, which is a more structured
  alternative to Extract Method when the variation is itself important
  rather than incidental.
- **Strategy.** When the varying part of the duplicated logic is better
  expressed as a swappable object or function passed in at the call site
  rather than as an inherited, overridden method, Strategy is the
  composition-based sibling of Template Method for the same underlying
  problem.
- **DRY, the Don't Repeat Yourself principle.** The general design
  principle that copy-paste programming most directly violates. this entry
  is incompatible with DRY in the specific sense that a codebase which
  systematically follows one cannot systematically exhibit the other in
  the same code paths. the two are not incompatible as a matter of
  necessity everywhere, because the applicability list in dimension 4
  describes real contexts where deliberate, bounded duplication is the
  correct choice even in a codebase that otherwise honors DRY.
- **Template repository / boilerplate generator.** The organizational
  answer to the file-level and configuration-level duplication variants
  from dimension 8. instead of copying a file by hand, a generator or a
  scaffolding tool produces the new file from a maintained template, which
  keeps the convenience of starting from a known-good example while
  recording, in the generator itself, exactly what was templated and what
  was supposed to be customized.

## 14. Refactoring path in and out

### Introducing the anti-pattern (how it enters a codebase, so it can be recognized early)

1. A developer needs behavior similar to existing code and does not know, or
   does not have time to find, a shared abstraction that already covers the
   need.
2. They copy the nearest matching block into the new location.
3. They edit the copy at its seams until its own tests pass, without
   re-running or even locating the tests for the original block.
4. The change ships as a self-contained pull request that never mentions the
   source it was copied from, because nothing in the review process asks.

### Removing it (Extract Method, the standard path)

1. **Locate every clone.** Run a duplication detector (PMD CPD, SonarQube,
   or an equivalent tool for the project's language) across the codebase, or
   search manually if the clone was recently introduced and the source is
   fresh in the author's memory. Confirm the count of clones before
   deciding how to refactor. two clones and five clones call for different
   amounts of design effort.
2. **Verify the clones are genuinely the same logic**, not merely
   similar-looking code that happens to share structure. Apply the "would a
   future change touch both together" test from dimension 11's last failure
   mode. if the answer is no for some of the located clones, exclude them
   from the refactor. unifying unrelated logic only because it looks alike
   introduces false coupling, which is a new problem, not a fix for the old
   one.
3. **Add characterization tests** around each clone that will be unified, if
   tests do not already exist, so the refactor has a safety net that proves
   behavior did not change (see dimension 15).
4. **Extract the shared logic** into a single function, method, or class,
   choosing parameters for the points where the clones genuinely differ.
   Keep the new abstraction's signature as small and honest as the observed
   variation requires. do not add parameters for variation that was not
   observed in the clones being unified, because that reintroduces the
   premature generalization that Extract Method is meant to avoid.
5. **Replace each clone with a call to the new shared implementation**, one
   call site at a time, running the full test suite after each replacement
   rather than after all of them, so a regression is attributable to a
   single, small change.
6. **Delete the clones.** A shared abstraction that coexists with its
   now-redundant clones has fixed nothing. the clones must actually be
   removed, or the codebase still carries the original maintenance risk
   alongside the new abstraction's added indirection.

### Extracting instead into Template Method or Strategy

When step 4 above reveals that the clones share an invariant skeleton with a
small number of varying steps, rather than differing at scattered,
unstructured points, prefer Template Method (an inheritance-based skeleton
with overridable steps) or Strategy (a composed, swappable object or
function) over a single flat function with many boolean or enum parameters.
A shared function that grows a long parameter list of flags to handle every
clone's special case is itself a documented anti-pattern in the making, and
Template Method or Strategy usually produces a clearer, more testable result
when the variation has real structure rather than being incidental.

## 15. Testing and verification

Duplicated code has a specific, measurable effect on testing that is worth
naming directly. test coverage measured per line or per branch treats each
clone as independent code to be covered, so a suite that covers the original
block thoroughly reports zero coverage benefit for an untested clone,
correctly, but a team that only watches the aggregate coverage percentage can
miss that one specific clone is untested while the metric as a whole looks
healthy. Reviewing coverage per file, not only in aggregate, is one of the
few reliable early signals of an untested clone in an otherwise well-tested
codebase.

Before refactoring duplication away, characterization tests, meaning tests
written against the current, possibly undocumented behavior of each clone
rather than against a specification, are the correct technique when the
original intent behind a clone's small differences is unclear. Writing a
characterization test for each clone before touching it converts "I believe
these three blocks do the same thing" into a verifiable claim, and the test
suite will fail loudly if the unification in dimension 14 accidentally
changes behavior that a clone's small, forgotten difference was relying on.

Golden master or snapshot testing is particularly well suited to verifying
that an Extract Method refactor of duplicated logic preserved behavior
exactly, because it captures the observable output of each clone across a
representative set of inputs before the refactor and diffs the shared
implementation's output against that captured baseline afterward, without
requiring the refactor's author to have anticipated every edge case a hand
written assertion would need.

A duplication detector such as PMD CPD or SonarQube's analysis, run as part
of continuous integration, functions as a regression test for the anti-
pattern itself, distinct from testing the behavior of any individual clone.
it fails the build, or at minimum reports a metric regression, when new
duplication above the project's configured threshold is introduced, which
catches the anti-pattern at the moment it is introduced rather than months
later when a missed fix shows up as a production bug.

## 16. Observability signals

Copy-paste programming is unusual among the anti-patterns in this catalog in
that it is directly, numerically measurable by static tooling rather than
only inferable from runtime behavior, so the most useful observability
signals for it are measured at build time rather than in a running system.

- **Duplicated lines density**, as defined by SonarQube's own formula,
  `duplicated_lines / lines * 100`, tracked as a trend over time on a
  project's default branch. a healthy, actively maintained codebase holds
  this number roughly flat or falling as it grows. a rising trend, even a
  slow one, indicates the team is copying faster than it is extracting
  shared abstractions.
- **Duplicated blocks count**, the number of distinct locations flagged as
  containing a duplicate, which behaves differently from the density
  percentage. a small file with one large duplicated block can show a
  worse density percentage than a large codebase with many small
  duplications, so both numbers are needed together to judge severity, not
  either alone.
- **Per-file and per-pull-request duplication delta**, meaning whether a
  specific change increased or decreased the count of duplicated blocks,
  shown directly in the pull request rather than only in a periodic
  dashboard. this is the signal that catches a new clone at the moment of
  review, which is far cheaper to fix than catching it after it has already
  merged and been copied again from.
- **Coverage-per-clone gap**, meaning a difference in test coverage
  percentage between two files or functions that a duplication detector has
  flagged as clones of each other. when one clone in a detected pair has
  coverage noticeably lower than the other, that is a strong, specific
  signal that a bug fix or a test written against one clone was never
  ported to its sibling.
- Once duplication is removed by extracting a shared implementation, the
  corresponding healthy signal to watch for regression is a rising call
  count or fan-in on the extracted function, confirmed against static
  analysis of its callers, which shows the unification held rather than a
  new clone having been created alongside it later.

Where a running production system is involved rather than only the codebase
itself, this dimension is judgement, not a sourced fact. the most direct
production signal is an inconsistency between two features that a product
owner believes share the same underlying rule, reported as a discrepancy
rather than as a crash or an error log line, which is why this anti-pattern's
production failures are often reported as confusing product bugs rather than
as incidents.

## 17. Security and privacy implications

Duplicated logic is a security concern specifically, not only a general
maintainability one, whenever the duplicated code performs authentication,
authorization, input validation, output encoding, or a cryptographic
parameter choice. A vulnerability fixed in one copy of such logic and missed
in a sibling copy leaves the exact same vulnerability reachable through a
different code path, and because the fix already shipped and was already
verified against the original location, the team's own records show the
issue as resolved while it remains exploitable elsewhere. This is a worse
outcome in practice than the vulnerability never having been patched at all,
because a resolved-but-still-present vulnerability is far less likely to be
looked at again by the people who already believe it was fixed.

Copying code from an external source, whether a public forum, a blog post,
another open-source project, or an AI coding assistant's suggestion, carries
an additional, distinct risk. the pasted code was written against a
different codebase's assumptions about input trust, error handling, and
logging, and pasting it without adapting those assumptions to the local
codebase's own security model can quietly reintroduce a class of bug the
local codebase had otherwise eliminated, for example logging a secret that
the source project's logging configuration happened to redact but the
destination project's does not. This dimension is judgement grounded in the
general secure-coding literature's emphasis on trust boundaries, not a
single sourced claim, and it is stated here because it is the specific way
copy-paste programming intersects with security beyond the general
maintenance argument made elsewhere in this entry.

There is no privacy-specific implication distinct from the general security
point above. duplicated logic that handles personal data carries the same
risk as duplicated logic that handles anything else, that a data-handling
fix, such as adding a required consent check or a redaction rule, is applied
to one copy and missed in a sibling copy, with the missed copy then
processing personal data in a way the fixed copy no longer does.

## 18. References

- Brown, William J., Raphael C. Malveau, Hays W. McCormick, and Thomas J.
  Mowbray. *AntiPatterns. Refactoring Software, Architectures, and Projects
  in Crisis.* John Wiley and Sons, 1998, chapter 4, Cut-and-Paste
  Programming.
- Fowler, Martin. *Refactoring. Improving the Design of Existing Code.* 2nd
  edition, Addison-Wesley, 2018, chapter 3, Bad Smells in Code, Duplicated
  Code.
- Wikipedia. "Copy-and-paste programming."
  https://en.wikipedia.org/wiki/Copy-and-paste_programming, verified
  2026-08-02.
- Fowler, Martin. "CodeSmell."
  https://martinfowler.com/bliki/CodeSmell.html, verified 2026-08-02.
- PMD project documentation. "PMD CPD."
  https://pmd.github.io/pmd/pmd_userdocs_cpd.html, verified 2026-08-02.
- SonarSource. "SonarQube Server, Metric Definitions."
  https://docs.sonarsource.com/sonarqube-server/user-guide/code-metrics/metrics-definition/,
  verified 2026-08-02.

## Code examples

Three languages, each showing the same shape. duplicated function-body
validation with a hand-dropped currency check, then the Extract Method
refactor from dimension 14 that unifies the two call sites behind one
parameter. All six samples were compiled or type-checked directly, not
merely inspected.

### TypeScript, before (duplicated) and after (extracted)

```typescript
interface Order {
  items: { price: number; quantity: number }[];
  currency: string;
}

// Checkout module: validation copied and adapted by hand for a special case.
function validateOrderForCheckout(order: Order): string[] {
  const errors: string[] = [];
  if (order.items.length === 0) {
    errors.push("order has no items");
  }
  const total = order.items.reduce((sum, i) => sum + i.price * i.quantity, 0);
  if (total <= 0) {
    errors.push("order total must be positive");
  }
  if (order.currency !== "EUR" && order.currency !== "USD") {
    errors.push(`unsupported currency: ${order.currency}`);
  }
  return errors;
}

// Refund module: pasted from validateOrderForCheckout, currency check dropped
// by hand and never restored when the currency rule changed upstream.
function validateOrderForRefund(order: Order): string[] {
  const errors: string[] = [];
  if (order.items.length === 0) {
    errors.push("order has no items");
  }
  const total = order.items.reduce((sum, i) => sum + i.price * i.quantity, 0);
  if (total <= 0) {
    errors.push("order total must be positive");
  }
  return errors;
}

const order: Order = { items: [{ price: 10, quantity: 2 }], currency: "GBP" };
const checkoutErrors: string[] = validateOrderForCheckout(order);
const refundErrors: string[] = validateOrderForRefund(order);
void checkoutErrors;
void refundErrors;
```

```typescript
interface Order {
  items: { price: number; quantity: number }[];
  currency: string;
}

interface ValidateOrderOptions {
  requireSupportedCurrency: boolean;
}

// Extract Method: one definition, a parameter for the point where the two
// call sites genuinely differed, so the fix in dimension 14 reaches both.
function validateOrder(order: Order, options: ValidateOrderOptions): string[] {
  const errors: string[] = [];
  if (order.items.length === 0) {
    errors.push("order has no items");
  }
  const total = order.items.reduce((sum, i) => sum + i.price * i.quantity, 0);
  if (total <= 0) {
    errors.push("order total must be positive");
  }
  if (options.requireSupportedCurrency) {
    if (order.currency !== "EUR" && order.currency !== "USD") {
      errors.push(`unsupported currency: ${order.currency}`);
    }
  }
  return errors;
}

const order: Order = { items: [{ price: 10, quantity: 2 }], currency: "GBP" };
const strictErrors: string[] = validateOrder(order, { requireSupportedCurrency: true });
const looseErrors: string[] = validateOrder(order, { requireSupportedCurrency: false });
void strictErrors;
void looseErrors;
```

Checked with `tsc --noEmit --strict --target es2022 --lib es2022`. Both
files typecheck clean.

### Python, before (duplicated) and after (extracted)

```python
def validate_order_for_checkout(items, currency):
    errors = []
    if not items:
        errors.append("order has no items")
    total = sum(price * quantity for price, quantity in items)
    if total <= 0:
        errors.append("order total must be positive")
    if currency not in ("EUR", "USD"):
        errors.append(f"unsupported currency: {currency}")
    return errors


# Pasted from validate_order_for_checkout. The currency check was dropped
# by hand and never restored when the currency rule changed upstream.
def validate_order_for_refund(items, currency):
    errors = []
    if not items:
        errors.append("order has no items")
    total = sum(price * quantity for price, quantity in items)
    if total <= 0:
        errors.append("order total must be positive")
    return errors
```

```python
def validate_order(items, currency, require_supported_currency):
    errors = []
    if not items:
        errors.append("order has no items")
    total = sum(price * quantity for price, quantity in items)
    if total <= 0:
        errors.append("order total must be positive")
    if require_supported_currency and currency not in ("EUR", "USD"):
        errors.append(f"unsupported currency: {currency}")
    return errors
```

Checked with `python3 -m py_compile`. Both files compile clean.

### Go, before (duplicated) and after (extracted)

```go
package main

type item struct {
	price    float64
	quantity int
}

func validateOrderForCheckout(items []item, currency string) []string {
	var errors []string
	if len(items) == 0 {
		errors = append(errors, "order has no items")
	}
	total := 0.0
	for _, it := range items {
		total += it.price * float64(it.quantity)
	}
	if total <= 0 {
		errors = append(errors, "order total must be positive")
	}
	if currency != "EUR" && currency != "USD" {
		errors = append(errors, "unsupported currency: "+currency)
	}
	return errors
}

// Pasted from validateOrderForCheckout. The currency check was dropped
// by hand and never restored when the currency rule changed upstream.
func validateOrderForRefund(items []item, currency string) []string {
	var errors []string
	if len(items) == 0 {
		errors = append(errors, "order has no items")
	}
	total := 0.0
	for _, it := range items {
		total += it.price * float64(it.quantity)
	}
	if total <= 0 {
		errors = append(errors, "order total must be positive")
	}
	return errors
}
```

```go
package main

type item struct {
	price    float64
	quantity int
}

func validateOrder(items []item, currency string, requireSupportedCurrency bool) []string {
	var errors []string
	if len(items) == 0 {
		errors = append(errors, "order has no items")
	}
	total := 0.0
	for _, it := range items {
		total += it.price * float64(it.quantity)
	}
	if total <= 0 {
		errors = append(errors, "order total must be positive")
	}
	if requireSupportedCurrency && currency != "EUR" && currency != "USD" {
		errors = append(errors, "unsupported currency: "+currency)
	}
	return errors
}
```

Checked with `go vet`. Both files vet clean. Go, Python, and TypeScript were
chosen because Extract Method is genuinely idiomatic in all three without
scaffolding. a plain function extraction, no framework, no build step beyond
the compiler itself. Java, Rust, Swift, C#, and Kotlin are omitted from this
entry's code samples because the same three-language demonstration already
carries the pattern completely, not because the anti-pattern is language
specific. copy-paste duplication and its Extract Method fix apply equally in
every language this catalog covers.
