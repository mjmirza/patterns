---
name: Golden Master
slug: golden-master
family: 14-testing
category: Testing
aliases: [Characterization Test, Approval Test, Snapshot Test, Approval Testing, Golden Master Testing]
first_described: "Feathers 2004"
maturity: established
related: [arrange-act-assert, four-phase-test, fresh-fixture, shared-fixture, test-data-builder, given-when-then, mock, fake]
incompatible_with: []
verified: 2026-08-02
---

# Golden Master

## 1. Name, aliases, and lineage

The canonical name used in this catalog is Golden Master, but the technique
travels under at least four names in day to day practice, and each name was
coined by a different community for a slightly different emphasis on the same
mechanism. capture the actual output a piece of code produces today, store it
as a reference file, and fail any future run whose output diverges from that
file until a person says the difference is intended.

Michael Feathers gave the earliest documented name for this technique inside
software testing literature. He called it a Characterization Test in his book
*Working Effectively with Legacy Code* (Prentice Hall, 2004, ISBN
0-13-117705-2). Wikipedia's summary of the term states the definition
plainly. "A characterization test is a means to describe (characterize) the
actual behavior of an existing piece of software, and therefore protect
existing behavior of legacy code against unintended changes via automated
testing" (Wikipedia contributors, "Characterization test,"
https://en.wikipedia.org/wiki/Characterization_test, verified 2026-08-02).
The same article states that Michael Feathers coined the term and that
"characterization test" is "also known as Golden Master Testing," treating
the two names as interchangeable descriptions of one practice rather than two
distinct techniques.

The name Golden Master itself is older than Feathers' book, but not as a
testing term. It was borrowed from the physical media industry, where the
"gold master" or "golden master" is the final, sealed build sent for mass
duplication once a release is signed off, a term Wikipedia traces to the record-industry practice
of preparing a master copy for physical duplication. "The RTM build is known as the 'gold master' or GM
[and] is sent for mass duplication or disc replication if applicable"
(Wikipedia contributors, "Software release life cycle,"
https://en.wikipedia.org/wiki/Software_release_life_cycle, verified
2026-08-02). Applied to testing, the borrowed sense is a reference copy that
is treated as authoritative once it has been reviewed and accepted, the same
role a gold master disc plays for a shipped product. This entry could not
find a single citable source that names the exact publication or person who
first repurposed "gold master" for a test fixture rather than a shipped
build, so that specific naming step is presented here as a reasonable
inference from the two sourced facts above, not as a sourced claim in its own
right.

Approval Test is the name preferred by the tool authors who built dedicated
libraries for this technique, most visibly the ApprovalTests family. Their
own documentation states the equivalence directly. Approval tests are "Also
known as Golden Master Tests or Snapshot Testing" (ApprovalTests.cpp project
documentation, https://github.com/approvals/ApprovalTests.cpp, verified
2026-08-02). The same page frames the workflow around human approval. "Unit
testing asserts can be difficult to use. Approval tests simplify this by
taking a snapshot of the results, and confirming that they have not
changed," with a developer approving the first captured result to establish
the reference (same source).

Snapshot Test is the name that reached the widest audience, largely through
Jest, the JavaScript test runner built at Facebook and now maintained under
the OpenJS Foundation. Jest's own documentation gives the clearest short
statement of the mechanism in general use today. "A typical snapshot test
case renders a UI component, takes a snapshot, then compares it to a
reference snapshot file stored alongside the test. The test will fail if the
two snapshots do not match. either the change is unexpected, or the
reference snapshot needs to be updated to the new version of the UI
component" (Jest documentation, "Snapshot Testing,"
https://jestjs.io/docs/snapshot-testing, verified 2026-08-02).

Reading all four sources together, the honest lineage is this. Feathers named
and popularized the underlying discipline for legacy code in 2004 and called
it Characterization Testing. The wider practitioner community, independently
and before and after that book, had already been calling the same mechanism
Golden Master Testing by analogy with the manufacturing sense of a reference
master copy. Tool builders in the 2000s and 2010s formalized the workflow
under the name Approval Testing, emphasizing the human review step. Front-end
tooling in the 2010s popularized the same mechanism again under the name
Snapshot Testing, emphasizing the act of capturing a point in time. None of
the four names describes a technically different mechanism. they describe
the same mechanism through the lens of legacy-code safety, of a reference
artifact, of a review workflow, and of a captured moment, in that order.

## 2. Problem and context

A piece of code produces output that is expensive or awkward to specify by
hand, one field at a time, and a person needs confidence that a change to the
code did not alter that output in a way nobody intended.

The situation shows up in a recognizable shape. A report generator turns a
set of database rows into a formatted page. A code formatter turns a parse
tree back into source text with specific spacing and line breaks. A
serializer turns an object graph into JSON, XML, or a binary wire format. A
rendering pipeline turns component state into HTML or into pixels. In every
one of these cases the correct output is a large, structured artifact, and
writing an assertion for every individual field, indentation choice, or pixel
would take longer to maintain than the code under test, and would drift out
of sync with the code the moment a legitimate formatting change landed.

A second, distinct situation motivates the same technique for a different
reason. A codebase has no test suite at all, the original author is gone, and
somebody now needs to refactor it. Feathers' framing of this case is the one
that gave the technique its first name. the actual current behavior of the
code, correct or not, is the only specification that exists, and a safety net
has to be built from that behavior before any structural change is safe to
attempt. In this context the reference output is not asserted to be
*correct*. it is asserted to be *unchanged*, which is a materially weaker and
more honest claim, and dimension 4 explains exactly where that distinction
matters.

Both situations share the same context that makes the technique the right
choice rather than a shortcut around writing real tests. the system under
test is deterministic given its inputs, its output can be serialized to a
comparable text or byte form, and a person is available, now or later, to
review a diff and decide whether it represents an intended change or a
regression. Remove any one of those three conditions and the technique either
cannot function or degrades into the misuse patterns catalogued in dimension
11.

## 3. Forces

- **Speed of test authoring.** Favoured, strongly, on the first run. Writing
  one call that captures whatever the system currently produces costs a
  fraction of the time it takes to write field-by-field assertions against a
  large structured output. This is the force that makes the technique
  attractive for legacy code with zero existing coverage.
- **Precision of the failure signal.** Sacrificed. A traditional assertion
  that fails names the exact field, the exact expected value, and the exact
  actual value in one line. A golden master failure names a diff across
  potentially the entire artifact, and a reader has to scan the diff to find
  the part that matters, which is slower per failure even though it was
  faster per test written.
- **Coverage of untested legacy code.** Favoured, and this is the force
  Feathers built the technique to serve. A characterization test can wrap
  code nobody understands well enough to write a correctness assertion for,
  because it asserts sameness rather than correctness.
- **Correctness versus stability.** In direct tension, and the tension is the
  central design question of the whole technique. A golden master proves the
  output did not change. It proves nothing about whether the captured output
  was right in the first place. A bug frozen into a golden file at capture
  time passes every subsequent run.
- **Determinism.** Non-negotiable rather than a matter of degree. Any
  non-deterministic input, current time, an unfixed random source, iteration order over an
  unordered collection, floating point formatting that varies by platform,
  turns every future run into a coin flip between a real regression and
  noise, and the fix always has to happen at the boundary of the system under
  test, never inside the comparison step.
- **Diff signal versus diff noise.** Favoured when the artifact is small and
  focused, sacrificed as the artifact grows. A ten line receipt diff is
  readable at a glance. A four thousand line rendered HTML page diff, where
  one attribute reordering touches every element, buries the one line that
  matters under thousands that do not.
- **Human review cost.** This is the cost the technique trades speed of
  authoring against. Every intentional change to the system under test now
  requires a person to look at a diff and click approve, which does not
  happen with hand written assertions, where the developer who wrote the new
  expected value already reviewed it by typing it.
- **Refactoring safety.** Favoured, and this is Feathers' primary intended
  use. a wide, shallow safety net around code that is about to be
  restructured, cheap enough to build that it gets built at all, in contrast
  to no safety net, which is the realistic alternative for code this
  expensive to specify by hand.

## 4. Applicability and non-applicability

Reach for Golden Master when the following hold.

- The output is large, structured, and expensive to specify field by field.
  formatted documents, rendered markup, serialized payloads, generated code,
  compiler or formatter output, report text.
- The code has no existing test coverage and a refactor or a migration is
  about to touch it. the goal for this first pass is stability, not
  correctness, and that goal is explicit to everyone reading the tests.
- The system under test is deterministic given a fixed input, or can be made
  deterministic by controlling the non-deterministic inputs at the boundary
  (an injected clock, a random source pinned to a fixed value, a stable sort).
- A human reviewer genuinely exists and genuinely will look at diffs before
  approving them. the technique assumes a review step is part of the
  workflow, not an optional extra.
- The cost of a missed regression in this particular output is bounded and
  recoverable, because the technique trades assertion precision for coverage
  breadth, and a precise failure will sometimes be buried in a large diff.

Do NOT reach for Golden Master in these cases, and the reason matters more
than the rule.

- **The behavior is a well understood, narrow calculation.** A tax
  calculation, a discount rule, a state machine transition. Here a small
  number of hand written example-based assertions, ideally paired with
  property-based tests per dimension 12, name the expected value directly
  and catch a wrong value on the very first run, which a golden master
  cannot do, since a golden master captures whatever the buggy calculation
  currently returns and calls it correct forever after.
- **The system is non-deterministic and cannot be made deterministic at a
  boundary.** Output that depends on wall clock time, network latency,
  concurrent goroutine or thread scheduling order, or an unseeded random
  generator will produce a stream of unrelated diffs that trains the team to
  stop reading them, which is the rubber stamping failure mode in dimension
  11.
- **Nobody will review the diffs.** A golden master test suite whose failures
  are always resolved by running the update command without reading the
  output is strictly worse than no test, because it consumes CI time and
  reviewer attention while providing zero actual protection. The technique
  is a review workflow with an automated diff step attached, not an
  automated correctness oracle.
- **The reference output was never verified correct at capture time.** Using
  this technique as the *only* test for new code, rather than as a
  supplement to hand written assertions, bakes an unverified guess into a
  file that everyone will subsequently trust as ground truth. This is the
  single most damaging misuse of the technique and it is covered in depth in
  dimension 11.
- **The output format itself is the thing under active design.** While a
  team is still deciding what a report or a rendered page should look like,
  every legitimate design iteration produces a diff that has to be approved,
  which turns the review step into ceremony rather than protection. Wait
  until the format stabilizes.
- **A cheaper, more precise technique already exists for this exact
  behavior.** If the output can be decomposed into independently assertable
  pieces without excessive cost, ordinary example-based assertions using
  Arrange-Act-Assert give a sharper failure message for the same or lower
  authoring cost, and should be preferred. Golden Master is the technique for
  when that decomposition is genuinely not worth doing, not the default for
  every test.

## 5. Structure

Five participants, named by the role each plays in the workflow rather than
by a class name, because the technique is a process as much as it is a piece
of code.

- **System Under Characterization (SUC).** The function, module, or pipeline
  whose output is being captured. It must be reachable through a single call
  with a controllable input, and it must be deterministic given that input.
- **Reference Output.** The stored artifact, usually a file on disk beside
  the test, sometimes an inline string in the test source itself, that
  represents the last approved output of the SUC. This is the file the
  approaches above call the golden file, the snapshot, or the approved file.
- **Test Runner.** The code that drives one execution. it invokes the SUC
  with a fixed input, serializes the result into a comparable text or byte
  form, and hands both the serialized result and the reference output to the
  comparator. This is also the point where a redaction or scrubbing step
  removes genuinely non-deterministic fragments, such as a generated
  timestamp, before comparison.
- **Comparator.** The component that decides whether the fresh output matches
  the reference output, and produces a diff when it does not. In the
  simplest implementations this is a byte for byte or line for line text
  comparison. More capable implementations understand the artifact's
  structure, for example a JSON-aware or DOM-aware comparator that ignores
  key ordering or whitespace that carries no meaning.
- **Approval Mechanism.** The step, invoked by a person, that promotes a
  freshly produced output to become the new reference output after the
  person reviews the diff and judges the change intentional. This is a first
  class part of the technique, not an afterthought, and every mature
  implementation gives it a dedicated command, such as `jest --updateSnapshot`
  or a file rename from a received copy to an approved copy.

## 6. ASCII structure diagram

```
   +------------------------+        input        +------------------------+
   |       Test Runner      |  -----------------> | System Under            |
   |------------------------|                      | Characterization (SUC) |
   | drives one execution   |  <----------------- |------------------------|
   | serializes the result  |     raw output       | deterministic given    |
   | applies redaction      |                      | its input              |
   +------------------------+                      +------------------------+
              |
              | serialized, redacted output
              v
   +------------------------+   reads    +------------------------+
   |      Comparator        | <--------- |    Reference Output    |
   |------------------------|            |------------------------|
   | diffs fresh vs stored  |            | file on disk, or an    |
   +------------------------+            | inline snapshot string |
              |                          +------------------------+
        match | mismatch                            ^
              |                                      |
        PASS  |                              promotes on approval
              v                                      |
   +------------------------+   diff shown to   +------------------------+
   |       Test Result      | ----------------> |   Approval Mechanism   |
   |    (green or red)      |                    | (a human decides)     |
   +------------------------+                    +------------------------+
```

## 7. Dynamics

Three distinct flows exist, and confusing them is the source of most
practical confusion about how this technique behaves. only one of the three
runs on an ordinary CI pass.

```
FLOW 1. First run, no reference output exists yet.

Test Runner        SUC              Comparator        Reference Output
    |               |                    |                    |
    |-- invoke() -->|                    |                    |
    |<-- output ----|                    |                    |
    |-- serialize -------------------------------------------->|
    |               |                    |          (file written,
    |               |                    |           test usually
    |               |                    |           marked as a
    |               |                    |           new capture,
    |               |                    |           not a pass)
```

```
FLOW 2. Ordinary run, reference output already exists. This is the flow
that runs on every CI pass once a suite is established.

Test Runner        SUC              Comparator        Reference Output
    |               |                    |                    |
    |-- invoke() -->|                    |                    |
    |<-- output ----|                    |                    |
    |-- serialize -->|                   |                    |
    |                |-- compare ------->|<-- read -----------|
    |                |                   |                    |
    |                |     match -----> PASS                  |
    |                |     mismatch --> FAIL, diff produced    |
```

```
FLOW 3. Approval, run by a person after reviewing a FAIL diff from Flow 2
and judging the new output correct.

Person          Approval Mechanism         Reference Output
  |                     |                        |
  |-- reviews diff ---->|                        |
  |-- approves -------->|                        |
  |                     |-- overwrite ---------->|
  |                     |   (fresh output becomes|
  |                     |    the new reference)  |
```

Two timing notes. First, Flow 1 must never be silently treated as a pass in
CI, because that would mean the very first capture, potentially of buggy
output, becomes the accepted baseline with no human ever looking at it. Most
mature tools mark a first capture as requiring explicit approval before the
next run can pass. Second, Flow 3 is deliberately out of band from ordinary
CI, run locally by a developer or in an interactive review tool, precisely
because approving a change is a judgment call that automation cannot make on
a person's behalf.

## 8. Implementation variants

**Hand rolled file comparison.** The oldest and simplest form. a test writes
the SUC's output to a file, or reads a fixed testdata file, and compares
strings directly, with a command line flag that switches the test from
verify mode to write mode. The Go standard library's own `go/printer` tests
use exactly this shape without any third party library, described further in
dimension 9.

**Dedicated library with an interactive approval step.** ApprovalTests,
available across languages including Java, .NET, C++, and Python, adds a
naming convention that derives the reference file path from the test name,
a comparator that can be swapped per data type, and a "reporter" abstraction
that opens a diff tool automatically on mismatch so a developer reviews the
change visually rather than reading raw text.

**Inline snapshots versus external file snapshots.** Jest and the Rust
`insta` crate both support writing the reference value directly inside the
test source as a string literal, rewritten in place by the update command,
in addition to storing it in a separate file. Inline snapshots keep small,
frequently reviewed values next to the assertion that uses them, at the cost
of noisy diffs in the test file itself. External file snapshots keep the
test file readable at the cost of a separate file to open and check.

**Redaction and scrubbing of non-deterministic fields.** Every mature
implementation provides a mechanism to normalize or remove values that would
otherwise make every run produce a spurious diff, timestamps, generated
identifiers, absolute file paths, memory addresses. `insta` calls this
redaction and lets a test declare a path expression whose value is replaced
with a placeholder before comparison. Doing this correctly is the difference
between a golden master suite that is trusted and one that is muted because
every run shows unrelated noise, see dimension 11.

**Structure aware comparison.** A plain text diff treats a JSON document
with keys in a different order, or an HTML document with an extra
insignificant whitespace character, as a full mismatch. A structure aware
comparator parses both sides into a JSON tree, a DOM tree, or an AST before
comparing, so that a reordering that carries no semantic meaning does not
produce a false failure. This variant trades comparator complexity for a
much lower false positive rate on documents with well defined structure.

**Partial or masked golden master.** Rather than comparing an entire large
artifact, the reference output is reduced to only the fields the team has
decided are worth protecting, for example the visible text of a rendered
page while ignoring internal element identifiers. This is a deliberate
narrowing of dimension 3's coverage force in exchange for a much smaller,
more readable diff, and it works well once a team has enough experience with
a full golden master to know which parts of the output actually matter.

**Visual, image based golden master.** The reference artifact is a rendered
bitmap rather than text, and the comparator is a pixel or perceptual image
diff rather than a text diff. This variant is common in UI regression
tooling and carries a distinct set of forces, most notably that
anti-aliasing and font rendering differences across operating systems make
byte identical image comparison unreliable, which pushes implementations
toward a similarity threshold rather than exact equality, trading precision
for portability.

## 9. Known production uses

**Jest snapshot testing, used across React and the wider JavaScript
community.** Jest, originally built at Facebook and now maintained as an
OpenJS Foundation project, ships `toMatchSnapshot()` as a first class
assertion. its own documentation describes the mechanism as rendering a
component, comparing the render to a stored reference file, and failing when
they diverge, with an explicit update command for intentional changes. Jest
documentation, "Snapshot Testing," https://jestjs.io/docs/snapshot-testing,
verified 2026-08-02.

**The Go standard library's `go/printer` package.** Go's own source
formatter is tested against a directory of golden files. The test source
defines a command line flag stating its purpose directly. "Use go test
-update to create/update the respective golden files." Each test case pairs
an `.input` source file with a `.golden` expected output file, and the test
either compares against the golden file or, when the update flag is passed,
overwrites it with the fresh formatter output. Go project source,
`src/go/printer/printer_test.go`,
https://github.com/golang/go/blob/master/src/go/printer/printer_test.go,
verified 2026-08-02.

**The ApprovalTests family of libraries.** ApprovalTests began as a Java and
.NET library and now ships ports for numerous languages including C++,
Python, and Go, all implementing the same approval workflow around a common
naming convention for reference files. The C++ port's own documentation
states plainly that the technique it implements is "Also known as Golden
Master Tests or Snapshot Testing." ApprovalTests.cpp project documentation,
https://github.com/approvals/ApprovalTests.cpp, verified 2026-08-02.

**The `insta` snapshot testing crate for Rust.** `insta`, created and
maintained by Armin Ronacher, is a widely adopted snapshot testing library
among Rust projects, supporting inline and external snapshots across
several serialization formats and shipping an interactive review tool,
`cargo-insta`, for approving pending snapshots. Its own description frames
the mechanism directly against ordinary assertions, describing a snapshot
test as one that "asserts values against a reference value (the snapshot)"
and presenting it as a strictly more capable replacement for a plain
`assert_eq!` call. insta project documentation, https://insta.rs/, verified
2026-08-02.

## 10. Consequences

**Positive.**

- A large, structured output gets test coverage in the time it takes to
  write one call, rather than the time it would take to enumerate every
  field by hand.
- Legacy code with no prior tests gains a safety net cheap enough that it
  actually gets built before a risky refactor, where the realistic
  alternative was usually no safety net at all.
- A regression in any part of a captured output, including a part nobody
  thought to write a specific assertion for, produces a visible diff, so the
  technique protects against the unknown unknowns that hand written
  assertions by construction cannot cover.
- The reference file doubles as living, always current documentation of
  exactly what the system currently produces, which is easier to read for a
  newcomer than a page of individual assertions.
- The approval workflow makes every intentional output change visible in
  code review as an explicit diff, which is a stronger review signal for
  formatting or serialization changes than a passing test suite that
  happened not to assert the changed field.

**Negative.**

- A test failure names a diff, not a specific wrong value, so diagnosing the
  actual cause of a regression usually takes longer per failure than reading
  a traditional assertion message.
- The technique proves stability, never correctness. A bug present at
  capture time is frozen into the reference file and will pass forever
  unless someone independently notices it is wrong.
- Reference files, especially large ones, are a magnet for source control
  merge conflicts, since two branches that both regenerate the same golden
  file in different ways cannot be merged automatically.
- The technique depends entirely on a person actually reading every diff.
  once the review step degrades into reflexively running the update command,
  the tests provide the appearance of coverage with none of its substance,
  see dimension 11.
- Non-deterministic inputs anywhere in the call path, an unseeded random
  source, wall clock time, unordered iteration, produce flaky diffs that
  erode trust in the whole suite faster than an equivalent number of flaky
  traditional assertions would, because a golden master flake is usually a
  large, hard to read diff rather than one obviously wrong number.

## 11. Failure modes and misuse

**Symptom.** The same test fails on every run with a slightly different
diff, even though nothing in the feature changed.
**Cause.** A non-deterministic value, most commonly a timestamp, a generated
identifier, an unordered map or set serialized without a stable sort, or a
floating point number formatted differently across platforms, leaks into the
captured output.
**Fix.** Control the non-determinism at the boundary of the system under
test, an injected clock, a random source pinned to a fixed value, a stable sort before
serialization, rather than trying to make the comparator tolerant of it. A
comparator level workaround, ignoring the offending field entirely, is
acceptable only when the field is confirmed to carry any real signal.

**Symptom.** CI shows dozens of golden file diffs on an unrelated pull
request, and the reviewer clicks the update command without reading a single
one.
**Cause.** Rubber stamping. once a team has been trained by repeated,
unreadable, or noisy diffs that the update command is safe to run reflexively,
the review step that makes the technique worth trusting has silently stopped
happening, and the tests continue to run green while providing no actual
protection.
**Fix.** Shrink the artifact each individual test protects so that a diff is
readable at a glance, add a structure aware comparator so incidental
reordering stops producing noise, and treat a large batch of simultaneous
snapshot updates as a signal to review a small number of representative
diffs by hand rather than accepting all of them at once.

**Symptom.** A refactor that is a pure behavior preserving code move somehow
produces a golden master diff.
**Cause.** The captured output leaked an implementation detail that was
never part of the actual contract, an internally generated identifier, a
class name embedded in an error message, an object's memory address in a
debug representation.
**Fix.** Narrow what the test captures to the part of the output that is
actually the contract, using a partial or masked golden master per dimension
8, or add the leaking field to the redaction list.

**Symptom.** A test suite that started as a temporary safety net for a
one-time refactor is still the only test coverage for a module two years
later, and nobody can say with confidence whether the captured behavior is
correct.
**Cause.** Characterization tests were never graduated into explicit,
correctness asserting tests once the original refactor was finished and the
team understood the code well enough to write them, which was always the
intended second step in Feathers' own account of the technique.
**Fix.** Follow the refactoring path in dimension 14. once the code is
understood, replace the highest value characterization tests with explicit
assertions that state the expected behavior, and keep the golden master
tests only for the genuinely bulky, low-value-per-line output that does not
justify hand written assertions.

**Symptom.** A newly written feature ships with only a golden master test,
and a bug present in the very first captured output survives untouched
through several releases.
**Cause.** The technique was used as the sole specification for new code
rather than as a supplement to hand written correctness assertions. nothing
in the workflow ever asked whether the first captured output was actually
right, only whether later output matched it.
**Fix.** Treat Golden Master as a technique for legacy code and for bulky,
low-signal output on top of an existing, understood system, never as the
primary test for new, unverified behavior. New code gets example-based or
property-based assertions first, per dimension 12, with a golden master
added afterward if the output is genuinely too large to specify by hand.

## 12. Trade-off matrix

Compared against the named alternatives that address the same underlying
need, coverage of behavior under test, across the forces from dimension 3.

| Force | Golden Master | Example-Based Assertions | Property-Based Testing | Contract Testing |
|---|---|---|---|---|
| Speed to first coverage on legacy code | Fast, one capture call | Slow, one assertion per field | Slow, requires a property statement | Slow, requires a contract definition |
| Precision of the failure message | Low, a diff across the artifact | High, names the exact field and value | Medium, names the failing input, not the field | High, names the violated contract clause |
| Protects against unknown unknowns | Strong, any field can regress | Weak, only asserted fields are checked | Strong, within the property's input space | Weak, only within the contract's stated shape |
| Proves correctness, not only stability | No | Yes, if the expected value was verified | Yes, for the stated property | Yes, for the stated contract |
| Requires a human review step to stay worth trusting | Yes, on every approval | No | No | Sometimes, on contract renegotiation |
| Suitable for code nobody currently understands | Yes, this is its primary intended use | No, requires knowing the correct value | No, requires knowing the correct property | No, requires knowing the correct contract |
| Behavior under non-deterministic inputs | Poor, without explicit control at the boundary | Good, per assertion | Good, generators can be pinned to a fixed value | Good |

## 13. Related and incompatible patterns

**Arrange-Act-Assert and Four-Phase Test.** A golden master test still has an
arrange step, an act step that invokes the system under characterization,
and a check step, it is only the assert phase that is replaced by a
comparator against a stored reference rather than a literal expected value.
The structural shape composes cleanly with both patterns.

**Fresh Fixture and Shared Fixture.** The determinism force from dimension 3
makes Fresh Fixture the safer default for a golden master test's input data,
since a Shared Fixture that another test mutates would make the captured
output depend on execution order, producing exactly the flaky diffs
catalogued in dimension 11.

**Test Data Builder.** Building the deterministic, controlled input that a
golden master test feeds to the system under characterization is a natural
job for a Test Data Builder, which keeps the input construction readable
even when the underlying object graph is large.

**Property-Based Testing.** The two techniques are complementary rather than
competing once a team is past the initial legacy code safety net stage.
Golden Master protects a specific, currently observed shape of output.
Property-based testing protects an invariant across a wide space of inputs
the team may never have thought to capture by hand. A mature suite often
uses golden master tests for a handful of representative, realistic inputs
and a property-based test for the algebraic invariants the same code should
satisfy for every input.

**Mutation Testing.** A golden master test suite can pass while catching
almost nothing, if the captured output happens not to depend on the part of
the code that changed. Mutation testing is the technique that verifies a
golden master suite is actually earning its keep, by deliberately injecting
small faults into the system under characterization and confirming that the
existing golden master tests fail as a result.

**Tension with Test-Driven Development.** Not an incompatibility, but a real
tension worth stating plainly. TDD's red-green-refactor cycle asks for a
failing test written before the code exists. A golden master test is, by
construction, captured from code that already exists and passes on its very
first real run, which is the opposite starting state. The two are reconciled
in practice by scope. TDD governs new behavior being written now. Golden
Master governs existing behavior nobody is confident enough to specify from
scratch, most often during the interval described in dimension 14.

## 14. Refactoring path in and out

**Introducing a golden master, following the workflow Feathers describes for
legacy code.**

1. Identify the smallest reasonable seam around the code that is about to be
   refactored, ideally a single function or module with a narrow entry
   point, so that capturing its output does not also capture the behavior of
   unrelated collaborators.
2. Choose or construct a small number of representative inputs that
   exercise the paths the refactor is going to touch, using a Test Data
   Builder if the inputs are large objects.
3. Write the capture call and run it once to generate the reference output,
   then read that output by hand before trusting it. this is the one point
   in the whole workflow where a person is looking at unverified output, and
   skipping this read is how a bug becomes permanently frozen behavior, per
   dimension 11.
4. Commit the reference output alongside the test, and run the suite to
   confirm it passes on the unmodified code, establishing the baseline the
   refactor will be checked against.
5. Perform the refactor in small steps, running the golden master suite
   after each step. any diff at this stage is either a bug the refactor
   introduced, requiring a fix, or evidence that the refactor was not in fact
   behavior preserving, requiring a decision about whether the new behavior
   is intentional.
6. Once the refactor is complete and the suite is green with no diffs, the
   golden master tests have done their job for this change.

**Retiring a golden master once it has served its purpose.**

1. As the team's understanding of the refactored code grows, identify the
   specific behaviors that are now well enough understood to state as
   explicit assertions, expected values a person can name and justify
   directly, rather than values that are merely observed to be stable.
2. Write example-based or property-based tests for those specific behaviors,
   using Arrange-Act-Assert, and confirm they pass against the current code.
3. Remove the corresponding coverage from the golden master's scope, either
   by deleting the golden master test entirely if the new tests fully
   subsume it, or by narrowing what the golden master captures per the
   partial golden master variant in dimension 8, so the two do not
   needlessly duplicate coverage of the same behavior.
4. Keep golden master coverage only for the parts of the output that remain
   genuinely too large or too low value per line to specify by hand, which
   is frequently a much smaller surface than the one the technique started
   with.

## 15. Testing and verification

Testing code that itself uses a golden master test raises one meta question.
how does a team know the golden master suite would actually catch a real
regression, rather than passing regardless of what the code does. Three
practices answer this directly.

- **Verify the very first capture by hand, every time.** This is not
  optional, and it is the only step in the whole technique that substitutes
  for a traditional assertion's built-in correctness check. Skipping it, as
  covered in dimension 11, is the root cause of a bug frozen permanently
  into a reference file.
- **Run mutation testing against the code under characterization.**
  Deliberately introduce a small, targeted fault, flip a comparison
  operator, drop a line, change an off by one boundary, and confirm the
  golden master suite goes red. A golden master test that survives a real
  fault untouched is providing false confidence and its scope needs
  widening or its comparator needs sharpening.
- **Treat the update command as a reviewable diff, never as a silent
  passthrough.** Wire the update step so that it always produces something a
  reviewer sees, whether that is a git diff in a pull request or an
  interactive prompt in a local tool, rather than a script that regenerates
  every reference file and commits the result unattended.

A golden master test is comparatively easy to make deterministic once the
non-deterministic inputs are identified, because the fix is almost always
the same shape, inject a fake clock, pin the random source to a fixed value, sort
before serializing, and this is worth doing early, since a flaky golden
master suite loses the team's trust faster than a flaky traditional suite.

## 16. Observability signals

- **Diff size per approval, tracked over time.** A shrinking median diff
  size across approvals is a healthy sign that the team is narrowing what
  each golden master actually protects, per the partial golden master
  variant. A growing median diff size is a sign the reference artifact is
  accumulating unrelated content.
- **Update frequency per reference file.** A reference file approved on
  nearly every commit is either tracking a fast moving, actively designed
  output, which is expected and fine, or it is capturing a non-deterministic
  value that should be redacted, which needs investigation.
- **Ratio of approvals reviewed versus approvals accepted in bulk.** If a
  team's tooling can distinguish an interactive, one at a time approval from
  a batch update command run against every pending snapshot, a rising share
  of bulk acceptances is the earliest observable signal of the rubber
  stamping failure mode in dimension 11.
- **Count of golden master tests still uncomplemented by any explicit
  assertion, per module, over time.** A module whose only coverage remains
  golden master tests long after the original refactor that introduced them
  finished is a signal that dimension 14's graduation step has stalled.
- **CI flake rate specifically attributable to golden master failures.** A
  flake rate materially higher than the rest of the suite almost always
  traces back to an uncontrolled non-deterministic input, and is worth
  isolating from the general test flake metric because the fix is a
  different kind of work.

## 17. Security and privacy implications

Reference output files are committed to source control and, unlike most test
fixtures, are frequently generated by copying real or realistic production
data through the system under characterization rather than being written by
hand. This creates a specific, easy to miss exposure. a captured HTTP
response fixture, a rendered customer facing document, or a serialized
record pulled from a staging database can carry personal data, an
authentication token, an internal hostname, or another secret directly into
a reference file that then lives permanently in git history, readable to
anyone with repository access and effectively impossible to fully remove
once it has been pushed and cloned elsewhere.

The redaction mechanism described in dimension 8 is a security control as
much as a determinism control, and should be treated that way in review. any
input path a golden master test captures from a source that could plausibly
carry real user data, a recorded API response, an imported sample dataset, a
staging database dump, deserves an explicit review for what fields the
reference file will contain before that file is committed, not after.
Synthetic, hand constructed input data built through a Test Data Builder
avoids the exposure entirely and is the safer default whenever the system
under characterization does not specifically require a realistic production
shaped input.

Where a golden master captures generated code, configuration, or
infrastructure templates, the reference file can also become a place where a
stale but still valid credential, a hardcoded internal URL, or an outdated
security setting sits unreviewed for a long time, since the whole point of
the technique is that a matching diff produces no attention at all. a
periodic audit of what long lived reference files actually contain, separate
from the routine pass or fail signal, closes this gap.

## 18. References

1. Michael Feathers. *Working Effectively with Legacy Code*. Prentice Hall,
   2004. ISBN 0-13-117705-2. Source of the term Characterization Test and
   the legacy code refactoring workflow described in dimensions 2 and 14.
   Bibliographic details confirmed via Open Library,
   https://openlibrary.org/isbn/0131177052.json, verified 2026-08-02.
2. Wikipedia contributors. "Characterization test."
   https://en.wikipedia.org/wiki/Characterization_test
   Verified 2026-08-02. Source for the definition quoted in dimension 1 and
   for the attribution of the term to Michael Feathers, and for the
   equivalence with Golden Master Testing.
3. Wikipedia contributors. "Software release life cycle."
   https://en.wikipedia.org/wiki/Software_release_life_cycle
   Verified 2026-08-02. Source for the manufacturing-industry origin of the
   term "gold master" quoted in dimension 1.
4. ApprovalTests.cpp project documentation.
   https://github.com/approvals/ApprovalTests.cpp
   Verified 2026-08-02. Source for the Approval Test naming, the stated
   equivalence with Golden Master Tests and Snapshot Testing, and the
   ApprovalTests production use in dimension 9.
5. Jest documentation. "Snapshot Testing."
   https://jestjs.io/docs/snapshot-testing
   Verified 2026-08-02. Source for the Snapshot Test naming and mechanism
   description in dimension 1, and the Jest production use in dimension 9.
6. Go project source. `src/go/printer/printer_test.go`.
   https://github.com/golang/go/blob/master/src/go/printer/printer_test.go
   Verified 2026-08-02. Source for the Go standard library golden file
   production use in dimension 9.
7. Armin Ronacher and contributors. `insta` project documentation.
   https://insta.rs/
   Verified 2026-08-02. Source for the `insta` production use in dimension
   9 and the redaction and inline snapshot variants in dimension 8.

## Code examples

The four examples below implement the same scenario in TypeScript, Python,
Go, and Swift. a plain text receipt formatter, tested by comparing its
output against a stored reference file, with a flag or environment variable
that switches the test from verify mode into update mode. The Go example
follows the same shape the Go standard library itself uses for its printer
package golden files, described in dimension 9.

```typescript
// receipt.ts. the system under characterization, and a minimal golden
// master test runner with no external test framework dependency.

interface LineItem {
  readonly name: string;
  readonly quantity: number;
  readonly unitPriceCents: number;
}

interface Order {
  readonly id: string;
  readonly items: readonly LineItem[];
}

function formatCents(cents: number): string {
  const sign = cents < 0 ? "-" : "";
  const abs = Math.abs(cents);
  const dollars = Math.floor(abs / 100);
  const remainder = abs % 100;
  return `${sign}$${dollars}.${remainder.toString().padStart(2, "0")}`;
}

function renderReceipt(order: Order): string {
  const lines: string[] = [`Order ${order.id}`, "-".repeat(24)];
  let totalCents = 0;
  for (const item of order.items) {
    const lineTotal = item.quantity * item.unitPriceCents;
    totalCents += lineTotal;
    lines.push(
      `${item.name.padEnd(14)} x${item.quantity}  ${formatCents(lineTotal)}`,
    );
  }
  lines.push("-".repeat(24));
  lines.push(`Total${" ".repeat(19 - "Total".length)}${formatCents(totalCents)}`);
  return lines.join("\n") + "\n";
}

// --- Golden master runner. no framework, so the sample stays runnable
// with only "tsc --noEmit" and needs no test dependency installed.

interface GoldenCase {
  readonly name: string;
  readonly order: Order;
}

interface FileSystemLike {
  readFile(path: string): string | undefined;
  writeFile(path: string, contents: string): void;
}

function runGoldenMasterSuite(
  cases: readonly GoldenCase[],
  fs: FileSystemLike,
  update: boolean,
): { passed: number; failed: string[] } {
  const failed: string[] = [];
  let passed = 0;
  for (const testCase of cases) {
    const path = `testdata/${testCase.name}.golden`;
    const actual = renderReceipt(testCase.order);
    const reference = fs.readFile(path);
    if (update || reference === undefined) {
      fs.writeFile(path, actual);
      passed += 1;
      continue;
    }
    if (reference === actual) {
      passed += 1;
    } else {
      failed.push(testCase.name);
    }
  }
  return { passed, failed };
}

export { renderReceipt, runGoldenMasterSuite, Order, LineItem };
```

```python
# receipt.py. the system under characterization, and a minimal golden
# master test runner using only the standard library.

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class LineItem:
    name: str
    quantity: int
    unit_price_cents: int


@dataclass(frozen=True)
class Order:
    id: str
    items: tuple[LineItem, ...]


def format_cents(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    absolute = abs(cents)
    dollars, remainder = divmod(absolute, 100)
    return f"{sign}${dollars}.{remainder:02d}"


def render_receipt(order: Order) -> str:
    lines = [f"Order {order.id}", "-" * 24]
    total_cents = 0
    for item in order.items:
        line_total = item.quantity * item.unit_price_cents
        total_cents += line_total
        lines.append(
            f"{item.name:<14} x{item.quantity}  {format_cents(line_total)}"
        )
    lines.append("-" * 24)
    label = "Total"
    lines.append(f"{label}{' ' * (19 - len(label))}{format_cents(total_cents)}")
    return "\n".join(lines) + "\n"


def golden_master_check(name: str, actual: str, update: bool = False) -> bool:
    """Compares actual output against testdata/<name>.golden.

    Returns True on a match or a fresh capture, False on a mismatch.
    Set update=True, or the UPDATE_GOLDEN environment variable, to
    write the fresh output as the new reference.
    """
    path = Path("testdata") / f"{name}.golden"
    should_update = update or os.environ.get("UPDATE_GOLDEN") == "1"
    if should_update or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(actual)
        return True
    reference = path.read_text()
    return reference == actual


def _sample_order() -> Order:
    return Order(
        id="A-1042",
        items=(
            LineItem(name="Espresso", quantity=2, unit_price_cents=350),
            LineItem(name="Croissant", quantity=1, unit_price_cents=425),
        ),
    )


def test_receipt_matches_golden_master() -> None:
    actual = render_receipt(_sample_order())
    assert golden_master_check("receipt_two_items", actual)
```

```go
// receipt.go. the system under characterization, and a golden file test
// in the same shape the Go standard library uses for src/go/printer.

package receipt

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// -update mirrors the flag the Go standard library's own printer tests
// define, so a maintainer already familiar with that convention finds
// this test immediately readable.
var update = flag.Bool("update", false, "update golden files")

type LineItem struct {
	Name           string
	Quantity       int
	UnitPriceCents int
}

type Order struct {
	ID    string
	Items []LineItem
}

func formatCents(cents int) string {
	sign := ""
	if cents < 0 {
		sign = "-"
		cents = -cents
	}
	dollars := cents / 100
	remainder := cents % 100
	return fmt.Sprintf("%s$%d.%02d", sign, dollars, remainder)
}

func RenderReceipt(order Order) string {
	var b strings.Builder
	fmt.Fprintf(&b, "Order %s\n", order.ID)
	b.WriteString(strings.Repeat("-", 24) + "\n")
	totalCents := 0
	for _, item := range order.Items {
		lineTotal := item.Quantity * item.UnitPriceCents
		totalCents += lineTotal
		fmt.Fprintf(&b, "%-14s x%d  %s\n", item.Name, item.Quantity, formatCents(lineTotal))
	}
	b.WriteString(strings.Repeat("-", 24) + "\n")
	label := "Total"
	padding := strings.Repeat(" ", 19-len(label))
	fmt.Fprintf(&b, "%s%s%s\n", label, padding, formatCents(totalCents))
	return b.String()
}

func checkGolden(t *testing.T, name string, actual string) {
	t.Helper()
	path := filepath.Join("testdata", name+".golden")
	if *update {
		if err := os.WriteFile(path, []byte(actual), 0o644); err != nil {
			t.Fatalf("writing golden file: %v", err)
		}
		return
	}
	want, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("reading golden file, run with -update to create it: %v", err)
	}
	if actual != string(want) {
		t.Errorf("receipt for %s does not match golden file %s", name, path)
	}
}

func TestRenderReceipt(t *testing.T) {
	order := Order{
		ID: "A-1042",
		Items: []LineItem{
			{Name: "Espresso", Quantity: 2, UnitPriceCents: 350},
			{Name: "Croissant", Quantity: 1, UnitPriceCents: 425},
		},
	}
	checkGolden(t, "receipt_two_items", RenderReceipt(order))
}
```

```swift
// Receipt.swift. the system under characterization, and a golden master
// comparison helper for use inside an XCTest target.

import Foundation

struct LineItem {
    let name: String
    let quantity: Int
    let unitPriceCents: Int
}

struct Order {
    let id: String
    let items: [LineItem]
}

func formatCents(_ cents: Int) -> String {
    let sign = cents < 0 ? "-" : ""
    let absolute = abs(cents)
    let dollars = absolute / 100
    let remainder = absolute % 100
    return String(format: "%@$%d.%02d", sign, dollars, remainder)
}

func renderReceipt(_ order: Order) -> String {
    var lines: [String] = ["Order \(order.id)", String(repeating: "-", count: 24)]
    var totalCents = 0
    for item in order.items {
        let lineTotal = item.quantity * item.unitPriceCents
        totalCents += lineTotal
        let paddedName = item.name.padding(toLength: 14, withPad: " ", startingAt: 0)
        lines.append("\(paddedName) x\(item.quantity)  \(formatCents(lineTotal))")
    }
    lines.append(String(repeating: "-", count: 24))
    let label = "Total"
    let padding = String(repeating: " ", count: 19 - label.count)
    lines.append("\(label)\(padding)\(formatCents(totalCents))")
    return lines.joined(separator: "\n") + "\n"
}

enum GoldenMasterError: Error {
    case referenceMissing(path: String)
    case mismatch(path: String, actual: String, reference: String)
}

/// Compares `actual` against a reference file at `testdata/<name>.golden`.
/// Pass `update: true` to write `actual` as the new reference, mirroring
/// the -update flag convention used by the Go and Rust examples above.
func checkGoldenMaster(name: String, actual: String, update: Bool = false) throws {
    let directory = URL(fileURLWithPath: "testdata")
    let path = directory.appendingPathComponent("\(name).golden")
    if update {
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        try actual.write(to: path, atomically: true, encoding: .utf8)
        return
    }
    guard let reference = try? String(contentsOf: path, encoding: .utf8) else {
        throw GoldenMasterError.referenceMissing(path: path.path)
    }
    if reference != actual {
        throw GoldenMasterError.mismatch(path: path.path, actual: actual, reference: reference)
    }
}
```
