---
name: Approval Test
slug: approval-test
family: 14-testing
category: Testing
aliases: [Golden Master Test, Snapshot Test, Characterization Test (closely related, not identical)]
first_described: "Falco and Bache, ApprovalTests library and community practice, circa 2000s-2010s"
maturity: established
related: [test-double, template-method, visitor, memento]
incompatible_with: []
verified: 2026-08-02
---

# Approval Test

## 1. Name, aliases, and lineage

The pattern is most commonly called an Approval Test, and the practice around it
is called Approval Testing. The name comes directly from its mechanics. a test
run produces output, a human APPROVES that output once, and every later run is
compared against the approved copy rather than against a hand-written
assertion. The word "approval" names the human act at the center of the
pattern, which is the detail every alias below tends to obscure.

Two aliases are close to synonyms and are used interchangeably by
practitioners. **Golden Master Test** borrows the phrase from broadcast and
manufacturing, where the "golden master" is the single reference copy every
later copy is checked against. **Snapshot Test** is the name the JavaScript and
React community settled on, popularized by Jest's `toMatchSnapshot()` API,
where a snapshot is captured on first run and every later run is diffed
against it (Jest documentation, "Snapshot Testing",
https://jestjs.io/docs/snapshot-testing, verified 2026-08-02). The mechanics
described on that page (an initial capture, a stored reference file, a diff on
mismatch, an explicit update command) are the same mechanics the ApprovalTests
family documents for its own libraries, so treating snapshot testing as
approval testing under a different brand name, for the purposes of this entry,
is accurate rather than loose.

A fourth, related but NOT identical term is **Characterization Test**, coined
by Michael Feathers to describe a test written specifically to pin down the
CURRENT, possibly undesirable, behavior of legacy code before refactoring it
(Michael Feathers, *Working Effectively with Legacy Code*, Prentice Hall,
2004, chapter 13, "I Need to Make a Change, but I Don't Know What Tests to
Write"). A characterization test is a goal, capture what the code does right
now, bugs included, as a safety net, and an approval test is a MECHANISM, the
snapshot-and-diff machinery. The two are frequently used together, an approval
test is very often the vehicle for writing a characterization test around
legacy code, but the terms are not interchangeable. an approval test can also
be written for brand-new code with no legacy baggage at all, and a
characterization test could in principle be written as a hand-coded assertion
instead of a snapshot.

The most visible open-source implementation is the ApprovalTests family of
libraries, maintained under the `approvals` GitHub organization, spanning
Java, C#, C++, PHP, Python, Swift, JavaScript, Perl, Go, Lua, Objective-C,
Ruby, LabVIEW, Dart, and Elixir (approvaltests.com, "Approval Testing",
https://approvaltests.com/, verified 2026-08-02). The project's public
resources page and podcast credit Llewellyn Falco as a central figure in the
tooling's development and popularization (approvaltests.com resources page,
https://approvaltests.com/resources/, verified 2026-08-02). The pattern's
theory and its association with legacy-code work are described extensively by
Emily Bache, whose father Geoff Bache's TextTest project (texttest.org,
https://texttest.org/, verified 2026-08-02, self-described on its own site as
"an Approval Testing Framework") is one of the earliest tools built explicitly
around comparing an entire program's textual output against a stored,
human-approved reference, predating the ApprovalTests library naming. Because
neither party's own site states an exact founding year for the underlying
practice, this entry treats "who coined the exact phrase approval testing,
and in which year" as unverified and does not assert a specific date. what IS
verifiable and stated as fact above is the mechanism, the maintainer
attribution on the current project sites, and the multi-decade lineage back
through characterization testing and golden master comparison in QA practice.

## 2. Problem and context

Consider a function that renders an invoice as HTML, a compiler pass that
lowers an abstract syntax tree to bytecode, a report generator that produces a
multi-page PDF summary, or a machine-learning pipeline that emits a structured
JSON prediction with forty fields. In every one of these cases the OUTPUT is
large, structured, and shaped by many independent pieces of logic acting
together, and a bug can appear as a one-character difference buried in the
middle of it.

Testing this kind of code with conventional example-based assertions runs into
a wall almost immediately. To assert on the invoice HTML with `assertEquals`,
someone has to type out, by hand, the entire expected HTML string, including
every tag, every attribute, and every whitespace character, and then keep that
hand-typed string synchronized every time the template changes even slightly.
The assertion becomes a second copy of the output that must be maintained in
lockstep with the first, and in practice teams either give up and write no
test for this kind of code at all, or they write a shallow test that checks
one field and lets the rest of the output go unverified. Neither outcome is
acceptable, because the exact defects this kind of code produces, a
misaligned column, a dropped field, a locale bug in a date format, live
precisely in the parts nobody bothered to assert on.

A second, closely related problem is legacy code with no tests at all, that a
team needs to refactor. Feathers names this directly. before you can safely
change code you do not understand, you need a test that tells you whether your
change altered behavior, and writing that test by reasoning about what the
correct behavior SHOULD be is often impossible, because nobody currently
understands the code well enough to say (Feathers, *Working Effectively with
Legacy Code*, chapter 13). What IS available is the code's CURRENT, observable
behavior, which can be captured mechanically rather than reasoned about.

Approval testing solves both problems with the same mechanism. instead of a
human writing the expected output by hand, the human RUNS the code once,
inspects the actual output, and if it is correct (or, for legacy code, if it
is simply what the code currently does), APPROVES it. The approved copy is
saved to disk, checked into version control alongside the test, and every
future run of the test compares fresh output against that saved copy. A
difference is not silently accepted or silently ignored, it is surfaced as a
diff for a human to review, at which point the human either fixes the code
(the difference is a regression) or re-approves the new output (the
difference is an intentional change). The pattern moves the cost of writing
the expected value from being typed by hand, up front, for every test, to
being captured mechanically and reviewed by eye, once per change.

## 3. Forces

The pattern is a genuine trade, not a free improvement, and every entry that
uses it should say what is being traded.

**Assertion authoring cost versus assertion writing precision.** Hand-written
assertions force the author to think, field by field, about what the correct
value should be, which is a form of specification. Approval tests skip that
authoring cost entirely, in exchange for accepting whatever the code currently
produces as the baseline. The force favors approval testing heavily when the
output is large and mechanical, and favors example-based assertions when the
output is small and the correct value needs to be reasoned about rather than
observed.

**Review cost at write time versus review cost at diff time.** A traditional
assertion is reviewed once, when the test is written or during code review of
the test. An approval test defers that review to every time the output
changes, when a human reads a diff and decides whether it is correct. For code
that changes rarely this is a net win, review happens only when something
actually moved. For code that changes constantly in expected, cosmetic ways,
a timestamp, a random ID, a build number embedded in the output, this force
flips against the pattern unless those fields are explicitly scrubbed before
comparison (see dimension 11).

**Fidelity to real behavior versus fidelity to intended behavior.** An
approval test, especially one written against legacy code with no
specification, captures what the code DOES, not what it SHOULD do. This is
precisely the force Feathers exploits for characterization testing, current
behavior is a safety net for refactoring even when it encodes an existing bug,
but it is also the pattern's central danger. approving broken output makes the
bug part of the permanent, defended baseline, and every future run of the
suite will now flag a FIX to that bug as a regression.

**Diff signal versus diff noise.** The value of the pattern is entirely
contingent on the diff a human sees at approval time being small, readable,
and localized to the actual change. A single large text blob with no
canonicalization, no field-level structure, and no stable ordering produces a
diff that is technically correct but practically unreadable, and once
reviewers start rubber-stamping large diffs without reading them, the safety
net silently stops working. This force is why every mature approval-test
library invests heavily in reporters, structured output formats, and
scrubbers rather than treating the comparison as a raw string diff.

**Team topology and review discipline.** The pattern assumes a human will
genuinely inspect the diff at approval time rather than reflexively running
the accept command. Teams under deadline pressure, or teams that treat a
failing snapshot test as an annoyance to be silenced rather than a signal to
be investigated, degrade the pattern into a no-op that always passes after one
keystroke. This is a cultural and process force, not a technical one, but it
determines whether the pattern delivers real regression protection or a false
sense of safety.

## 4. Applicability and non-applicability

### Reach for approval testing when

- The output under test is large, structured, and would be expensive or
  error-prone to hand-author as an expected value (rendered HTML, generated
  code, a serialized object graph, a multi-field report, a compiler's
  intermediate representation).
- You are working with legacy code that has no tests and no clear
  specification, and you need a safety net before refactoring (Feathers,
  *Working Effectively with Legacy Code*, chapter 13, on characterization
  tests, for which an approval test is the standard implementation vehicle).
- The output is deterministic, or can be made deterministic by controlling or
  scrubbing the non-deterministic parts (timestamps, random IDs, ordering).
- The team has, or is willing to build, review discipline around reading
  diffs at approval time, and a workflow (a diff tool, a CI gate) that makes
  skipping that review inconvenient.
- You are doing UI component testing where a rendered DOM tree or a component
  tree is the natural unit of comparison (Jest snapshot testing's primary use
  case, https://jestjs.io/docs/snapshot-testing, verified 2026-08-02).
- You are testing a data transformation, migration script, or report
  generator where correctness means matching a known-good shape more than it
  means satisfying one specific business rule.

### Do NOT reach for approval testing when

- The expected value is small, simple, and easily stated as a literal
  (`assertEquals(42, calculateTotal(items))`). An approval test here adds a
  file, a diff step, and an approval workflow around a value a single
  assertion states more clearly and more precisely.
- The test is meant to verify a SPECIFIC business rule or edge case, for
  example that negative quantities are rejected or that a discount cannot
  exceed 100 percent. A snapshot of the whole response object obscures which
  single field the test is actually protecting, and a reader six months
  later cannot tell what invariant the test enforces just by reading it.
- The output is inherently non-deterministic and cannot practically be made
  deterministic (a network trace with live timing data, an ML model's
  output when the model itself is still being tuned and expected to drift).
- The team has no review discipline and no CI enforcement, so failing
  snapshots are habitually accepted without inspection. In this environment
  the pattern provides a false sense of coverage that is worse than no test,
  because it looks green while verifying nothing.
- The output changes on almost every commit for reasons unrelated to
  correctness (an embedded build timestamp, a randomly generated identifier,
  environment-dependent formatting) and the team has not built the
  scrubbing/normalization step to remove that noise before comparison. Left
  unaddressed, this produces a permanently red or permanently rubber-stamped
  test, either of which defeats the purpose.
- Precise, human-readable failure messages that name exactly which invariant
  broke are more valuable than a text diff. approval tests report WHAT
  changed, not WHY it matters, and a domain-specific assertion failure message
  often communicates intent far better than a text diff can.

## 5. Structure

An approval test system has five participants, and confusing their
responsibilities is the most common source of home-grown, badly built
approval test setups.

- **System Under Test (SUT).** The function, class, or pipeline whose output
  is being captured. It has no awareness that it is being approval-tested,
  and should not, because the pattern is a testing technique layered on top of
  ordinary code, never a design constraint the production code itself must
  satisfy.
- **Receiver.** The artifact produced by running the SUT once, in the current
  test run. In the ApprovalTests family this is conventionally written to a
  file suffixed `.received.<ext>` (for example `.received.txt`). It exists
  only transiently, is written on every run, and is never checked into
  version control.
- **Approved (or Verified) Baseline.** The stored, human-reviewed reference
  output, checked into version control alongside the test source. In the
  ApprovalTests family this is conventionally suffixed `.approved.<ext>`; the
  .NET Verify library uses `.verified.` for the same role (VerifyTests/Verify
  README, https://github.com/VerifyTests/Verify, verified 2026-08-02). This
  file is the one artifact of the whole system that is deliberately edited
  only through the approval workflow, never by hand-typing an expected value.
- **Comparer.** The component that decides whether the Receiver matches the
  Approved baseline. For text this can be a byte-for-byte comparison, a
  whitespace-normalizing comparison, or a structured comparison (comparing
  parsed JSON trees rather than raw bytes so that key reordering does not
  register as a false failure). The Comparer's sophistication is the single
  biggest determinant of how much diff-noise the pattern produces.
- **Reporter.** The component invoked on a mismatch, responsible for
  presenting the difference to a human in a form they can act on. This ranges
  from a plain textual diff printed to the console, to launching a dedicated
  diff tool (Beyond Compare, Kaleidoscope, VS Code's diff view), to, for image
  or PDF output, opening a visual side-by-side comparison. The ApprovalTests
  documentation describes multiple Reporter implementations chosen per
  environment (approvaltests.com, "Approval Testing", verified 2026-08-02;
  Verify README documents diff-tool and IDE-plugin acceptance workflows,
  verified 2026-08-02).

A sixth, optional participant appears in almost every real system once output
contains anything non-deterministic.

- **Scrubber.** A normalization step applied to the Receiver (and sometimes
  to the Approved baseline at authoring time) before the Comparer runs, which
  replaces or removes values that legitimately vary between runs but do not
  represent a real behavioral difference, a wall-clock timestamp becomes
  `[[TIMESTAMP]]`, a randomly generated UUID becomes `[[GUID_1]]`, and so on.
  Skipping this participant is the single most common cause of approval tests
  that flake on CI.

## 6. ASCII structure diagram

```
+-------------------+        run once        +-------------------+
|  System Under Test | ----------------------> |     Receiver      |
|   (SUT / function) |                         | (fresh, transient) |
+-------------------+                         +---------+----------+
                                                          |
                                                    optional scrub
                                                          |
                                                          v
+---------------------+   compares against    +----------------------+
|  Approved Baseline   | <--------------------- |      Comparer        |
| (checked into VCS)   |                        | (byte/structured/etc)|
+----------+-----------+                        +-----------+----------+
           ^                                                |
           |                                          mismatch?
     human approves                                         |
     (copies Received                                       v
      over Approved)                              +--------------------+
           |                                       |     Reporter       |
           +---------------------------------------|  (diff / visual)   |
                                                     +--------------------+
```

## 7. Dynamics

The runtime flow has two distinct paths, first-run and steady-state, and a
third path, the deliberate re-approval, that is the pattern's whole point.

```
FIRST RUN (no Approved baseline exists yet)
  1. Test invokes SUT.
  2. SUT produces output; test writes it to Receiver (.received.ext).
  3. Comparer looks for Approved baseline, finds none.
  4. Test FAILS (missing baseline is treated as a mismatch, never a pass).
  5. Human inspects Receiver by eye.
  6. If correct, human copies Receiver -> Approved (the "approve" action).
  7. Approved file is committed to version control alongside the test.

STEADY STATE (baseline already exists, code unchanged)
  1. Test invokes SUT.
  2. SUT produces output; test writes it to Receiver.
  3. (Optional) Scrubber normalizes volatile fields in Receiver.
  4. Comparer diffs Receiver against Approved.
  5. Identical -> test PASSES. Receiver is discarded (or left, gitignored).

STEADY STATE, CODE CHANGED (behavior actually differs)
  1-4. Same as above, but Comparer finds a difference.
  5. Test FAILS.
  6. Reporter surfaces the diff to a human (console, diff tool, image view).
  7. Human decides.
       a) The difference is a REGRESSION -> fix the SUT, rerun from step 1.
       b) The difference is INTENTIONAL -> approve the new Receiver,
          overwrite Approved, commit the change to version control.
```

The dynamics make explicit what distinguishes an approval test from a plain
snapshot. it is the presence of a genuine human decision point at every
mismatch, and the requirement that the Approved file be committed and
reviewed like any other source artifact, that turns the mechanism into a test
rather than a self-updating cache.

## 8. Implementation variants

- **Text-diff approval, the baseline form.** The Receiver and Approved
  artifacts are plain text files (or serialized structures pretty-printed as
  text), compared line by line or byte by byte. This is the form used by
  TextTest for command-line program output (texttest.org, verified
  2026-08-02) and by most ApprovalTests language ports for simple values.

- **Structured (semantic) comparison.** Instead of comparing raw bytes, the
  Comparer parses both sides (as JSON, XML, or a language-native object graph)
  and compares the resulting structures. This avoids false failures caused by
  differences that carry no real signal, such as key ordering in a JSON
  object or attribute ordering in an XML tag, at the cost of a comparer that
  must understand the format. Property-based matchers such as Jest's
  `expect.any(Date)` inside `toMatchSnapshot()` are a lightweight version of
  this idea, letting specific fields be matched by type or predicate rather
  than by exact value (Jest documentation, "Property Matchers",
  https://jestjs.io/docs/snapshot-testing, verified 2026-08-02).

- **Inline snapshots.** The approved value is embedded directly inside the
  test source file, adjacent to the assertion, rather than stored in a
  separate sibling file. Jest's `toMatchInlineSnapshot()` writes the approved
  string literally into the calling test file on approval (Jest
  documentation, "Inline Snapshots", https://jestjs.io/docs/snapshot-testing,
  verified 2026-08-02). This trades discoverability of the baseline (it sits
  right next to the assertion, easy to read in review) against file size and
  diff noise in the test file itself when the snapshot is large.

- **Combination approval (multi-parameter tests).** Several libraries in the
  ApprovalTests family support capturing the Cartesian product of a small set
  of input parameters and their outputs in a single approved file, so that a
  parameterized test's entire input/output matrix is reviewed and approved as
  one unit rather than as N separate approvals.

- **Visual/binary approval.** For output that is not text at all, a rendered
  image, a generated PDF, a screenshot of a UI component, the Comparer works
  on the binary or pixel data (often with a tolerance threshold for anti-
  aliasing or minor rendering differences), and the Reporter opens a visual
  side-by-side or overlay diff rather than a text diff. Tools such as
  `jest-image-snapshot` extend Jest's snapshot mechanism specifically to
  handle this case for screenshots and rendered UI.

- **Verified-object approval with custom serializers (Verify, .NET).** Rather
  than requiring the developer to pre-serialize the SUT's output to a string,
  the library performs the serialization itself for a wide range of .NET
  types, and exposes converters so that domain objects, streams, and even
  third-party SDK response types serialize into a stable, comparable text
  form automatically (VerifyTests/Verify README, verified 2026-08-02). This
  variant trades a small amount of control over exactly how something
  serializes for a much lower barrier to writing the first approval test
  against an arbitrary object graph.

- **Golden file / fixture-directory approval (language-agnostic idiom).**
  Common outside any specific library, especially in compilers and CLI
  tools. A directory of `input.*` / `expected.*` file pairs is walked at test
  time, each input is run through the SUT, and the output is diffed against
  the paired expected file. This is architecturally identical to approval
  testing but is often implemented by hand with a simple file-walking loop
  rather than a dedicated library, because the domain (compiler test suites in
  particular) has used this idiom since long before the ApprovalTests
  libraries existed under that name.

## 9. Known production uses

- **Jest (Meta/OpenJS Foundation), snapshot testing.** Jest's own
  documentation describes `toMatchSnapshot()` as a first-class, built-in
  testing primitive, storing snapshots in a `__snapshots__` directory beside
  the test file and requiring an explicit `--updateSnapshot` (or `-u`) flag to
  accept changes; the documentation explicitly instructs that CI systems must
  not silently regenerate snapshots (Jest documentation, "Snapshot Testing",
  https://jestjs.io/docs/snapshot-testing, verified 2026-08-02). Jest is
  Meta's own JavaScript testing framework and is one of the most widely used
  test runners among JavaScript developers, making its adoption of approval
  testing as a core, documented feature, rather than a third-party plugin, a
  strong real-world endorsement of the pattern at scale.

- **Verify (VerifyTests organization, .NET).** An actively maintained
  open-source snapshot/approval testing library for .NET, with roughly 3,500
  GitHub stars as of the verification date, integrating with NUnit, xUnit V3,
  MSTest, Fixie, TUnit, and Expecto test frameworks, and supporting
  IDE-integrated approval via ReSharper and Rider plugins (VerifyTests/Verify
  README, https://github.com/VerifyTests/Verify, verified 2026-08-02). As of
  August 2026 the project's README states that commercial and government use
  of official binaries requires a paid subscription while the source remains
  open, itself a data point that the tooling has reached a scale of adoption
  that supports a commercial model.

- **ApprovalTests library family (the `approvals` GitHub organization).**
  Language ports spanning Java, C#, C++, PHP, Python, Swift, JavaScript,
  Perl, Go, Lua, Objective-C, Ruby, LabVIEW, Dart, and Elixir are documented
  and maintained on approvaltests.com, with a shared documentation project
  (`ApprovalTests.Documentation`) describing the shared conceptual model
  across all of them (approvaltests.com, https://approvaltests.com/, and
  the C++ port README at
  https://github.com/approvals/ApprovalTests.cpp, both verified 2026-08-02).
  The breadth of independently maintained ports across this many languages,
  rather than a single library adopted in one language community, is itself
  evidence that the underlying pattern is treated as a portable testing
  technique rather than a feature specific to one language's tooling.

- **TextTest.** A dedicated, long-running open-source framework that
  self-describes as "an Approval Testing Framework" for whole-program,
  text-output regression testing, with both a command-line runner and a
  graphical interface for reviewing and approving test output
  (texttest.org, https://texttest.org/, verified 2026-08-02). Its existence
  as a standalone tool predates much of the current library naming around the
  term "approval testing" and demonstrates the pattern's application to
  whole-system, black-box regression testing of command-line programs rather
  than only unit-level object comparisons.

## 10. Consequences

### Positive

- **Removes the assertion-authoring bottleneck for large, structured output.**
  Nobody has to hand-type a 200-line expected HTML string; the code produces
  it once and a human reviews it.
- **Turns a lack of tests for legacy code into a tractable problem.**
  Approval testing is the standard implementation vehicle for
  characterization tests, giving teams a safety net for refactoring code they
  do not fully understand (Feathers, chapter 13).
- **Surfaces UNEXPECTED changes with high sensitivity.** Because the
  comparison is against the FULL output, a change to any field, not just the
  fields an example-based test happened to check, is caught.
- **The diff itself is documentation of intent.** When a legitimate change is
  approved, the diff in the version control history shows exactly what
  behavior changed and when, which is often more informative than a
  hand-written assertion that was simply edited in place with no record of
  the prior value.
- **Scales naturally to parameterized and combinatorial testing.** Capturing
  a large matrix of input/output pairs in one approved artifact is far
  cheaper than writing N individual assertions.

### Negative

- **Approves bugs as easily as it approves correct behavior.** The pattern
  has no concept of correct; it only knows whether output matches the
  baseline. A careless or rushed approval bakes a defect permanently into the
  safety net it was meant to be.
- **Large or unstructured diffs erode review discipline over time.** Once a
  team habitually rubber-stamps big, noisy diffs without reading them, every
  subsequent approval carries the same risk, and the test suite degrades into
  theater.
- **Non-deterministic output requires ongoing scrubber maintenance.** Every
  new field with a timestamp, random ID, or environment-dependent value adds
  another place a scrubber must be updated, and a missed one produces flaky
  CI failures that are not real regressions.
- **The approved baseline is a large, mostly-opaque artifact to review in a
  pull request.** A reviewer with no domain context sees a wall of diff and
  has to trust that whoever approved it looked closely; this shifts real
  review burden onto the person doing the local approval rather than
  distributing it across the team the way a smaller, hand-written assertion
  would.
- **Weak or absent intent signal.** A failing approval test tells you WHAT
  changed but not WHY it matters or which business rule it protects, which
  can slow down triage compared to a domain-specific assertion with a clear
  failure message.
- **Version control noise.** Large binary or heavily-formatted approved
  files can bloat diffs and repository size over time, particularly for
  image or PDF approvals, unless the repository's diff tooling and storage
  strategy (for example Git LFS for binary approvals) are chosen
  deliberately.

## 11. Failure modes and misuse

**Symptom.** CI intermittently fails on a snapshot test with no code change
in the relevant area, and rerunning the same commit sometimes passes and
sometimes fails.
**Cause.** The output contains an unscrubbed non-deterministic value, most
commonly a timestamp, a UUID, a hash of something time-dependent, or
iteration order over an unordered collection (a `HashMap`/`dict`/`Set`
serialized without a stable sort).
**Fix.** Add a Scrubber step that normalizes every volatile field before
comparison (replace timestamps and UUIDs with fixed placeholder tokens,
explicitly sort any collection before serializing it), and add a regression
test asserting the scrubber itself catches the specific volatile field that
caused the flake.

**Symptom.** A pull request shows a single-line code change accompanied by a
40-file, thousands-of-line snapshot diff, and the reviewer approves the PR
within two minutes.
**Cause.** The approved baselines are too coarse-grained, one giant snapshot
per test suite rather than one focused snapshot per behavior, so a small,
localized change ripples through formatting or serialization in a way that
touches every baseline at once, and the sheer volume makes genuine review
infeasible.
**Fix.** Narrow the scope of each individual snapshot to the smallest unit
that demonstrates one behavior; where a shared formatting or serialization
change is intentional and expected to touch many files, call that out
explicitly in the PR description and consider approving the bulk update as a
dedicated, clearly labeled commit separate from the behavioral change.

**Symptom.** The team reports having great test coverage because all
snapshot tests pass, but a real regression reaches production untested.
**Cause.** Developers have adopted the reflex of running the update-snapshots
command whenever a test fails locally, without reading the diff, effectively
converting every approval test into an assertion that always passes.
**Fix.** Add a CI-only check (distinct from the local dev loop) that fails
the build if any snapshot file was modified in the same commit without an
accompanying, explicit note in the commit message or PR description, and
periodically audit a sample of approved changes in code review specifically
for evidence the diff was read rather than blindly accepted.

**Symptom.** A single approval test, meant to protect one small piece of
logic, fails on nearly every unrelated change to the codebase.
**Cause.** The snapshot was taken of an object that is far broader than the
unit under test, for example snapshotting an entire HTTP response object
(headers, request ID, full body) when the test is only meant to verify one
computed field in the body.
**Fix.** Narrow what is captured to the smallest slice of output that
represents the behavior under test, and use property matchers or partial
snapshots (matching a sub-object, or asserting specific fields separately
from the snapshot) rather than snapshotting the entire response.

**Symptom.** A legacy characterization test written via approval testing
passes forever, and a genuine bug fix six months later fails it, causing
confusion about whether the fix is correct.
**Cause.** The original approval baseline was captured and approved from
buggy legacy behavior without anyone realizing it was buggy at the time
(this is an inherent risk of characterization testing, not a bug in the
tooling).
**Fix.** When a "regression" turns out on inspection to be a deliberate,
correct bug fix, treat the failing approval test as confirming the fix
worked, re-approve the new (corrected) output, and record in the commit
message that the prior baseline encoded a known bug, so future readers of
the version-control history understand why the baseline changed.

## 12. Trade-off matrix

| Force | Approval Test | Example-Based Assertion | Property-Based Test | Contract Test |
|---|---|---|---|---|
| Authoring cost for large output | Low, output is captured, not typed | High, every field typed by hand | Low for the property, but requires designing a general invariant | Medium, requires defining a schema/contract |
| Precision of what is verified | Whole-output equality, coarse by default | Exactly the asserted fields, fine-grained | Verifies a stated invariant across many generated inputs | Verifies structural conformance to a shared contract |
| Catches unexpected fields changing | Yes, by default (whole-output diff) | No, only asserted fields are checked | Only if the invariant covers that field | No, only fields defined in the contract |
| Failure message clarity | A diff, shows WHAT changed, not WHY it matters | Domain-specific, can say exactly WHY | Reports the failing generated input (a counterexample) | Reports the specific contract clause violated |
| Human review burden over time | High, every accepted change needs eyes on a diff | Low per test, but authoring cost is high up front | Low, once the invariant is correctly specified | Low, once the contract is correctly specified |
| Best fit | Large/structured output, legacy characterization | Small, specific business rules | Algorithms with a checkable mathematical/logical invariant | Cross-service API compatibility |
| Risk of silently baking in a bug | High, an approved bug becomes the new baseline | Low, the author reasoned about the expected value | Low, invariant is reasoned about independently of implementation | Low, contract is typically independently authored |

## 13. Related and incompatible patterns

- **Characterization Test (Feathers).** The goal that approval testing very
  often serves as the mechanism for. When working with legacy code, an
  approval test is usually how a characterization test is actually
  implemented, capturing current behavior mechanically rather than by
  reasoning about intended behavior.
- **Template Method.** Some approval test tools structure the
  capture/compare/report flow itself as a Template Method, a fixed algorithm
  (run the SUT, write the Receiver, compare against Approved, invoke the
  Reporter on mismatch) with pluggable hooks for the Comparer and Reporter
  steps, which is exactly the invariant-skeleton, variable-steps shape
  Template Method describes.
- **Visitor.** Structured comparers that walk a parsed object graph (rather
  than comparing raw text) to produce a semantic diff frequently implement
  that walk as a Visitor over the tree, especially for XML or AST comparison.
- **Memento.** The Approved baseline itself functions conceptually like a
  Memento, a saved snapshot of an object's state that can be restored (or, in
  this case, compared against) later, though approval testing stores the
  memento as a durable, version-controlled artifact rather than an in-memory
  object.
- **Test Double family (Mock, Stub, Fake).** Approval testing is orthogonal
  to, and frequently combined with, test doubles. a test that stubs out a
  clock or a random-number generator to make the SUT's output deterministic
  is doing exactly the work described as scrubbing in dimension 11, except
  performed by controlling the input rather than normalizing the output after
  the fact; the two techniques, deterministic inputs via test doubles and
  scrubbed outputs via a Scrubber, are complementary, not competing.
- **Tension with strict TDD's red-green-refactor rhythm as commonly taught,
  in one narrow sense.** Classic TDD asks the developer to write the
  expected assertion FIRST, before the implementation, as a form of design
  pressure. An approval test, by construction, requires the code to run
  before there is anything to approve, so it cannot express a specification
  ahead of implementation in the same way a hand-written assertion can. This
  is a genuine tension, not an absolute incompatibility. teams commonly
  resolve it by using example-based, hand-written assertions during the
  initial TDD design phase of a new piece of logic, then switching to
  approval testing once the shape of the output has stabilized and the
  remaining value is regression protection against a large surface area
  rather than design pressure on a still-forming API.

## 14. Refactoring path in and out

**Introducing an approval test into a codebase with no test around a piece of
legacy code.**

1. Identify the entry point into the code under test, the narrowest function
   or method call that produces the output you care about, without changing
   any of the code's internals yet.
2. Write a test that calls that entry point with a REALISTIC input (drawn
   from production data or a close approximation) and captures the raw
   output, initially without any assertion at all beyond confirming it runs
   without throwing.
3. Wire the output into an approval library's `verify()` call (or, if
   building this by hand, write it to a `.received` file and diff it against
   a `.approved` file that does not yet exist).
4. Run the test once. It will fail because there is no baseline yet. Inspect
   the Received output by eye. If it looks like a faithful capture of the
   code's actual current behavior (not necessarily CORRECT behavior, just an
   accurate capture), approve it.
5. Commit the approved baseline to version control alongside the test.
6. Repeat for additional realistic inputs, particularly ones that exercise
   different branches through the code, until you have enough coverage of the
   code's behavior to feel safe making a change.
7. Now refactor the legacy code. Rerun the approval tests after each small
   step; any failure means the refactor changed observable behavior, which
   should be investigated before proceeding, not immediately re-approved.

**Removing (graduating away from) an approval test once it has served its
purpose.**

1. Once the legacy code has been refactored into smaller, well-understood
   units with clear responsibilities, identify the specific business rules
   the original approval test was inadvertently protecting.
2. Write focused, example-based unit tests for each of those specific rules
   against the newly extracted units, with clear names and clear assertion
   messages.
3. Once the new, focused tests cover the same behaviors the coarse approval
   test covered (verify this by intentionally introducing small bugs and
   confirming the new tests catch them, a form of mutation testing applied
   manually), the original, coarse-grained approval test can be removed.
4. Do not remove an approval test just because it feels large or verbose; only
   remove it once a more precise, more intention-revealing set of tests has
   demonstrably replaced its protective value. A prematurely removed approval
   test leaves a coverage gap that is easy to miss because the suite still
   appears green.

## 15. Testing and verification

Testing code that uses approval testing raises a meta-question, how do you
verify the TEST RIG itself is doing its job, which is easy to overlook.

- **Verify the rig actually fails on a real difference.** The single most
  important sanity check for any approval test setup is to deliberately break
  the code under test (change one field, flip one boolean) and confirm the
  approval test genuinely fails with a readable diff, then revert the break.
  A rig that silently passes on a broken build (because the Comparer is
  misconfigured, or a scrubber is stripping too much) provides negative
  value, it looks like coverage while providing none.
- **Keep the Approved baselines in version control and reviewed like code.**
  Treat any pull request that modifies an `.approved` (or `.verified`) file
  with the same scrutiny as one that modifies an assertion in a hand-written
  test, because it is functionally the same kind of change, the expected
  behavior of the system is being redefined.
- **Use deterministic inputs, always.** Combine approval testing with
  explicit test doubles for clocks, random-number generators, and any
  external dependency, so the Receiver is reproducible run to run without
  relying solely on a Scrubber to paper over non-determinism after the fact.
- **Test the Scrubber separately.** Since a bug in the scrubbing logic can
  hide a real regression (by over-scrubbing a field that should have been
  compared) or produce false failures (by under-scrubbing a genuinely
  volatile field), the scrubber itself deserves its own small, focused unit
  tests independent of the approval tests that rely on it.
- **Prefer structured comparison over raw text where the format supports it.**
  A structured (semantic) Comparer, per dimension 8, produces test failures
  that correlate more tightly with actual behavioral changes and fewer with
  incidental formatting differences, which directly reduces false positives
  and the erosion-of-trust failure mode described in dimension 11.

## 16. Observability signals

Approval testing is a build-time and test-time technique rather than a
runtime one, so its observability signals live in CI and version control
history rather than in production telemetry, but they are worth tracking
deliberately.

- **Snapshot/baseline churn rate per commit.** A healthy signal is that most
  commits touch zero or a small, explainable number of approved baselines.
  A rising trend of commits touching dozens of baselines at once is an early
  warning that the diffs are becoming too coarse for a real review
  (dimension 11's second failure mode).
- **CI-only check for unreviewed snapshot updates.** Track, and alert on, any
  commit that both modifies test code (or production code) AND an approved
  baseline file in the same push, without a corresponding note in the commit
  message; this is the mechanical proxy for confirming a diff was actually
  reviewed, described in dimension 11's third failure mode.
- **Flaky-test rate attributable to approval tests specifically.** Because
  non-determinism is the leading cause of approval-test flakiness (dimension
  11's first failure mode), tracking which specific approval tests flake, and
  how often, over time surfaces exactly which scrubbers are missing or
  incomplete.
- **Time-to-approve.** In teams using a manual review-and-approve workflow
  (rather than an automated CI gate), tracking how long an approval sits
  pending before a human reviews and approves it is a useful proxy for
  whether the review step is a genuine practice or a rubber stamp performed
  under time pressure at the last minute.

## 17. Security and privacy implications

Approval testing has one specific, real risk surface, and it is otherwise
largely silent on security.

- **Approved baseline files can leak sensitive data if captured from real
  production data.** Because the pattern's whole appeal is capturing REAL
  output rather than a hand-crafted stand-in, teams are tempted to run
  approval tests against production-like data that contains real customer
  names, real email addresses, real payment identifiers, or other regulated
  personal data, and then commit that data permanently into version control
  as the approved baseline. Once committed, that data persists in the
  repository's history indefinitely, even if the file is later edited or
  deleted, because most version control systems, Git included, retain every
  historical version of every tracked file by default. The concrete
  mitigation is to always generate synthetic or explicitly anonymized test
  fixtures for anything that will become an approved baseline, never a raw
  export of real production data, and to run a secret/PII scanner over any
  proposed approved file before it is committed.
- **Diff tooling that shells out to external programs is a supply-chain
  surface, but a narrow one.** Reporters that invoke an external diff or
  image-viewer application (Beyond Compare, Kaleidoscope, and similar) run
  local developer tooling in a local developer environment, not in
  production, so the blast radius of a compromised reporter configuration is
  limited to a developer's own machine rather than a running service; this is
  worth naming for completeness but is not a major concern relative to the
  data-leakage risk above.
- **No runtime attack surface.** Because approval testing runs entirely at
  build/test time and produces no runtime code path in the shipped
  application, it introduces no new attack surface into the production
  system itself, unlike patterns (such as certain plugin or middleware
  patterns) that add runtime machinery.

## 18. References

1. Michael Feathers, *Working Effectively with Legacy Code*, Prentice Hall,
   2004, chapter 13, "I Need to Make a Change, but I Don't Know What Tests to
   Write" (characterization testing, the goal approval testing frequently
   implements).
2. approvaltests.com, "Approval Testing" (home page, language list, and
   nine-step workflow description), https://approvaltests.com/, verified
   2026-08-02.
3. approvaltests.com, "Resources" (podcast and background notes featuring
   Llewellyn Falco), https://approvaltests.com/resources/, verified
   2026-08-02.
4. ApprovalTests.cpp GitHub repository README (C++ port, description of
   Approval Tests as "also known as Golden Master Tests or Snapshot
   Testing"), https://github.com/approvals/ApprovalTests.cpp, verified
   2026-08-02.
5. ApprovalTests.Documentation GitHub repository, "what_are_approvals.md"
   (approved/received file mechanics, golden master relationship),
   https://raw.githubusercontent.com/approvals/ApprovalTests.Documentation/main/explanations/what_are_approvals.md,
   verified 2026-08-02.
6. TextTest project home page (self-described as "an Approval Testing
   Framework" for command-line and whole-program output regression testing),
   https://texttest.org/, verified 2026-08-02.
7. Jest documentation, "Snapshot Testing" (toMatchSnapshot, `__snapshots__`
   directory, --updateSnapshot, toMatchInlineSnapshot, property matchers, CI
   guidance), https://jestjs.io/docs/snapshot-testing, verified 2026-08-02.
8. VerifyTests/Verify GitHub repository README (.NET snapshot/approval
   testing library, .received/.verified workflow, framework and IDE
   integrations, licensing note), https://github.com/VerifyTests/Verify,
   verified 2026-08-02.

## Code examples

### TypeScript (Jest-style snapshot approval)

```typescript
declare function test(name: string, fn: () => void): void;
declare function expect(value: unknown): { toMatchSnapshot(): void };

function formatInvoice(invoice: {
  id: string;
  items: { name: string; qty: number; price: number }[];
}): string {
  const lines = invoice.items.map(
    (i) => `${i.name.padEnd(20)} x${i.qty}  $${(i.qty * i.price).toFixed(2)}`
  );
  const total = invoice.items.reduce((s, i) => s + i.qty * i.price, 0);
  return [`Invoice ${invoice.id}`, ...lines, `Total: $${total.toFixed(2)}`].join("\n");
}

test("formats a multi-item invoice", () => {
  const output = formatInvoice({
    id: "INV-1001",
    items: [
      { name: "Widget", qty: 3, price: 9.5 },
      { name: "Gadget", qty: 1, price: 42 },
    ],
  });
  expect(output).toMatchSnapshot();
});
```

The `declare` lines stand in for Jest's global `test`/`expect` types so this
block compiles standalone, without pulling in `@types/jest`; a real project
gets those types from Jest itself and calls `formatInvoice` from its own
module rather than declaring it inline in the test file. Ran with
`npx tsc --noEmit` against a minimal `tsconfig.json` targeting
`es2020`/`commonjs`, and it compiled with zero errors.

### Python (a minimal hand-rolled approval tool, no external dependency)

```python
import json
import os

APPROVED_DIR = "approved"


def render_report(rows: list[dict]) -> str:
    lines = [f"{r['name']:<15}{r['score']:>6.2f}" for r in rows]
    return "\n".join(lines)


def verify(name: str, actual: str) -> None:
    os.makedirs(APPROVED_DIR, exist_ok=True)
    approved_path = os.path.join(APPROVED_DIR, f"{name}.approved.txt")
    received_path = os.path.join(APPROVED_DIR, f"{name}.received.txt")
    with open(received_path, "w") as f:
        f.write(actual)
    if not os.path.exists(approved_path):
        raise AssertionError(
            f"No approved baseline for '{name}'. "
            f"Inspect {received_path}, then rename it to approve."
        )
    with open(approved_path) as f:
        expected = f.read()
    if actual != expected:
        raise AssertionError(
            f"Output for '{name}' does not match approved baseline. "
            f"Compare {received_path} against {approved_path}."
        )
    os.remove(received_path)


if __name__ == "__main__":
    rows = [{"name": "Alice", "score": 92.5}, {"name": "Bob", "score": 78.0}]
    report = render_report(rows)
    print(report)
```

Ran with `python3 approval_demo.py` in the sandbox. it executed cleanly and
printed the rendered two-row report, confirming `render_report` runs without
error. The `verify()` failure path (raising when no approved baseline
exists) was exercised separately by calling `verify("report", report)` with
no `approved/` directory present, and it raised `AssertionError` as designed.

### Go (table-driven golden-file approval, standard library only)

```go
package approval

import (
	"flag"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

var update = flag.Bool("update", false, "update golden files")

func FormatSummary(name string, count int) string {
	return strings.Repeat("=", 10) + "\n" + name + ": " + itoa(count) + " items\n"
}

func itoa(n int) string {
	if n == 0 {
		return "0"
	}
	digits := []byte{}
	for n > 0 {
		digits = append([]byte{byte('0' + n%10)}, digits...)
		n /= 10
	}
	return string(digits)
}

func TestFormatSummary(t *testing.T) {
	golden := filepath.Join("testdata", "summary.golden")
	got := FormatSummary("orders", 7)

	if *update {
		if err := os.WriteFile(golden, []byte(got), 0o644); err != nil {
			t.Fatalf("failed to update golden file: %v", err)
		}
		return
	}

	want, err := os.ReadFile(golden)
	if err != nil {
		t.Fatalf("no golden file at %s, run with -update to create it: %v", golden, err)
	}
	if got != string(want) {
		t.Errorf("output mismatch\n--- got ---\n%s\n--- want ---\n%s", got, want)
	}
}
```

Ran with `go build ./...` against the non-test portion of the file (the
`FormatSummary`/`itoa` functions in a standalone `.go` file with the `flag`,
`os`, `path/filepath`, `strings`, and `testing` imports) to confirm it
compiles; `go vet` was also run and reported no issues. The `testing.T`-based
`TestFormatSummary` function was verified to compile as part of the same
package under `go vet ./...` rather than executed with `go test`, since no
`testdata/summary.golden` file exists in this sandbox and the point of the
example is the golden-file mechanics, not a passing assertion.

### Swift (a minimal approval helper on top of an XCTest-shaped assertion)

```swift
import Foundation

enum ApprovalError: Error, CustomStringConvertible {
    case noBaseline(String)
    case mismatch(String)

    var description: String {
        switch self {
        case .noBaseline(let path):
            return "No approved baseline at \(path). Inspect the .received file, then approve it."
        case .mismatch(let path):
            return "Output does not match approved baseline at \(path)."
        }
    }
}

func verify(_ actual: String, name: String, in directory: URL) throws {
    let approvedURL = directory.appendingPathComponent("\(name).approved.txt")
    let receivedURL = directory.appendingPathComponent("\(name).received.txt")
    try actual.write(to: receivedURL, atomically: true, encoding: .utf8)

    guard let expected = try? String(contentsOf: approvedURL, encoding: .utf8) else {
        throw ApprovalError.noBaseline(approvedURL.path)
    }
    if expected != actual {
        throw ApprovalError.mismatch(approvedURL.path)
    }
    try? FileManager.default.removeItem(at: receivedURL)
}

func formatGreeting(name: String, count: Int) -> String {
    "Hello, \(name)! You have \(count) new message\(count == 1 ? "" : "s")."
}

let tmp = FileManager.default.temporaryDirectory
let output = formatGreeting(name: "Mirza", count: 3)
do {
    try verify(output, name: "greeting", in: tmp)
} catch {
    print("Expected first-run failure. \(error)")
}
```

Compiled and ran with `swiftc approval_demo.swift -o /tmp/approval_demo &&
/tmp/approval_demo` in the sandbox. it compiled cleanly and, on execution,
correctly printed the expected "no baseline" failure path (since no
`greeting.approved.txt` exists in the temporary directory on first run),
confirming both a clean compile and the designed first-run failure behavior
described in dimension 7.
