---
name: Snapshot Test
slug: snapshot-test
family: 14-testing
category: Testing
aliases: [Snapshot Testing, Golden File Testing, Snapshot Assertion]
first_described: "Alpert, Carlesso 2016"
maturity: established
related: [golden-master, characterization-test, contract-test, property-based-test, fresh-fixture, test-data-builder]
incompatible_with: []
verified: 2026-08-02
---

# Snapshot Test

## 1. Name, aliases, and lineage

The name in day to day use across every ecosystem this entry surveyed is
Snapshot Test, sometimes written Snapshot Testing when the emphasis is on the
practice rather than a single test case. The name was fixed by a specific
engineering artifact, not by a paper. Ben Alpert and Cristian Carlesso, working
with the React team at Facebook, shipped the feature in Jest 14 on 27 July
2016, and the Jest project's own announcement gives both the authorship and
the motivation in the same paragraph. Engineers were spending more time
writing React tests than building the components under test, and many gave up
on testing altogether, so the team built a mechanism that renders a component,
serializes the render tree, stores that serialized text as a reference file,
and fails the test the moment a later render produces different text (Jest
blog, "Jest 14.0. Snapshot Testing, Coverage and Superfast Watch Mode,"
https://jestjs.io/blog/2016/07/27/jest-14, verified 2026-08-02). The same post
states that the idea was carried over from an existing internal practice for
testing native Facebook apps, and that the mechanism was deliberately split
into its own jest-snapshot package so other test runners could adopt the
same file format and comparison logic without adopting all of Jest.

Two aliases are common enough to name directly. Golden File Testing is the
older, more general term used outside the JavaScript world for the identical
mechanism applied to any text output, a compiler's generated assembly, a
linter's formatted output, a CLI's help text, compared byte for byte against a
file checked into the repository under a name like expected.golden. Snapshot
Assertion shows up inside individual test frameworks as the name of the single
assertion call, toMatchSnapshot in Jest, assert actual == snapshot in the
Python plugin syrupy, distinguishing the one line of test code from the
broader practice it belongs to.

This entry treats Snapshot Test as a close sibling of, but not identical to,
the Golden Master pattern documented elsewhere in this family. The two
mechanisms share the same core move, capture output once, compare against
that capture forever after, but they differ in emphasis and in the shape of
their tooling, and the difference is worth stating plainly rather than
treating the names as pure synonyms, because the tooling built for each
emphasis looks different in practice. Golden Master, as Michael Feathers
described it in *Working Effectively with Legacy Code* (Prentice Hall, 2004),
answers a whole-system question, does an inherited module with no test
coverage still behave the way it behaved yesterday. The workflow around it,
crystallized later in libraries like ApprovalTests, centers on a human
reviewing and approving a diff, one file at a time, often for a large output.
Snapshot Test, as it reached most working engineers through Jest, answers a
narrower and more frequent question, does this one component, this one
function, this one API response still serialize to the same structured text
it serialized to an hour ago. The workflow around it centers on structured,
machine-diffable text stored one small file per test case, reviewed the same
way a code diff is reviewed inside a pull request, and updated with a single
command line flag rather than an interactive approval step. Both mechanisms
belong to the same family tree. approval testing predates both names and
supplies the underlying idea of capture, compare, approve. Llewellyn Falco's
ApprovalTests project states its own kinship directly in its documentation,
describing an approval test as an assertion that takes "a snapshot of the
results, and confirming that they have not changed" (ApprovalTests project
site, https://approvaltests.com/, verified 2026-08-02), which is the exact
sentence a Jest user would use to describe toMatchSnapshot. The naming split
in practice is real even where the underlying mechanism is the same, and this
entry keeps the split so that the specific tooling, the specific failure
modes, and the specific advice that grew up around component and structured
data snapshots in the last decade get their own treatment, separate from the
whole-program characterization use case that Golden Master covers in depth.

## 2. Problem and context

A function, a component, or an API endpoint produces an output that is
correct today, and the author knows it is correct today because they looked
at it, ran it, or eyeballed a rendered page. The output has real structure. a
tree of nested elements, a JSON document with a dozen fields, a formatted
report with several sections, a generated SQL query, a CLI's stdout after a
subcommand runs. Writing a hand assertion that checks every field, every
attribute, every nested node, one expect call at a time, is possible but
expensive to write and, worse, expensive to keep honest as the shape of the
output changes over the life of the project. Every time a new field is added
to the response, every hand-written assertion that checks the response has to
be updated by a person who remembers to update it. In practice that person
frequently does not remember, and the test either stays silently blind to the
new field forever, or the author gives up on asserting the full shape and
falls back to checking one or two fields, which defeats the purpose of having
a structural test in the first place.

The problem sharpens further for anything with genuine visual or structural
complexity. a React component tree, a rendered email template, an SVG icon, a
formatted diff, a generated configuration file. For these the correct output
is not a short scalar a person can type into an assertion by hand at all. It
is pages of nested markup or a full image. Historically two responses to this
problem competed. either skip testing the output's shape entirely and settle
for testing that the function did not throw, which catches almost nothing,
or write the assertion by hand once, accept that it will be wrong the moment
the shape changes, and treat every future test failure as a coin flip between
a real regression and an intentional, unassessed change.

Snapshot testing answers this specific problem by removing the requirement
that a person write down the expected output by hand at all. The test asserts
that the current output matches a PREVIOUSLY CAPTURED output, and the first
capture is trusted the same way a person trusts their own eyes when they
review a diff. The context in which this genuinely helps is narrow and
specific, work with a shape that is large or nested enough that hand
assertions are painful to write and painful to maintain, work whose output is
deterministic given deterministic inputs, and work whose review cost, the
cost of a human actually reading the diff before approving it, stays low
enough that the technique keeps paying for itself rather than becoming a
rubber stamp. When any one of those three conditions is missing, snapshot
testing degrades quickly, and dimension 11 of this entry catalogs exactly how.

## 3. Forces

The central force is the trade between assertion effort and assertion
precision. A hand-written assertion is precise, it states exactly the field
and the value the author cares about, and it is expensive to write for a
large or deeply nested structure. A snapshot assertion is cheap to write,
one line, and it captures the whole structure at once, but the price of that
cheapness is that a snapshot cannot say which part of the structure the
author actually cares about. Every field in the captured output becomes an
assertion, whether the author intended it to be one or not, and a change
anywhere in that structure fails the test whether or not the change is one
the author would have cared to specify by hand. This is not a defect that a
smarter implementation removes. it is the shape of the trade the pattern
makes, and the honest way to reason about a specific use of snapshot testing
is to ask whether the author actually wants the whole shape to stay fixed as
the assertion, or whether they want something narrower and are only reaching
for a snapshot because writing the narrow thing by hand felt like too much
work.

A second force sits between review discipline and review cost. Kent C. Dodds,
a member of the Testing JavaScript community who wrote one of the most cited
essays on the pattern's failure mode, put the tension plainly. a snapshot
"more than a few dozen lines" invites a reviewer to stop reading it carefully
and simply accept the regeneration, because reading a hundred lines of
serialized markup and mentally diffing it against the previous hundred lines
is real cognitive work a reviewer is unlikely to do consistently under time
pressure (Kent C. Dodds, "Effective Snapshot Testing,"
https://kentcdodds.com/blog/effective-snapshot-testing, verified
2026-08-02). Every snapshot's usefulness depends on a human actually reading
the diff at the moment it changes. size and diff-legibility work directly
against that requirement. a serialized tree that changes indentation because
a wrapping div was added produces a diff that touches every line, obscuring
the one line that actually changed something a person would care about.

A third force is determinism against realism. The whole mechanism depends on
identical inputs producing byte-identical serialized output on every run, on
every machine, in every timezone. Real systems are full of sources of
nondeterminism that have nothing to do with correctness, current timestamps,
randomly generated identifiers, floating point formatting differences between
platforms, locale-dependent number and date formatting, insertion order in a
hash structure that a language does not guarantee to be stable. Every one of
these has to be normalized, mocked, or explicitly excluded from the snapshot
before the technique becomes usable, and every one of these normalization
steps is itself a place where a real bug can hide behind a mock that always
returns the same fake value.

A fourth force, more particular to structured or visual snapshots than to
scalar assertions, is coupling to representation versus coupling to
behavior. A DOM snapshot changes when a class name changes even if the
rendered pixels are identical, and a pixel snapshot changes when an anti
aliasing algorithm in a rendering library is upgraded even if no application
code changed at all. Storybook's own documentation names this tension when it
recommends visual or interaction tests over structural snapshot tests for
components. structural snapshots are easier to review in the sense that a
text diff is legible, but a visual regression tool that compares rendered
pixels catches classes of bugs, like a CSS regression that changes layout
without changing any DOM attribute, that a structural snapshot cannot see at
all (Storybook documentation, "Snapshot tests,"
https://storybook.js.org/docs/writing-tests/snapshot-testing, verified
2026-08-02).

## 4. Applicability and non-applicability

Reach for a snapshot test when the following hold together, not
individually.

- The output has real, non-trivial structure, deeply nested JSON, a rendered
  component tree, a generated file, a formatted CLI report, where a
  hand-written field-by-field assertion would be long, repetitive, and
  brittle to write in the first place.
- The output is fully deterministic once nondeterministic inputs, clocks,
  random identifiers, are controlled, because any residual nondeterminism
  turns every run into a coin flip between a real failure and a flaky one.
- The failure mode of interest is that this output changed at all, and the
  team genuinely wants to be told about every change to the captured shape,
  not only the changes a person predicted in advance.
- Snapshots stay small enough, ideally under a few dozen lines each, that a
  reviewer can actually read the diff in the time a code review normally
  takes, per the size concern raised in dimension 3.
- The team has committed to treating a snapshot file exactly like production
  code in review, meaning a pull request that regenerates a snapshot is read
  with the same attention as a pull request that changes an assertion by
  hand, never merged on the strength of a green check mark alone.
- The domain benefits from documentation-by-example, a transformation's
  before and after state, an error message's exact wording, a CSS-in-JS
  library's generated class names, where the captured artifact is itself
  useful reading for a future maintainer, not only a pass or fail signal.

Do not reach for a snapshot test in these situations, and treat each of
these as a genuine non-applicability, not a minor caveat.

- The behavior under test is a single scalar or a small, known set of
  fields. A function that returns a boolean, a status code, or three named
  fields is better served by a direct assertion on those fields. A snapshot
  here hides the actual intent of the test behind an opaque stored file and
  gives up nothing in writing effort that the direct assertion did not
  already save.
- The output legitimately varies between correct runs. Anything whose
  correct output is one of several valid orderings, one of several valid
  formattings, or genuinely random by design, defeats a byte-for-byte
  comparison entirely and produces permanent, unfixable flakiness rather than
  a signal worth reading.
- The team will not review snapshot diffs. If the actual behavior of the
  team is to run the update flag and commit without reading the diff, the
  test provides zero regression protection while still consuming CI time and
  disk space, and is strictly worse than no test, because it creates the
  appearance of coverage where none exists.
- The thing under test needs an explanation of why it is correct, not only
  a record of what it produced. A snapshot records an opaque blob of
  output. It carries no statement of intent. A reader six months later cannot
  tell whether a given field's value in the snapshot is load bearing or an
  accident of whatever the code happened to produce on the day someone ran
  the update command. Property-based tests or explicit example-based
  assertions communicate intent in a way a snapshot cannot.
- The output crosses a security or compliance boundary. A snapshot of an
  API response that happens to include a customer's personal data, an
  authentication token, or an internal-only header gets committed straight
  into source control and often straight into CI logs, and stays there in
  history even after later removal. Dimension 17 covers this at length.
- The unit under test is large enough that the entire application's
  rendered output would end up inside one snapshot. A page-level snapshot
  of a full HTML document changes on almost every commit for reasons wholly
  unrelated to the change being reviewed, whitespace shifts, a shared header
  component's unrelated update, a build tool's hash suffix, turning the
  snapshot into permanent background noise that trains reviewers to stop
  reading it, which is the specific failure Kent C. Dodds's essay names as
  the giant snapshot antipattern (Kent C. Dodds, "Effective Snapshot
  Testing," https://kentcdodds.com/blog/effective-snapshot-testing, verified
  2026-08-02).

## 5. Structure

Snapshot testing has fewer moving parts than a design pattern from an
object-oriented catalog, because most of the mechanism lives in a test
runner's library code rather than in application classes an architect
designs. The participants are still worth naming precisely, because getting
any one of them wrong is where the pattern's failure modes originate.

- Subject under test. The function, component, or system whose output is
  being captured. Nothing about this participant is special to the pattern.
  it is whatever the test would otherwise assert against directly.
- Serializer. Converts the subject's raw output, a React element tree, a
  Python object graph, a Rust struct, into a stable, comparable
  representation, almost always text. The default serializer that ships with
  a test runner handles the common cases, JSON-shaped objects, DOM nodes,
  simple structs. A custom serializer replaces or augments the default when
  the raw output contains something the default renders unstably, a
  timestamp, a random identifier, a circular reference, or a value whose
  default string conversion is not useful to a human reviewer.
- Snapshot store. The place the serialized text lives between runs. Two
  shapes dominate. an external file, one per test case or one shared file
  per test module, stored under a conventional directory like
  __snapshots__, and an inline literal, the serialized text written
  directly into the test source file next to the assertion that produced it.
  Jest supports both, toMatchSnapshot for the external file and
  toMatchInlineSnapshot for the inline literal (Jest documentation,
  "Snapshot Testing," https://jestjs.io/docs/snapshot-testing, verified
  2026-08-02). syrupy, the pytest plugin, defaults to an external Amber file
  format, one file per test module, and treats an assert-style call,
  assert actual == snapshot, as the entry point rather than a dedicated
  method call (syrupy project, https://github.com/syrupy-project/syrupy,
  verified 2026-08-02).
- Comparator. The logic that decides whether two serialized
  representations count as matching. For text this is almost always exact
  string equality after normalization. For image-based snapshots, the
  comparator is a pixel-difference algorithm with a configurable tolerance
  rather than exact equality, because rendering engines legitimately produce
  a handful of differing pixels between runs due to anti aliasing and font
  hinting even when nothing meaningful changed. Playwright's
  toHaveScreenshot exposes this tolerance directly through a
  maxDiffPixels option built on the pixelmatch library (Playwright
  documentation, "Visual comparisons,"
  https://playwright.dev/docs/test-snapshots, verified 2026-08-02).
- Update mechanism. The explicit, deliberate action that overwrites a
  stored snapshot with a freshly captured one. This is almost always a
  command line flag, --updateSnapshot or -u in Jest, --snapshot-update
  in syrupy, cargo insta review or cargo insta accept for the Rust crate
  insta, and it is the single most important participant to get right,
  because a runner that updates snapshots automatically, silently, or by
  default on every run has stopped being a test and become a tautology.
- Review surface. Not a runtime participant, but a structural
  requirement of the pattern working at all. the diff of a changed snapshot
  file must be legible inside whatever code review tool the team already
  uses, a pull request's file diff view being the overwhelmingly common
  case, because the snapshot store's whole reason for being a plain,
  version-controlled file rather than a database row is so that ordinary
  version control tooling can show a human exactly what changed.

## 6. ASCII structure diagram

```
                     +----------------------+
   test code   ----->|   Subject under test |
                     +----------------------+
                                |
                                v
                     +----------------------+
                     |      Serializer      |   normalizes non-determinism,
                     |  (default or custom) |   masks timestamps and ids
                     +----------------------+
                                |
                                v
                     serialized representation
                                |
                    +-----------+-----------+
                    |                       |
                    v                       v
        +----------------------+   +----------------------+
        |  Snapshot store       |   |     Comparator        |
        |  (file or inline      |<->|  exact text match, or  |
        |   literal, versioned) |   |  pixel diff threshold  |
        +----------------------+   +----------------------+
                    ^                       |
                    |                       v
        +----------------------+   +----------------------+
        |  Update mechanism      |   |    Test verdict        |
        |  (explicit CLI flag,   |   |  pass, fail, or new     |
        |   never automatic)     |   |  (missing) snapshot     |
        +----------------------+   +----------------------+
                    ^
                    |
        +----------------------+
        |    Review surface      |
        |  pull request diff of  |
        |  the snapshot store    |
        +----------------------+
```

## 7. Dynamics

The runtime behavior of a snapshot test has three distinct paths, and
conflating them is the source of most confusion about what the pattern
actually asserts.

```
FIRST RUN, no stored snapshot exists
  test executes subject under test
    -> serializer produces text T
    -> snapshot store has no file for this test name
    -> runner WRITES T to the store
    -> test reports PASS (or "1 snapshot written", depending on runner)

SUBSEQUENT RUN, unchanged behavior
  test executes subject under test
    -> serializer produces text T2
    -> snapshot store already has stored text T
    -> comparator checks T2 against T
    -> T2 equals T
    -> test reports PASS

SUBSEQUENT RUN, behavior changed
  test executes subject under test
    -> serializer produces text T3
    -> snapshot store already has stored text T
    -> comparator checks T3 against T
    -> T3 differs from T
    -> test reports FAIL, prints a diff of T vs T3
    -> human reads the diff
        -> if the change is a real regression, human fixes the code, reruns
        -> if the change is intentional, human runs the update flag,
           the store is overwritten with T3, and the new state is
           committed to version control as part of the same change

CI-SPECIFIC PATH, Jest and most runners that follow its lead
  when running under a recognized CI environment
    -> a missing snapshot is treated as a FAILURE, not silently written,
       because CI must never be the place a new baseline is first accepted
    -> the update flag must be passed explicitly even to write a first
       snapshot, so an author cannot forget to commit a snapshot locally
       and have CI paper over the gap
```

The critical property to notice in this flow is that the pattern has three
states, not two. pass, fail, and no baseline yet, and the third state is
handled differently depending on where the test runs. Locally, on a
developer's machine, a missing snapshot is usually written automatically on
first run, because the developer is right there to review it before
committing. On a shared CI server, the same missing snapshot is usually
treated as a failure, specifically so that a snapshot cannot be silently
created and immediately trusted by a machine that has no ability to judge
whether the captured output is correct. Jest's own documentation states this
directly, snapshots are not written automatically in CI unless the update
flag is explicitly passed (Jest documentation, "Snapshot Testing,"
https://jestjs.io/docs/snapshot-testing, verified 2026-08-02).

## 8. Implementation variants

- File-per-test external snapshots. The dominant shape. Jest's
  toMatchSnapshot() writes a .snap file under a __snapshots__ directory
  next to the test file, keyed by the test's name (Jest documentation,
  https://jestjs.io/docs/snapshot-testing, verified 2026-08-02). syrupy
  follows the same directory convention for Python but defaults to a
  human-readable Amber format rather than JSON, and supports swapping the
  serializer per assertion for JSON, PNG, or SVG output (syrupy project,
  https://github.com/syrupy-project/syrupy, verified 2026-08-02). The
  advantage of one file per test case is that a version control diff shows
  exactly which test's expectation changed, with no noise from unrelated
  test cases sharing a file.
- Inline literal snapshots. The serialized value is written directly
  into the test source as a string literal, right next to the assertion.
  Jest's toMatchInlineSnapshot() supports this, auto-formatting the
  literal with the project's code formatter when one is configured (Jest
  documentation, https://jestjs.io/docs/snapshot-testing, verified
  2026-08-02). This trades a smaller number of files for larger, noisier
  individual test files, and works best for genuinely small outputs, a
  single serialized object rather than a full component tree.
- Interactive review tooling. Rather than trusting a bare text diff,
  some ecosystems ship a companion CLI or editor extension that walks a
  developer through each changed snapshot one at a time, showing old and new
  side by side and asking for an explicit accept or reject decision per
  case. The Rust crate insta ships exactly this workflow through its
  cargo-insta companion tool and a VS Code extension, so a developer
  reviews pending snapshot changes interactively rather than eyeballing a
  raw diff in a terminal (insta documentation, https://insta.rs/docs/,
  verified 2026-08-02).
- Property-matcher snapshots. Rather than requiring every field in the
  captured structure to be fully deterministic before a snapshot can be
  taken at all, the assertion accepts a map of per-field matchers for the
  known-nondeterministic fields, an identifier that only needs to be any
  number, a timestamp that only needs to be any date, and stores those
  matcher placeholders inside the snapshot file in place of an actual value.
  Jest's toMatchSnapshot(propertyMatchers) form supports this directly
  (Jest documentation, https://jestjs.io/docs/snapshot-testing, verified
  2026-08-02).
- Structural or DOM snapshots for UI components. The serializer walks a
  rendered component's element tree, not the pixels a browser would paint,
  and produces a textual representation of tags, attributes, and children.
  Storybook's Portable Stories API supports composing a story for this kind
  of test inside Jest or Vitest, explicitly distinct from a pixel-based
  visual test of the same story (Storybook documentation,
  https://storybook.js.org/docs/writing-tests/snapshot-testing, verified
  2026-08-02).
- Pixel or image-based visual snapshots. The serializer is a screenshot
  renderer rather than a text serializer, and the comparator is a
  pixel-difference algorithm with a configurable tolerance rather than exact
  text equality. Playwright's toHaveScreenshot() captures a PNG or WebP on
  first run and compares subsequent captures against it, with the reference
  image's filename carrying the browser and operating system so that
  Chromium-on-macOS and WebKit-on-Linux never compare against the wrong
  baseline (Playwright documentation, https://playwright.dev/docs/test-snapshots,
  verified 2026-08-02).
- Golden file, non-UI variant. Outside any component-testing context,
  the same file-store-and-compare mechanism is applied directly to text a
  program writes to stdout or to disk, a compiler's generated intermediate
  representation, a linter's formatted output, a database migration tool's
  generated SQL. There is usually no dedicated library for this variant. a
  shell script or a small helper function reads a fixture file, runs the
  program, and diffs the two, following the same three-state dynamic as
  dimension 7 by hand.

## 9. Known production uses

- Jest, at Meta and across the wider JavaScript ecosystem. Jest is the
  project that gave the technique its dominant name and its dominant
  implementation, built by Ben Alpert and Cristian Carlesso with the React
  team and shipped as part of Jest 14 in July 2016, explicitly carried over
  from an existing internal practice for testing Facebook's native mobile
  apps (Jest blog, "Jest 14.0. Snapshot Testing, Coverage and Superfast
  Watch Mode," https://jestjs.io/blog/2016/07/27/jest-14, verified
  2026-08-02). Jest remains the default test runner scaffolded by Create
  React App and is bundled or supported by most React, Next.js, and Node
  project templates in current use.
- Storybook and Chromatic. Storybook, the component development
  environment now maintained by the company Chromatic, exposes both a
  structural DOM snapshot path through its Portable Stories API for use
  inside Jest or Vitest, and, through Chromatic's own hosted service, a
  pixel-based visual regression path that snapshots every registered story
  on every commit (Storybook documentation, "Snapshot tests,"
  https://storybook.js.org/docs/writing-tests/snapshot-testing, verified
  2026-08-02).
- Playwright, maintained by Microsoft. Playwright's own end-to-end test
  runner ships first-class visual snapshot assertions, toHaveScreenshot()
  and toMatchSnapshot(), with platform and browser aware baseline naming
  and a configurable pixel-difference tolerance built on the pixelmatch
  library, used across projects that need pixel-level UI regression coverage
  rather than only structural coverage (Playwright documentation, "Visual
  comparisons," https://playwright.dev/docs/test-snapshots, verified
  2026-08-02).
- insta, in the Rust ecosystem. insta is a dedicated snapshot testing
  crate for Rust, shipped with a companion cargo-insta command line tool
  and a VS Code extension for interactively reviewing pending snapshot
  changes, and supports redactions and custom serializers for the same
  nondeterminism problem Jest's property matchers solve in JavaScript (insta
  documentation, https://insta.rs/docs/, verified 2026-08-02).
- syrupy, in the Python ecosystem. syrupy is a pytest plugin, described
  in its own documentation as zero-dependency, that adds an assert actual
  == snapshot assertion style to pytest, storing snapshots in a
  __snapshots__ directory in a default Amber text format alongside
  optional JSON, PNG, and SVG extension classes (syrupy project,
  https://github.com/syrupy-project/syrupy, verified 2026-08-02).
- ApprovalTests, across many languages. Created by Llewellyn Falco,
  ApprovalTests reimplements the same capture, compare, approve mechanism
  for Java, C#, Python, Ruby, Node.js, PHP, and C++, under the name Approval
  Testing, and its own documentation states explicitly that the technique is
  also known as Golden Master Tests or Snapshot Testing on at least one of
  its language-specific project pages (ApprovalTests project site,
  https://approvaltests.com/, verified 2026-08-02), evidence that the naming
  boundary drawn in dimension 1 of this entry is a matter of community
  emphasis rather than a technical distinction the tool authors themselves
  insist on.

## 10. Consequences

Positive consequences.

- A test that would otherwise require dozens of hand-written field
  assertions collapses to a single line, and that line automatically covers
  every field in the output, including fields added after the test was
  written, which a hand-written assertion would silently ignore until
  someone remembered to update it.
- Regressions in output shape are caught even when nobody anticipated the
  specific way the shape could break, because the assertion is unchanged
  from before, not matches this one predicted value, and an unanticipated
  change is exactly the kind of change a predicted-value assertion is
  structurally unable to catch.
- The snapshot file itself becomes a form of documentation. a stored
  example of what a function, a component, or an error message actually
  produces, readable by a future maintainer without running the code, which
  Kent C. Dodds names directly as one of the technique's genuine strengths
  when the babel-plugin-tester project uses before-and-after formatted
  snapshots to communicate a transformation's effect (Kent C. Dodds,
  "Effective Snapshot Testing,"
  https://kentcdodds.com/blog/effective-snapshot-testing, verified
  2026-08-02).
- Updating an expectation after an intentional change is a single command
  line flag rather than a manual rewrite of a long hand assertion, which
  lowers the friction of keeping tests aligned with deliberate, reviewed
  changes to behavior.
- Because the mechanism is largely runner-provided rather than
  author-written, teams get review-friendly, version-control-native diffs
  of behavior changes essentially for free, without building any custom
  tooling.

Negative consequences.

- The assertion has no ability to express intent. A snapshot cannot say
  which field is load bearing and which one is incidental, so a reviewer
  reading a diff has no signal from the test itself about which of the
  changed lines actually matter, and has to reconstruct that judgment from
  context every single time.
- Snapshots grow stale as an artifact of habit rather than of correctness.
  the update flag makes it exactly as easy to accept a real regression as
  to accept an intentional change, and nothing in the mechanism itself
  distinguishes the two, so the pattern's entire value depends on a human
  discipline that the tool cannot enforce.
- Large snapshots actively erode the review discipline they depend on. once
  a snapshot passes a size threshold where a reviewer cannot hold the whole
  diff in their head, the practical behavior most teams settle into is
  approving the regeneration without close reading, at which point the test
  still runs, still consumes CI time, and provides close to zero actual
  regression protection.
- The technique is coupled to a specific representation, not to the
  underlying behavior a person actually cares about. a cosmetic change, a
  reordered object key, an added but functionally inert wrapper element, a
  version bump in a rendering library that shifts anti aliasing by a few
  pixels, produces a failing test that has nothing to do with a real defect,
  and a team that experiences this often enough starts to distrust every
  snapshot failure, which is the precursor to ignoring them altogether.
- Nondeterminism anywhere in the path from input to serialized output turns
  the test flaky, and flaky snapshot tests are unusually corrosive because
  the standard fix, rerun and see if it passes, trains the team to treat a
  failing snapshot as noise rather than as a signal worth investigating.

## 11. Failure modes and misuse

Symptom. A pull request touches one small, unrelated part of a
component, and CI reports dozens of failing snapshot tests across files the
author never opened.
Cause. A shared piece of markup, a layout wrapper, a design token, a
timestamp footer, is included inside every one of those component snapshots,
so any change to that shared piece cascades into every snapshot that
contains it, none of which is actually testing the shared piece on purpose.
Fix. Scope snapshots to the smallest unit that can meaningfully vary on
its own, extract shared chrome into its own dedicated test, and treat a
snapshot that fails across many unrelated files as a sign the snapshot
boundary is drawn in the wrong place, not as a sign that many components
regressed at once.

Symptom. A test suite that was reliably green starts failing
intermittently, with the same test passing on one CI run and failing on the
next with no code change in between.
Cause. The serialized output contains a value the test author never
controlled for, a timestamp from Date.now(), a randomly generated
identifier, a floating point number whose last digit differs by platform, or
the insertion order of a hash map that a language's runtime does not
guarantee to be stable across processes.
Fix. Mock every clock and random source the code under test touches
before capturing a snapshot, or apply an explicit property matcher or
redaction for exactly the fields that are legitimately nondeterministic,
following the pattern Jest's propertyMatchers argument and insta's
redaction filters both provide (Jest documentation,
https://jestjs.io/docs/snapshot-testing, verified 2026-08-02; insta
documentation, https://insta.rs/docs/, verified 2026-08-02).

Symptom. A single .snap file in the repository is several thousand
lines long, its diffs in pull requests are routinely approved within
seconds, and a genuine regression sat unnoticed inside it for weeks before a
user reported the actual bug.
Cause. The giant snapshot antipattern, one enormous captured structure
standing in for what should have been several small, focused assertions,
past the point where any reviewer can realistically read the whole diff on
every change, which Kent C. Dodds's essay identifies as the single largest
practical failure of the technique (Kent C. Dodds, "Effective Snapshot
Testing," https://kentcdodds.com/blog/effective-snapshot-testing, verified
2026-08-02).
Fix. Split the captured structure into several smaller, independently
meaningful snapshots, or replace the whole-structure capture with a small
number of hand-written assertions on the specific fields that actually
matter, accepting the extra writing cost in exchange for a diff a human will
actually read. eslint-plugin-jest's no-large-snapshots rule exists
specifically to enforce a size ceiling mechanically rather than rely on
review discipline alone (Jest documentation,
https://jestjs.io/docs/snapshot-testing, verified 2026-08-02).

Symptom. A code review approves a pull request that regenerates a
snapshot, and only later does someone notice the new snapshot silently
encodes an actual bug, a null field that should have been populated, an
off-by-one in a computed total, a broken layout that still renders without
throwing an error.
Cause. The update mechanism accepts whatever the code currently
produces as correct with zero judgment applied. If the code was already
wrong at the moment the snapshot was regenerated, the wrong output becomes
the new source of truth, and every future run will now happily confirm the
bug persists rather than flag it.
Fix. Treat every snapshot diff in a pull request exactly like a code
diff, requiring a reviewer to read the specific lines that changed and
reason about whether the new value is correct, never merging on a green CI
check alone when the check's meaning is only that it matches whatever the
author most recently accepted.

Symptom. A visual snapshot test that has been reliably passing for
months starts failing across the entire suite on every developer's machine
except the one that originally captured the baseline images, or after an
operating system or browser upgrade on the CI runner.
Cause. Pixel-based comparisons are sensitive to font rendering, anti
aliasing, and GPU driver differences that vary by operating system and
browser engine, and a baseline captured on one platform does not reliably
match a render produced on another. Playwright's own documentation names
this directly, stating that screenshots differ between browsers and
platforms due to different rendering and fonts, and addresses it by baking
the platform and browser name into the snapshot's filename so each
combination gets its own baseline (Playwright documentation,
https://playwright.dev/docs/test-snapshots, verified 2026-08-02).
Fix. Run visual snapshot capture and comparison inside a consistent,
containerized environment, ideally the exact same one used to capture the
original baseline, and never compare a baseline captured on a developer's
laptop against a render produced on a different operating system in CI.

## 12. Trade-off matrix

| Force | Snapshot Test | Golden Master, approval-style | Hand-written assertion | Property-based test |
|---|---|---|---|---|
| Authoring effort for large output | Very low, one line captures the whole shape | Low, but the human approval step adds friction per change | High, every field written by hand | Moderate, an invariant must be found and stated |
| Precision of what is actually being checked | Low, everything captured is asserted, whether intended or not | Low for the same reason, offset by an explicit human approval gate | High, only the stated fields are checked | High, but only for the invariant chosen, not the exact value |
| Cost of a legitimate output change | Very low, one command line flag regenerates the baseline | Moderate, requires an explicit interactive approval per file | High, every affected assertion is edited by hand | Low, the invariant usually still holds after a legitimate change |
| Communicates intent to a future reader | Low, an opaque captured blob with no stated reason | Moderate, an approval workflow at least records who signed off | High, the assertion states exactly what was expected and why | High, the property itself is a statement of intent |
| Tolerance for nondeterministic input | None without explicit masking or redaction | None without explicit masking or redaction | High, only the deterministic fields need be asserted | High by construction, since generated inputs are the whole point |
| Typical granularity | Unit or component level, one function or one render | Whole module or whole legacy system | Any granularity, chosen by the author | Function level, over a generated input space |
| Review cost as the artifact grows | Grows fast and nonlinearly once past a few dozen lines | Grows but the approval workflow is designed to scale to it | Grows linearly with the number of fields asserted | Stays roughly flat, the invariant does not grow with output size |

## 13. Related and incompatible patterns

Golden Master, documented elsewhere in this family, is the closest relative
and the one this entry has drawn a deliberate boundary against throughout.
The two share the identical capture-compare-approve mechanism, and the
difference this entry has argued for is one of granularity and tooling
emphasis, Snapshot Test skewing toward small, frequent, structured captures
reviewed inside ordinary pull request diffs, Golden Master skewing toward
larger, whole-system captures reviewed through a dedicated approval
workflow. A team is entirely free to use the same underlying library for
both use cases, and several of the tools named in dimension 9 explicitly
serve both.

Characterization Test, Michael Feathers's original name for using captured
output to pin down the behavior of legacy code with no prior test coverage,
is the specific use case snapshot testing serves best when applied to a
whole, poorly understood module rather than to a single well-understood
function, and the two entries should be read together when the motivating
context is an inherited codebase rather than new work.

Contract Test addresses a related but distinct problem, confirming that two
services agree on the shape of the messages they exchange across a network
boundary. A snapshot of a single service's response can serve as one
building block inside a contract test, but a contract test typically needs
both sides, provider and consumer, to agree independently, which a bare
snapshot comparison inside one codebase does not provide on its own.

Property-Based Test sits at the opposite end of the precision spectrum from
Snapshot Test. where a snapshot asserts an exact captured value, a
property-based test asserts an invariant that must hold across a generated
range of inputs, without ever pinning down one specific expected output.
The two compose well in practice. a property-based test can guard the
algebraic behavior of a function, while a small number of snapshot tests
guard the specific rendered or serialized shape that end users or
downstream systems actually consume.

Fresh Fixture and Test Data Builder both address how the input side of a
snapshot test is constructed, and both matter directly to the determinism
force named in dimension 3. a snapshot test built on a shared, mutable
fixture inherits whatever nondeterminism that fixture carries, while one
built on a fresh, explicitly constructed input is far more likely to stay
byte-for-byte stable across runs.

No pattern in this catalog is flatly incompatible with Snapshot Test in the
sense of being impossible to combine. the closest thing to a genuine
conflict is combining a snapshot test with a Shared Fixture that mutates
state across test cases, since a snapshot's entire value depends on the
input being reproducible, and a fixture shared and mutated across tests
routinely is not.

## 14. Refactoring path in and out

Introducing a snapshot test into code that has none, or that currently
relies on a long, brittle hand-written assertion, follows a small number of
concrete steps.

1. Identify a unit whose output has real structure and is currently either
   untested or tested with a long chain of field-by-field assertions that
   are painful to keep in sync with the code.
2. Confirm the unit's output is fully deterministic given deterministic
   input. run it twice with identical arguments and diff the two outputs by
   hand before writing any test at all. any difference found here has to be
   fixed, mocked, or masked before step 3, not after.
3. Write the single snapshot assertion, run the suite once to generate the
   baseline file, and read the generated baseline in full, end to end, the
   same way a reviewer would read a hand-written assertion. a snapshot
   baseline that is never read carefully at the moment it is created starts
   the test's life already untrustworthy.
4. Commit the baseline file alongside the test, and confirm in a code review
   that a second person also reads the baseline before approving, not only
   the test code that produced it.
5. Add masking, redaction, or property matchers for any field identified in
   step 2 as legitimately nondeterministic, and re-run to confirm the
   baseline is now stable across repeated executions.
6. Watch the size of the resulting snapshot over the following weeks. if it
   grows past a few dozen lines as the unit under test grows, treat that as
   a prompt to split the test rather than as an acceptable side effect of
   the unit's growth.

Removing a snapshot test that has stopped earning its place follows the
opposite direction.

1. Read the current, passing snapshot in full, and identify which specific
   fields inside it, if any, have actually caught a real regression in the
   test's history, by checking the file's version control log for
   meaningful diffs rather than mechanical whitespace-only regenerations.
2. For every field that has demonstrated value, write a direct,
   hand-written assertion that states the expectation explicitly, giving a
   future reader a stated reason rather than an opaque captured value.
3. For every field that has never meaningfully changed or never been read
   closely by a reviewer, drop it from the assertion entirely rather than
   converting it, since carrying dead assertion weight forward provides no
   benefit and adds to what a future refactor has to reason about.
4. Delete the snapshot file and the snapshot assertion once the replacement
   direct assertions are in place and green, and confirm the replacement
   suite still fails when the same historical regressions identified in
   step 1 are reintroduced by hand, as a sanity check that no coverage was
   lost in the conversion.

## 15. Testing and verification

Testing code that itself uses snapshot tests raises a question one level up
from the usual one, how does a team verify that its snapshot tests are
actually catching what they claim to catch, given that the mechanism, by
construction, always passes immediately after any change is accepted. The
practical answer is mutation-style verification applied by hand at
authoring time, described in dimension 14 step 3 above, reading the
generated baseline in full at the moment it is created, because that is the
one point in the test's life where a human is guaranteed to look at the
actual content rather than only its pass or fail status.

A second, mechanical layer of verification is size discipline enforced by
tooling rather than habit. eslint-plugin-jest's no-large-snapshots rule
fails a lint check when a stored snapshot file exceeds a configured line
count, converting the dimension 11 giant-snapshot failure mode from a
subjective judgment call into an objective, CI-enforced limit (Jest
documentation, https://jestjs.io/docs/snapshot-testing, verified
2026-08-02).

A third layer is running the same test suite twice, in immediate
succession, with no code changes between the two runs, specifically to
surface nondeterminism before it reaches a shared CI environment. A
snapshot test that fails on this repeated local run, without any code
change, has a nondeterminism problem that step 2 of the refactoring path in
dimension 14 was supposed to catch and did not, and the fix belongs in the
serializer or the input construction, not in a retry loop around the test
runner.

A fourth layer applies specifically to visual, pixel-based snapshots.
capturing baselines and running comparisons inside the same containerized
or CI-hosted environment every time, never comparing a baseline captured on
a developer's own machine against a render produced somewhere else, per the
platform-sensitivity failure mode described in dimension 11 and addressed
directly by Playwright's platform-and-browser-aware baseline naming
(Playwright documentation, https://playwright.dev/docs/test-snapshots,
verified 2026-08-02).

Finally, a snapshot test suite benefits from an explicit, periodic audit
distinct from day to day development, walking every stored snapshot file
and asking whether it has been meaningfully read by a reviewer at any point
in the last several months, or whether it has only ever been silently
regenerated. A snapshot store where every file's version control history
shows nothing but repeated, unreviewed regenerations is strong evidence the
team's snapshot tests have stopped functioning as tests at all, regardless
of what the CI dashboard reports.

## 16. Observability signals

A healthy snapshot test suite shows a small, stable rate of snapshot
regenerations over time, each one associated with a pull request whose
description explains why the captured output was expected to change, and
each one small enough in line count that the diff was plausibly read in
full. Tracking the size, in lines, of every stored snapshot file over time,
and flagging any file that crosses a configured threshold, per the
no-large-snapshots mechanism named in dimension 15, turns the giant
snapshot antipattern into a visible metric rather than a matter of
individual reviewer discipline.

A second useful signal is the ratio, per pull request, of lines changed in
application code to lines changed in snapshot files. a pull request that
touches ten lines of application logic and regenerates a thousand lines of
snapshot output is a strong candidate for the cascading-failure pattern
described in dimension 11, and surfacing this ratio in a pull request
template or a CI comment gives reviewers a concrete reason to slow down on
that specific change rather than approve it on the strength of a passing
check.

A third signal, specific to CI, is the rate at which the same snapshot
test flips between pass and fail across repeated runs of the identical
commit, with no intervening code change. Any nonzero rate here indicates
undetected nondeterminism somewhere in the path from input to serialized
output, and should route directly to the masking and determinism work
described in dimension 15, rather than being handled by an automatic retry
mechanism that would only paper over the underlying problem.

A fourth signal worth tracking specifically for visual, pixel-based
snapshots is the distribution of the reported pixel-difference count on
passing runs, not only on failing ones. a visual snapshot that consistently
passes at 40 or 50 pixels different, just under a configured
maxDiffPixels threshold, is quietly eroding its own usefulness, since a
real, small visual regression of a similar magnitude would slip through
undetected, and this drift is invisible unless the near-threshold pass rate
is tracked deliberately over time.

## 17. Security and privacy implications

Snapshot test files are, without exception, committed to version control
and are typically included in whatever build or CI logging the test runner
produces on failure. Any personal data, secret, authentication token, or
internal-only header that happens to be present in a captured API
response, a rendered form, or a serialized object graph becomes a
permanent part of that repository's history the moment the snapshot is
first committed, and, unlike a value stored in a database, removing it from
the current file does not remove it from the git history a person with
repository access can still retrieve.

This risk is sharper for snapshot testing than for a hand-written assertion
precisely because of the pattern's core advantage. a hand-written assertion
only asserts the fields a person deliberately chose to write down, so a
person choosing what to write naturally avoids asserting a secret they were
not looking to test. A snapshot captures everything, including any field
the author never consciously noticed was present in the output at all, a
debug header, an internal database identifier, a full stack trace embedded
in an error response used only in development mode. The very feature that
makes snapshot testing convenient, no need to enumerate every field by
hand, is what removes the moment at which a person would otherwise have
consciously decided whether a given field was safe to write into a file
that is about to be committed.

The practical response is to treat any test fixture whose output can
contain personal data, credentials, or internal-only fields with the same
data handling discipline applied to production logging, redacting or
masking those specific fields before the snapshot is ever taken, using
exactly the property matcher or redaction mechanisms named in dimension 8
for nondeterministic fields, since the mechanical fix is identical whether
the motivation is stability or data protection. A repository-wide scan for
common secret patterns, applied specifically to the __snapshots__
directory tree in addition to application source, catches the case where a
real credential was captured in a fixture during local development and
never noticed before the commit was pushed.

A second, narrower implication concerns pixel-based visual snapshots taken
against a staging or production-adjacent environment rather than a fully
synthetic one. a screenshot baseline captured against real account data
during manual test authoring commits an image containing that data
permanently into the repository, and image content is considerably harder
to scan automatically for sensitive information than structured text is,
which argues strongly for capturing visual baselines only against fully
synthetic, deliberately constructed fixture data, never against a live or
copied production account.

## 18. References

- Jest blog, "Jest 14.0. Snapshot Testing, Coverage and Superfast Watch
  Mode," https://jestjs.io/blog/2016/07/27/jest-14, verified 2026-08-02.
- Jest documentation, "Snapshot Testing," https://jestjs.io/docs/snapshot-testing,
  verified 2026-08-02.
- Kent C. Dodds, "Effective Snapshot Testing,"
  https://kentcdodds.com/blog/effective-snapshot-testing, verified
  2026-08-02.
- insta project documentation, https://insta.rs/docs/, verified 2026-08-02.
- Storybook documentation, "Snapshot tests,"
  https://storybook.js.org/docs/writing-tests/snapshot-testing, verified
  2026-08-02.
- Playwright documentation, "Visual comparisons,"
  https://playwright.dev/docs/test-snapshots, verified 2026-08-02.
- ApprovalTests project site, https://approvaltests.com/, verified
  2026-08-02.
- syrupy project, https://github.com/syrupy-project/syrupy, verified
  2026-08-02.
- Michael Feathers, Working Effectively with Legacy Code, Prentice Hall,
  2004, ISBN 0-13-117705-2, the source of the Characterization Test naming
  and the whole-system framing this entry contrasts Snapshot Test against
  in dimension 1 and dimension 13.

## Code examples

The three samples below implement the same minimal snapshot testing
mechanism directly, first run writes a baseline, second run against
unchanged input passes, third run against changed input fails with a
readable diff, rather than depending on Jest, syrupy, or insta as external
packages. This keeps every sample self-contained and independently
compilable, while showing the exact mechanism dimension 7 describes rather
than a black box import. Each sample was compiled or run with the toolchain
noted beside it.

TypeScript, type-checked with tsc --strict against @types/node.

```typescript
import { existsSync, readFileSync, writeFileSync, mkdirSync } from "fs";
import { dirname, join } from "path";

interface SnapshotResult {
  status: "written" | "passed" | "failed";
  diff?: string;
}

function serialize(value: unknown): string {
  return JSON.stringify(value, null, 2) + "\n";
}

export function matchSnapshot(
  name: string,
  actual: unknown,
  dir: string,
  update = process.env.UPDATE_SNAPSHOTS === "1"
): SnapshotResult {
  const file = join(dir, "__snapshots__", `${name}.snap`);
  const serialized = serialize(actual);

  if (!existsSync(file) || update) {
    mkdirSync(dirname(file), { recursive: true });
    writeFileSync(file, serialized);
    return { status: "written" };
  }

  const stored = readFileSync(file, "utf8");
  if (stored === serialized) {
    return { status: "passed" };
  }
  return {
    status: "failed",
    diff: `expected (stored):\n${stored}\nreceived (actual):\n${serialized}`,
  };
}

function run(): void {
  const dir = join(__dirname, "fixtures");
  const invoice = { id: "INV-42", total: 199.5, currency: "USD" };

  const first = matchSnapshot("invoice", invoice, dir);
  console.log("first run:", first.status);

  const second = matchSnapshot("invoice", invoice, dir);
  console.log("second run (unchanged):", second.status);

  const mutated = { ...invoice, total: 250.0 };
  const third = matchSnapshot("invoice", mutated, dir);
  console.log("third run (regression):", third.status);
  if (third.status === "failed") {
    console.log(third.diff);
  }
}

run();
```

Python 3.10 or newer, checked with python3 -m py_compile and run directly.

```python
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SnapshotResult:
    status: str
    diff: str | None = None


def serialize(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def match_snapshot(
    name: str,
    actual: Any,
    directory: Path,
    update: bool = os.environ.get("UPDATE_SNAPSHOTS") == "1",
) -> SnapshotResult:
    snap_dir = directory / "__snapshots__"
    snap_dir.mkdir(parents=True, exist_ok=True)
    path = snap_dir / f"{name}.snap"
    serialized = serialize(actual)

    if not path.exists() or update:
        path.write_text(serialized)
        return SnapshotResult(status="written")

    stored = path.read_text()
    if stored == serialized:
        return SnapshotResult(status="passed")
    diff = f"expected (stored):\n{stored}\nreceived (actual):\n{serialized}"
    return SnapshotResult(status="failed", diff=diff)


def run() -> None:
    directory = Path(__file__).parent / "fixtures"
    invoice = {"id": "INV-42", "total": 199.5, "currency": "USD"}

    first = match_snapshot("invoice", invoice, directory)
    print("first run:", first.status)

    second = match_snapshot("invoice", invoice, directory)
    print("second run (unchanged):", second.status)

    mutated = dict(invoice, total=250.0)
    third = match_snapshot("invoice", mutated, directory)
    print("third run (regression):", third.status)
    if third.status == "failed":
        print(third.diff)


if __name__ == "__main__":
    run()
```

Rust, compiled with rustc --edition 2021 and run as a standalone binary.

```rust
use std::env;
use std::fs;
use std::path::{Path, PathBuf};

enum Status {
    Written,
    Passed,
    Failed(String),
}

fn serialize(fields: &[(&str, String)]) -> String {
    let mut out = String::from("{\n");
    for (key, value) in fields {
        out.push_str(&format!("  {}: {}\n", key, value));
    }
    out.push_str("}\n");
    out
}

fn match_snapshot(name: &str, actual: &str, dir: &Path) -> Status {
    let snap_dir = dir.join("__snapshots__");
    fs::create_dir_all(&snap_dir).expect("create snapshot dir");
    let file: PathBuf = snap_dir.join(format!("{}.snap", name));
    let update = env::var("UPDATE_SNAPSHOTS").as_deref() == Ok("1");

    if !file.exists() || update {
        fs::write(&file, actual).expect("write snapshot");
        return Status::Written;
    }

    let stored = fs::read_to_string(&file).expect("read snapshot");
    if stored == actual {
        Status::Passed
    } else {
        Status::Failed(format!(
            "expected (stored):\n{}\nreceived (actual):\n{}",
            stored, actual
        ))
    }
}

fn main() {
    let dir = Path::new("fixtures");
    let invoice = serialize(&[
        ("id", "\"INV-42\"".to_string()),
        ("total", "199.5".to_string()),
        ("currency", "\"USD\"".to_string()),
    ]);

    match match_snapshot("invoice", &invoice, dir) {
        Status::Written => println!("first run: written"),
        Status::Passed => println!("first run: passed"),
        Status::Failed(diff) => println!("first run: failed\n{}", diff),
    }

    match match_snapshot("invoice", &invoice, dir) {
        Status::Written => println!("second run (unchanged): written"),
        Status::Passed => println!("second run (unchanged): passed"),
        Status::Failed(diff) => println!("second run (unchanged): failed\n{}", diff),
    }

    let mutated = serialize(&[
        ("id", "\"INV-42\"".to_string()),
        ("total", "250.0".to_string()),
        ("currency", "\"USD\"".to_string()),
    ]);

    match match_snapshot("invoice", &mutated, dir) {
        Status::Written => println!("third run (regression): written"),
        Status::Passed => println!("third run (regression): passed"),
        Status::Failed(diff) => println!("third run (regression): failed\n{}", diff),
    }
}
```

Each sample, run in order, prints first run written, second run unchanged
passed, and third run regression failed followed by a readable diff,
matching the three-path dynamic described in dimension 7 exactly. Java, Go,
C#, Kotlin, and Swift were not included as full samples here because the
pattern's interesting behavior lives entirely in the generic
capture-compare-update mechanism shown above, which is identical in shape
across every general purpose language, and a fourth or fifth translation of
the same forty lines would not surface anything the three languages above
do not already show.
