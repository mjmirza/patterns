---
name: Four-Phase Test
slug: four-phase-test
family: 14-testing
category: Test Structure
aliases: [Arrange-Act-Assert, Given-When-Then, Setup-Exercise-Verify-Teardown]
first_described: "Meszaros 2007"
maturity: canonical
related: [test-fixture, test-double, parameterized-test, page-object, builder]
incompatible_with: []
verified: 2026-08-02
---

# Four-Phase Test

## 1. Name, aliases, and lineage

The canonical name is Four-Phase Test, from Gerard Meszaros, *xUnit Test
Patterns. Refactoring Test Code*, Addison-Wesley, 2007, ISBN
978-0-13-149505-0, chapter 4, "Four-Phase Test". Meszaros named and formalised
a shape that testing communities had already converged on independently under
different names, and his contribution was to give the four parts fixed names,
state the ordering as a rule, and catalog the ways real test suites violate
it. The book grew out of Meszaros's own xunitpatterns.com catalog, which
predates the book and served as its working draft.

The dominant alias in day-to-day conversation is **Arrange-Act-Assert**, often
written AAA. The phrase is attributed to Bill Wake, credited by name inside
Meszaros's own book as the source of the shorter three-word vocabulary that
practitioners actually say out loud (Meszaros 2007, chapter 4, "Four-Phase
Test", the naming-history note). Arrange-Act-Assert collapses Meszaros's
four phases into three by treating teardown as implicit framework cleanup
rather than an explicit named step, which is accurate for the common case
where teardown is nothing more than releasing what setup allocated.

A second alias, **Given-When-Then**, comes from a different lineage entirely.
It is the vocabulary of Behaviour-Driven Development, introduced by Dan North
in his original BDD writing and later formalised as the Gherkin syntax that
Cucumber and SpecFlow parse. Given-When-Then names the same three functional
phases as Arrange-Act-Assert, aimed at a business-readable scenario rather
than at code. Given corresponds to Arrange, When corresponds to Act, Then
corresponds to Assert. The phases are the same shape wearing different
vocabulary for a different audience, not two competing patterns.

A test that also names its cleanup step explicitly is sometimes described by
the fuller **Setup-Exercise-Verify-Teardown** vocabulary, which is Meszaros's
own naming for the four phases individually, namely setup, exercise, verify,
and teardown. This document uses setup, exercise, verify, teardown as the four
phase names throughout, and arrange, act, assert as the informal three-word
shorthand for the same first three phases when teardown is implicit.

## 2. Problem and context

A test method's job is to answer one question unambiguously, did the
behaviour under test do the right thing. A test that mixes preparation code,
the action being tested, checking code, and cleanup code together in no
particular order fails at that job even when it passes, because a reader
cannot tell which lines matter to the assertion and which lines are scaffolding
that happens to be nearby.

The failure shows up in three recognisable shapes in a real codebase. First,
a long test method where setup for the third scenario is interleaved with
assertions for the first, so a reader has to trace variable lifetimes across
forty lines to know what state existed when an assertion ran. Second, a test
where the assertion appears before the action it is meant to check, because
the author copied an earlier test and edited it out of order, so the
assertion silently checks pre-action state and always passes. Third, a test
suite where every test repeats the same fifteen lines of object construction
inline, so a change to the constructor's signature requires editing forty
files instead of one shared setup routine.

The context in which the four-phase shape earns its place is any test written
against the xUnit family of frameworks, meaning any framework structured
around a test method, a setup hook, and an assertion library. That family
includes JUnit, pytest, Jest, Google Test, XCTest, and Go's `testing`
package, among their many relatives. The pattern assumes a single test
exercises a single behaviour and produces a single pass or fail verdict,
which is the design point of that whole framework family. It also assumes
the reader of the test is a programmer maintaining the code, not solely a
business stakeholder reading a specification, which is the axis along which
Given-When-Then and BDD tooling diverge from plain xUnit style without
changing the underlying shape.

## 3. Forces

- **Readability versus terseness.** Favoured toward readability. Four named
  sections, even when a blank line is the only separator, cost vertical space
  that a single-line clever assertion would not. The pattern trades density
  for a reader being able to answer what does this test check in the time
  it takes to scan four paragraphs.
- **Independence versus reuse.** Sacrificed toward reuse when setup is
  extracted into a shared fixture. A fixture shared by many tests couples
  those tests to one construction path, so a change to the fixture can break
  tests that never mention it by name. The pattern does not resolve this
  tension, it only makes the coupling visible instead of hidden inside every
  test body.
- **Speed of writing versus speed of diagnosis.** Sacrificed toward
  diagnosis. Separating exercise from verify costs an extra line or two per
  test to write, and pays it back the first time a test fails and the person
  reading the failure needs to know, without stepping through a debugger,
  which line produced the wrong value.
- **One assertion versus several.** A live tension inside the verify phase
  itself. A single logical assertion per test gives the clearest failure
  message and the smallest diagnostic surface, but produces more test methods
  and more setup duplication for a class with many properties to check in one
  interaction. Meszaros treats verifying several properties of a single
  observed outcome as one logical assertion even when it is several assertion
  statements, and treats checking several independent outcomes in one method
  as multiple logical assertions that belong in separate tests.
- **Determinism versus realism.** Favoured toward determinism. Setup should
  build known, fixed input, exercise should call exactly the behaviour under
  test, and verify should compare against an expected value computed
  independently of the code under test, never against a value the code
  itself produced. A test whose expected value is derived by re-running part
  of the production algorithm is not exercising anything, because it will
  agree with itself even after the algorithm regresses.

## 4. Applicability and non-applicability

Reach for the four-phase shape when the following hold.

- The test targets the xUnit family of frameworks, where one method is one
  test case with one pass or fail outcome.
- The behaviour under test can be driven from a known starting state, through
  one action, to one observable outcome.
- More than one person will read or modify the test later, so the cost of an
  unclear test compounds.
- The test suite is growing past a size where copy-pasted setup across many
  tests has already started to cost real maintenance time.

Do NOT reach for it, or reach for a variant, in the following cases, and the
reason matters more than the rule.

- **A property-based test.** Frameworks such as Hypothesis, fast-check, or
  ScalaCheck generate hundreds of inputs per run and assert an invariant
  property rather than one concrete expected value. The four-phase shape
  still applies loosely at the level of generate input, run the function,
  check the invariant, but forcing a property test into a literal
  arrange-act-assert template with a single hard-coded expected value defeats
  the point of generative testing. Cross reference the property-based-testing
  entry.
- **A snapshot or golden-master test.** The verify phase compares the entire
  output against a stored artefact rather than checking discrete assertions,
  so the setup and exercise phases still apply but the verify phase collapses
  into a single diff call. Treating this as a violation of the pattern
  misreads what the pattern is protecting against.
- **An end-to-end or exploratory test that must observe an evolving system
  over time**, such as a long-running integration scenario with multiple
  interleaved actions and checks (login, then browse, then add to cart, then
  check the cart, then checkout). Collapsing this into one setup, one action,
  one assertion produces an artificial and brittle test. The honest answer is
  either several four-phase tests chained through shared state, or a
  different pattern such as a state machine walk, not a single stretched
  four-phase test.
- **A performance or load test.** The action runs repeatedly under load and
  the assertion is a statistical threshold over a distribution, not a
  single comparison. The four-phase vocabulary of setup and verify still maps
  loosely, but the pattern's assumption of one action and one deterministic
  comparison does not hold.
- **A test whose entire purpose is to observe an interaction, not a return
  value**, such as verifying a specific sequence of calls to a collaborator.
  Here verify happens partly during exercise, because a mock records calls as
  they occur and the assertion checks the recorded call log afterward. The
  phases are still present logically, but the code sometimes cannot be split
  into visually separate blocks, since the mock's expectations are often set
  during arrange and checked during verify while the calls themselves happen
  during act.
- **A single, trivial assertion where naming phases would only add noise**,
  for example a one-line property getter test. A rigid enforcement that
  every test must carry visible section comments or blank-line dividers, even
  when the whole method is three lines, produces the exact clutter the
  pattern exists to avoid. The shape is a discipline about ordering and
  separation of concerns, not a formatting mandate that must be visually
  performed in every method regardless of size.

## 5. Structure

Four participants, named by the role they play inside a single test method.

- **Setup (Arrange, Given).** Builds the fixture, the known starting state the
  test needs. Constructs the object or objects under test, prepares any
  collaborators, seeds any data. Setup answers what state does this test
  begin from and nothing else. It never calls the method under test and it
  never contains an assertion.
- **Exercise (Act, When).** Invokes exactly the behaviour under test, once.
  Captures whatever the behaviour returns, throws, or causes as a side
  effect, so the verify phase has something concrete to check. A test with
  more than one call to the behaviour under test in its exercise phase is
  usually testing more than one thing and should be split.
- **Verify (Assert, Then).** Compares the observed outcome from exercise
  against an expected value computed independently, and reports pass or fail
  through the framework's assertion mechanism. Verify never mutates the
  system under test, if it does, it has silently become a second exercise
  phase.
- **Teardown.** Releases whatever setup acquired that will not clean itself
  up, such as closed connections, deleted temporary files, reset global
  state, or restored mocked singletons. In managed languages and modern
  xUnit frameworks, teardown is very often implicit, handled by the
  framework's own fixture lifecycle (a `finally` block, a context manager, a
  `yield` fixture's post-yield code, a per-test object instantiation that
  garbage collects on its own) rather than written out by hand in every
  test.

The four phases execute in that fixed order inside a single test method,
setup, then exercise, then verify, then teardown. Meszaros calls a test that
violates the ordering, most commonly by inserting an assertion before the
exercise it is meant to check, an Assertion Roulette or a badly-ordered
test depending on the exact failure; see dimension 11 for the named failure
modes.

## 6. ASCII structure diagram

```
   +----------------------------------------------------+
   |                  test_method()                      |
   |------------------------------------------------------|
   |  SETUP    | build fixture, construct SUT,            |
   |           | seed input data, no assertions here      |
   |------------------------------------------------------|
   |  EXERCISE | call the ONE behaviour under test,        |
   |           | capture its result, exception, or effect |
   |------------------------------------------------------|
   |  VERIFY   | compare captured outcome against an       |
   |           | independently computed expected value    |
   |------------------------------------------------------|
   |  TEARDOWN | release resources setup acquired,         |
   |           | often implicit via framework lifecycle    |
   +------------------------------------------------------+

   Fixed order, top to bottom, inside one test method.
   Each phase depends only on the phase(s) above it.
```

## 7. Dynamics

The runtime flow for a single test run, showing where the test framework's
own lifecycle hooks intersect the four phases.

```
Framework          TestMethod             SUT              Assertion Lib
   |                    |                   |                    |
   |-- beforeEach() --->|                   |                    |
   |   (shared setup,   |                   |                    |
   |    if any)         |                   |                    |
   |                    |                   |                    |
   |-- run test ------->|                   |                    |
   |                    |-- SETUP           |                    |
   |                    |   build fixture   |                    |
   |                    |   new SUT() ----->|                    |
   |                    |                   |                    |
   |                    |-- EXERCISE        |                    |
   |                    |   sut.method() -->|                    |
   |                    |<-- result --------|                    |
   |                    |                   |                    |
   |                    |-- VERIFY          |                    |
   |                    |   assertEquals() ------------------->  |
   |                    |                   |     compares       |
   |                    |<---------------------- pass/fail ----- |
   |                    |                   |                    |
   |<-- test result ----|                   |                    |
   |                    |                   |                    |
   |-- afterEach() ---->|                   |                    |
   |   (TEARDOWN,       |                   |                    |
   |    often implicit) |                   |                    |
   |                    |                   |                    |
```

Two timing notes worth stating plainly. First, when setup is shared across
many tests through a framework hook such as `beforeEach` or a pytest
fixture, that hook runs before the body of every test method that requests
it, so per-test setup inside the method body handles only what differs for
that specific case, and the two setup layers compose rather than compete.
Second, when exercise throws an exception that the test expects, the
framework's own assertion mechanism for expected exceptions (a decorator, a
context manager, an `assertThrows` call) effectively fuses exercise and
verify into one statement, because catching the expected exception is itself
the verification.

## 8. Implementation variants

**Explicit sectioning with comments.** The literal form, `// arrange`,
`// act`, `// assert` comments or blank lines marking the three visible
blocks. Cheapest to adopt, easiest to lint for mechanically, and the
clearest for a newcomer to a codebase, at the cost of visual noise in a
suite that already follows the convention by habit.

**Given-When-Then via a BDD framework.** Cucumber, SpecFlow, and
behave-style tools parse a plain-language feature file into step
definitions that map onto the same three phases, aimed at making the
scenario readable by a non-programmer stakeholder. The underlying step
implementations still follow setup, exercise, verify internally, the BDD
layer changes who can read the scenario, not the phase structure itself.

**Fixture-extracted setup.** The setup phase is pulled out of the test
method into a shared fixture, a JUnit `@BeforeEach` method, a pytest
`@pytest.fixture`, an XCTest `setUp()` override, or a Jest `beforeEach`
callback. Multiple tests share one setup routine, each test method then
contains only exercise and verify. This is the single most common variant
in real codebases with more than a handful of tests, because duplicated
setup is the first maintenance cost a growing suite hits.

**Yield-style setup with implicit teardown.** pytest's fixture `yield`
form places setup code before the `yield` statement and teardown code
after it in the same function, so the two halves of one fixture read as
one unit even though they run at opposite ends of the test. The pytest
documentation states plainly that with these fixtures "we can run some
code and pass an object back to the requesting fixture/test... Any
teardown code for that fixture is placed after the yield" (pytest
documentation, "How to use fixtures", "Yield fixtures",
https://docs.pytest.org/en/stable/how-to/fixtures.html, verified
2026-08-02). Go's `t.Cleanup(func(){...})`, registered during setup,
achieves the same coupling of acquisition and release without the
generator syntax.

**Builder-based setup.** Setup constructs its fixture through a Test Data
Builder rather than a raw constructor call, so a test that needs one
field different from the default reads as one changed line rather than a
full re-listing of every constructor argument. This variant composes
directly with the Builder pattern, see the related-patterns entry for
Builder and the Object Mother alternative.

**Table-driven exercise and verify.** Go's idiomatic testing style defines
a slice of input-and-expected-output pairs, then loops over the table
calling `t.Run` once per entry, so setup happens once for the whole table
and exercise-plus-verify repeats per row. The Go Wiki states that "each
table entry is a complete test case with inputs and expected results... the
actual test simply iterates through all table entries and for each entry
performs the necessary tests. The test code is written once and amortized
over all table entries" (Go Wiki, "TableDrivenTests",
https://go.dev/wiki/TableDrivenTests, verified 2026-08-02). This is
structurally a Four-Phase Test with the exercise-verify pair
parameterised and repeated, corresponding to what xUnit-family frameworks
call a parameterised test, see the parameterized-test entry.

**Given-When-Then as method naming without a BDD framework.** A team
writes plain xUnit tests but names helper methods `given...`, `when...`,
`then...` to make the three phases visible in the method body without
adopting a Gherkin parser. This is a lightweight adoption of the
vocabulary with none of the tooling overhead, common in Kotlin and Swift
codebases influenced by BDD style without a full behave-driven pipeline.

## 9. Known production uses

**JUnit 5's lifecycle annotation model.** JUnit 5's `@BeforeEach` and
`@AfterEach` annotations exist specifically to let a test class factor
setup and teardown out of the four-phase test body into shared,
per-method hooks, and `@BeforeAll` and `@AfterAll` provide the
once-per-class equivalent. The framework's own user guide documents this
lifecycle model as the mechanism by which JUnit-based test classes
structure setup and teardown around test methods (JUnit 5 User Guide,
"Overview" and lifecycle-callback sections, https://docs.junit.org/current/user-guide/,
verified 2026-08-02, current version 6.1.2 as served at that URL). This is
the most widely deployed instance of the pattern's fixture-extracted setup
variant, given JUnit's position as the default JVM testing framework.

**pytest's fixture system.** pytest's `@pytest.fixture` decorator, and in
particular its `yield`-based teardown form, is the canonical Python
implementation of setup-and-teardown factored around a test's exercise and
verify phases, as documented in the official "How to use fixtures" guide
cited under dimension 8 (pytest documentation, https://docs.pytest.org/en/stable/how-to/fixtures.html,
verified 2026-08-02).

**Go's standard library `testing` package and its table-driven convention.**
The Go project's own `fmt` package tests, and the pattern's documentation on
the official Go Wiki, both instantiate the table-driven variant of the
Four-Phase Test as the idiomatic way to write a Go test with multiple input
cases against one behaviour (Go Wiki, "TableDrivenTests",
https://go.dev/wiki/TableDrivenTests, verified 2026-08-02).

**Kent Beck's original xUnit test framework design.** Kent Beck's
description of the test-first practice that produced the JUnit lineage
already assumes a test method sets up a fixture, exercises the code, and
checks an assertion, predating Meszaros's formal naming of the four phases.
Kent Beck, *Test-Driven Development. By Example*, Addison-Wesley, 2002,
ISBN 0-321-14653-0, part I, the money example chapters, which walk through
tests that follow exactly this setup, exercise, verify shape before the
book ever names it explicitly.

## 10. Consequences

Positive.

- A reader can answer what does this test check by scanning four short
  regions instead of tracing variable lifetimes through an undifferentiated
  block of code.
- A failing assertion's location tells the reader precisely which expected
  value did not match, because verify contains nothing but comparisons.
- Setup extracted into a shared fixture removes duplicated construction code
  across a growing suite, so a constructor signature change touches one
  fixture instead of every test file that builds that type.
- The discipline of exercising the behaviour exactly once surfaces tests
  that were secretly checking more than one thing, because splitting such a
  test along its exercise calls produces two clean four-phase tests instead
  of one tangled one.
- The ordering makes copy-paste errors visible on inspection, an assertion
  positioned before the exercise it is meant to check reads wrong to anyone
  who knows the convention, even without running the test.

Negative.

- Rigid application produces visual clutter on trivial tests, where three
  section comments cost more lines than the assertion they surround.
- Shared fixtures reintroduce the coupling the pattern's per-test
  independence goal was meant to avoid, a fixture used by forty tests can
  break all forty when it changes, even though only one of them cares about
  the change.
- The pattern says nothing about how to name the resulting test method or
  how to structure test class hierarchies, so teams that adopt the phase
  discipline without also adopting a naming and organisation convention
  still end up with a suite that is locally clear but globally hard to
  navigate.
- Table-driven and property-based variants stretch the one-exercise-one-
  assertion rule until it is more honoured in spirit than in code layout,
  which confuses a reader who expects the textbook four-block shape and
  finds a loop instead.

## 11. Failure modes and misuse

**Assertion Roulette.** Symptom. A test fails, and the failure message gives
no hint which of the eight assertions in the verify phase actually broke,
because none of them carries a descriptive message and several check
unrelated properties of unrelated exercise calls. Cause. Multiple exercise
calls and their assertions interleaved in one method instead of separated
into distinct tests. Meszaros names this failure directly as one of the
canonical test smells the four-phase discipline is meant to prevent. Fix.
Split the method along its exercise calls into one four-phase test per
behaviour, or add a descriptive message to each assertion if the checks
genuinely belong together as one logical assertion of one outcome.

**Eager Test, also called an overspecified test.** Symptom. A single test
method exercises several unrelated behaviours of the SUT and verifies all of
them, so the test is slow to write, hard to name honestly, and fails for
several unrelated reasons that all look the same in the test runner output.
Cause. Exercise phase calling more than one method under test. Fix. One
exercise call per test, split the rest into siblings.

**Assertion before exercise.** Symptom. A test passes even though the
behaviour under test is broken, discovered only when a mutation testing tool
or a manual code review notices the assertion checks a value that was never
touched by the call underneath it. Cause. A copy-pasted test where lines were
reordered incorrectly, or an assertion accidentally checking the fixture's
initial state rather than the post-exercise state. Fix. Enforce, by
convention or lint, that the exercise call's captured result is what every
assertion in verify references.

**Mystery Guest.** Symptom. A test fails intermittently or only in a shared
CI environment, and the failure cannot be reproduced by reading the test
file alone. Cause. Setup implicitly depends on external state not visible in
the test, for example a shared database row seeded by a different test, a
file on disk left by a previous run, or an environment variable set outside
the test. Fix. Move the dependency into the setup phase explicitly, or
replace it with a Test Double so the fixture is fully self-contained, see
the test-double entry.

**Conditional logic inside verify.** Symptom. A test contains an `if`
statement that decides which assertion to run, and a code review cannot tell
from reading the test which branch will actually execute for a given run.
Cause. An attempt to make one test method cover multiple scenarios instead
of writing separate tests or a parameterised table. Fix. Split into separate
tests, or convert to the table-driven variant from dimension 8, which
removes the conditional by making each row its own deterministic case.

**Expected value derived from the code under test.** Symptom. A regression
in the production algorithm ships without a single test failing, because the
expected value in verify was computed by calling a helper that shares logic
with the SUT, so a shared bug produces agreement rather than a mismatch.
Cause. Verify phase computes its expected value dynamically instead of using
a literal, independently sourced constant. Fix. Hard-code the expected value
or derive it from an independent oracle, never from a code path that shares
implementation with what is under test.

**Teardown that silently never runs.** Symptom. Test suite state leaks
between runs, a test that passes alone fails when run after a specific
other test. Cause. Teardown written as ordinary statements after the
assertion, which never execute if the assertion throws, rather than in a
`finally`, a context manager, or a framework's guaranteed-run teardown hook.
Fix. Move teardown into the framework's lifecycle mechanism (`afterEach`, a
`finally` block, a `yield` fixture's post-yield code, `t.Cleanup`) so it runs
regardless of whether verify passed.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Four-Phase Test (AAA / GWT) | Property-based testing | Snapshot / golden-master testing | Fluent assertion chains without phase separation | BDD scenario files (Gherkin) |
|---|---|---|---|---|---|
| Readability per test | High. Fixed structure, scannable | Medium. Reader must understand the invariant, not a concrete example | High for the diff, low for why the golden file has that shape | Medium. Depends on chain naming discipline | High for a non-programmer, adds an indirection layer for a programmer |
| Setup cost per test case | One fixture per test or per shared fixture | One generator, amortised over many cases | One recorded snapshot, regenerated on intentional change | Same as AAA, just formatted differently | A step-definition layer plus the scenario file |
| Failure diagnosis | Precise, one expected-vs-actual per assertion | Reports a minimal failing case via shrinking | A diff of the whole output, can be noisy for a large artefact | As precise as AAA if phases are still logically separated | Precise at the step level, harder to trace into the underlying code |
| Coverage of edge cases | Only the cases the author thought to write | Broad, generator explores the input space | None beyond the one recorded scenario | Same as AAA | Same as AAA |
| Maintenance under refactor | Fixture and assertions need updating by hand | Invariant usually survives a refactor untouched | Fragile, any output-format change breaks every snapshot | Same as AAA | Step definitions plus scenario text both need updating |
| Audience | Programmers | Programmers, requires statistical literacy | Programmers, moderate setup | Programmers | Programmers and non-programmer stakeholders |
| Best fit | Single deterministic behaviour, one interaction | An invariant that should hold over many inputs | Rendering, serialisation, generated output | Teams already using a fluent assertion library | Cross-functional teams needing a shared specification artefact |

Reading of the table. Four-Phase Test wins as the default for ordinary unit
and integration tests of deterministic behaviour. Property-based testing
wins where the property, not one example, is what actually matters.
Snapshot testing wins where the output is large and hand-written
assertions would be more tedious than useful. Fluent assertion chains are a
stylistic variant of Four-Phase Test rather than a genuine alternative, and
BDD scenario files are a presentation layer over the same phases aimed at a
different reader.

## 13. Related and incompatible patterns

- **Test Fixture.** The setup phase's product. A Test Fixture is the known
  state a test begins from, and the pattern of extracting that state into a
  reusable, named unit (a `beforeEach` method, a pytest fixture, a Test Data
  Builder result) is what most teams mean when they say their fixtures. The
  Four-Phase Test consumes a fixture, it does not define how to build one.
- **Test Double.** Composes inside setup and sometimes inside verify. When
  the SUT collaborates with something slow, non-deterministic, or hard to
  construct, setup substitutes a stub, mock, fake, or spy for the real
  collaborator so the test stays fast and deterministic. See the test-double
  entry for the distinctions between the four kinds.
- **Object Mother and Builder.** Two competing answers to how setup
  constructs its fixture cheaply. An Object Mother is a factory method
  returning a fully configured, named example object. A Builder returns a
  fluent chain letting the caller override only what differs from a
  sensible default. Both reduce setup duplication across many four-phase
  tests, Builder scales better as the number of optional fields grows.
- **Parameterized Test.** A direct generalisation of the table-driven
  variant from dimension 8, one setup, then the framework repeats exercise
  and verify once per data row, reporting each row as its own pass or fail.
  JUnit's `@ParameterizedTest`, pytest's `@pytest.mark.parametrize`, and
  Go's table-driven convention are all instances.
- **Page Object.** A common companion in UI end-to-end tests. The exercise
  phase of a four-phase test drives the system through a Page Object's
  methods rather than raw selectors, which keeps the exercise phase
  readable even when the underlying interaction is a multi-step browser
  workflow.
- **Given-When-Then / Behaviour-Driven Development.** Not a distinct
  pattern from Four-Phase Test but a presentation of the same three
  functional phases aimed at a business-readable specification. Composes
  cleanly, conflict arises only when a team layers a full Gherkin toolchain
  on top of tests that never need a non-programmer reader, adding
  indirection for no audience.
- **Property-based testing.** Partially incompatible in literal structure,
  fully compatible in spirit. A property test still has a setup phase
  (configure the generator), an exercise phase (run the function under
  test for each generated input), and a verify phase (check the invariant
  holds), but the one-exercise-one-assertion rule from dimension 5 does not
  apply, because the framework itself repeats exercise and verify many
  times per test run.

## 14. Refactoring path in and out

Introducing four-phase discipline into an existing tangled test.

1. Identify the single behaviour the test is meant to be checking. If the
   method's name and its assertions do not agree on what that is, that
   disagreement is the first thing to fix, independent of formatting.
2. Locate every line that constructs state the SUT will need, and move those
   lines to the top of the method in the order they must run. This becomes
   the setup phase. Do not yet extract it into a shared fixture.
3. Locate the single call to the method under test. If there is more than
   one such call, stop here and split the test into as many tests as there
   are calls, each repeating the shared setup, before continuing.
4. Move every assertion below the exercise call, in any order, as the verify
   phase. Delete any assertion that checks pre-exercise state, it belongs, if
   anywhere, as a sanity check inside setup, not as part of verify.
5. Identify any acquired resource that setup opened and that will not clean
   up automatically. Move its release into the framework's guaranteed
   teardown hook, never into a bare statement after the assertions.
6. Once several sibling tests share an identical setup phase, extract that
   shared code into the framework's fixture mechanism (`beforeEach`, a
   pytest fixture, a `setUp` override), leaving each test method with only
   its distinguishing exercise and verify.
7. If several of the resulting tests differ only in their input and expected
   output, and never in the shape of their setup, exercise, or verify code,
   collapse them into one parameterised or table-driven test per dimension 8.

Removing or loosening the pattern when it stops earning its place.

1. Confirm the test genuinely falls into one of the non-applicability cases
   from dimension 4, a property test, a snapshot test, a multi-step
   end-to-end scenario, or a trivial one-line check.
2. For a trivial test, simply drop the section comments or blank-line
   dividers, the phases still exist logically, they no longer need to be
   visually marked.
3. For a scenario that needs multiple interleaved actions and checks, split
   it explicitly into a chain of four-phase tests sharing state through a
   fixture, or rewrite it as a state-machine walk, rather than forcing one
   oversized method to keep the AAA label it no longer deserves.
4. For a test converted to property-based form, keep the setup phase (the
   generator configuration) and accept that exercise and verify now repeat
   per generated case rather than running once, documenting that departure
   in a short comment so a future reader does not fix it back into a
   literal single-example test.

## 15. Testing and verification

This dimension is unusual for this entry. The pattern being described is
itself a testing pattern, so how do you test code that uses it becomes how do
you check that a test suite actually follows the discipline it claims to.

Easier because of the pattern.

- A code reviewer can check phase discipline by eye in seconds, is there
  exactly one call to the method under test, do all assertions sit after
  it, is nothing acquired in setup left unreleased. This is a fast, cheap
  review heuristic that catches the Assertion Roulette and out-of-order
  assertion failure modes before they ship.
- A lint rule can mechanically flag a test method containing more than one
  call to a method matching the class under test's public API, which
  catches the Eager Test smell without a human reading every file.
- Mutation testing becomes a meaningful signal specifically because
  Four-Phase Test keeps verify narrow, a mutation that survives (a changed
  operator or constant that no test catches) points precisely at a missing
  or weak assertion in a specific, small verify block, rather than
  somewhere inside a sprawling method.

Harder because of the pattern.

- The discipline itself has no automatic enforcement in most languages, a
  team must adopt a convention (comments, a lint rule, or a code review
  checklist) or the shape erodes back into tangled tests over time, since
  nothing in the compiler or the test framework requires phase separation.
- Extracted shared fixtures, once adopted, need their own tests or at least
  their own scrutiny, because a bug in a fixture used by forty tests is a
  bug that forty green checkmarks will not reveal on their own, a fixture
  that silently constructs the wrong default value can make every dependent
  test pass for the wrong reason.

Techniques that apply.

- **Mutation testing** against the verify phase specifically. Tools such as
  Stryker (JavaScript and TypeScript), PIT (Java), or mutmut (Python)
  introduce small code changes and check whether the existing verify
  assertions catch them, a Four-Phase Test with a narrow, well-targeted
  verify phase produces a clean, interpretable mutation-testing report.
- **A code-review checklist item**, one exercise call, all assertions after
  it, teardown in a guaranteed-run hook. Cheap, catches the majority of
  failure modes in dimension 11 without any tooling.
- **Snapshot the fixture itself** for a complex Object Mother or Builder
  default, so a change to the default's shape is visible in a diff rather
  than silently altering every dependent test's starting state.

## 16. Observability signals

Because the Four-Phase Test pattern governs test code rather than production
code, observability here means what a CI dashboard and a test-run report
should surface to make a suite's health visible, not runtime telemetry from
a deployed system.

What to record.

- Per-test duration, so a test whose setup phase silently grew expensive (a
  fixture that now opens a real database connection instead of a fake one)
  is visible as a slow outlier rather than discovered only when the whole
  suite becomes sluggish.
- Assertion count per test method, tracked as a suite-wide metric over time.
  A rising average, especially concentrated in a few files, is a leading
  indicator of Assertion Roulette accumulating.
- Flaky-test rate, meaning tests that alternate between pass and fail across
  otherwise identical runs with no code change. A test that violates
  teardown discipline (dimension 11) or depends on a Mystery Guest is the
  most common source of this signal.
- Mutation score per file or module, where mutation testing is in use,
  broken down enough to point at specific verify phases whose assertions
  are too weak to catch an introduced defect.

A healthy suite on a dashboard. Test durations cluster tightly with a small
number of clearly-labelled slow integration tests, not a long unexplained
tail. The flaky-test rate sits at or near zero and does not creep upward
release over release. Assertion counts per test stay low and roughly even
across files, rather than concentrated in a handful of sprawling methods.

A failing suite. A subset of tests intermittently flip pass and fail on an
unchanged codebase, which localises to Mystery Guest or missing-teardown
failures once the specific tests are identified. Test duration grows
release over release with no corresponding growth in production code
complexity, which usually means fixtures have drifted from fast fakes
toward slow, real dependencies. A mutation-testing report shows surviving
mutants concentrated in a small number of files, which localises exactly
where the verify phase's assertions are weaker than the test method's name
implies.

## 17. Security and privacy implications

The pattern itself is close to silent on security, being a shape for test
code rather than production code, but three genuine implications follow
from how setup and verify phases are commonly written in practice.

**Fixtures holding real credentials or production-like personal data.**
A setup phase that seeds a fixture from a copy of production data, or that
hardcodes a real API key or database password for convenience, turns every
test file into a place a secret or a real person's data can leak,
particularly once that fixture is committed to source control and
distributed to every developer's machine and every CI runner. The
recommended discipline is to make setup produce synthetic or clearly
fabricated data by default, and to keep any genuinely sensitive
configuration out of the fixture entirely, injected instead through a
secrets manager scoped to the environment that actually needs it.

**Shared fixtures as a single point of contamination.** A shared setup
fixture used across many tests is also a single place where a
security-relevant default can be silently wrong, for example a fixture
that constructs a user object with an overly permissive role because that
was convenient for testing an unrelated feature. Because dozens of tests
inherit that default without re-examining it, a role or permission bug
introduced in one shared fixture can hide behind a large number of
otherwise-passing, otherwise-unrelated tests.

**Teardown as a data-retention control, not just cleanup.** When setup
creates a real record in a shared test database, an integration
environment, or a cloud sandbox account, the teardown phase is what
prevents that record from accumulating indefinitely. A test suite whose
teardown is unreliable, per the failure mode in dimension 11, does not
only leak state between test runs, over time it also leaks real records,
sometimes containing test-fabricated but realistic personal data, into an
environment that is not scoped or retained the way a genuine data-handling
policy would require. Treating teardown as guaranteed-to-run is therefore
also a data-hygiene control, not purely a correctness one.

## Code examples

Three languages, chosen for genuinely different idiomatic shapes. Java shows
the classical JUnit 5 form with an extracted fixture. Python shows pytest's
`yield`-fixture variant, where setup and teardown live in one function
around one `yield`. Go shows the table-driven variant, where setup happens
once and exercise-plus-verify repeats per table row through `t.Run`.

### Java

The shape below writes what JUnit 5's `@BeforeEach`, `@Test`, and `@AfterEach`
would produce, by hand, so it compiles with plain `javac` and needs no
external dependency. A real JUnit test class replaces the hand-rolled
`runTest` loop with the annotations from dimension 9 and lets the framework
call `setUp`, each test method, and `tearDown` for it.

```java
import java.util.HashMap;
import java.util.Map;
import java.util.function.Consumer;

class ShoppingCart {
    private final Map<String, Integer> items = new HashMap<>();

    void add(String name, int priceCents) {
        items.put(name, priceCents);
    }

    void remove(String name) {
        items.remove(name);
    }

    int total() {
        int sum = 0;
        for (int price : items.values()) sum += price;
        return sum;
    }

    boolean isEmpty() {
        return items.isEmpty();
    }
}

public class Main {

    private static ShoppingCart cart;

    // SETUP. what @BeforeEach would run before every test method
    static void setUp() {
        cart = new ShoppingCart();
        cart.add("apple", 100);
    }

    // TEARDOWN. what @AfterEach would run after every test method
    static void tearDown() {
        cart = null;
    }

    static void addingASecondItemIncreasesTotal() {
        // EXERCISE. the one behaviour under test
        cart.add("bread", 250);

        // VERIFY. expected value computed independently, not derived
        // from the cart's own internals
        assertEquals(350, cart.total());
    }

    static void removingTheOnlyItemLeavesTotalAtZero() {
        // EXERCISE
        cart.remove("apple");

        // VERIFY
        assertEquals(0, cart.total());
        assertTrue(cart.isEmpty());
    }

    static void assertEquals(int expected, int actual) {
        if (expected != actual) throw new AssertionError(expected + " != " + actual);
    }

    static void assertTrue(boolean condition) {
        if (!condition) throw new AssertionError("expected true");
    }

    static void runTest(String name, Runnable test) {
        setUp();
        test.run();
        tearDown();
        System.out.println("PASS " + name);
    }

    public static void main(String[] args) {
        runTest("addingASecondItemIncreasesTotal", Main::addingASecondItemIncreasesTotal);
        runTest("removingTheOnlyItemLeavesTotalAtZero", Main::removingTheOnlyItemLeavesTotalAtZero);
    }
}
```

### Python

```python
import pytest


class ShoppingCart:
    def __init__(self):
        self._items = {}

    def add(self, name: str, price_cents: int) -> None:
        self._items[name] = price_cents

    def remove(self, name: str) -> None:
        del self._items[name]

    def total(self) -> int:
        return sum(self._items.values())

    def is_empty(self) -> bool:
        return not self._items


@pytest.fixture
def cart():
    # SETUP happens before yield
    c = ShoppingCart()
    c.add("apple", 100)
    yield c
    # TEARDOWN happens after yield, guaranteed to run even if the
    # test raises, because pytest resumes the generator during cleanup
    print(f"cart torn down with {len(c._items)} items remaining")


def test_adding_a_second_item_increases_total(cart):
    # EXERCISE
    cart.add("bread", 250)

    # VERIFY
    assert cart.total() == 350


def test_removing_the_only_item_leaves_total_at_zero(cart):
    # EXERCISE
    cart.remove("apple")

    # VERIFY
    assert cart.total() == 0
    assert cart.is_empty()
```

### Go

```go
package cart

import "testing"

type ShoppingCart struct {
	items map[string]int
}

func NewShoppingCart() *ShoppingCart {
	return &ShoppingCart{items: map[string]int{"apple": 100}}
}

func (c *ShoppingCart) Add(name string, priceCents int) {
	c.items[name] = priceCents
}

func (c *ShoppingCart) Total() int {
	sum := 0
	for _, price := range c.items {
		sum += price
	}
	return sum
}

func TestShoppingCartTotals(t *testing.T) {
	// Table-driven variant. setup once as data, exercise and verify
	// repeat once per row via t.Run.
	cases := []struct {
		name      string
		addName   string
		addPrice  int
		wantTotal int
	}{
		{name: "adding bread", addName: "bread", addPrice: 250, wantTotal: 350},
		{name: "adding nothing extra", addName: "", addPrice: 0, wantTotal: 100},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			// SETUP. fresh cart per subtest, never shared mutable state
			c := NewShoppingCart()

			// EXERCISE
			if tc.addName != "" {
				c.Add(tc.addName, tc.addPrice)
			}

			// VERIFY
			if got := c.Total(); got != tc.wantTotal {
				t.Errorf("Total() = %d, want %d", got, tc.wantTotal)
			}
		})
	}
}
```

## 18. References

1. Gerard Meszaros. *xUnit Test Patterns. Refactoring Test Code*.
   Addison-Wesley, 2007. ISBN 978-0-13-149505-0. Chapter 4, "Four-Phase
   Test". Source of the pattern's name, the four phase names, the
   Arrange-Act-Assert attribution to Bill Wake, and the named test smells
   Assertion Roulette, Eager Test, and Mystery Guest referenced in
   dimension 11.
2. Kent Beck. *Test-Driven Development. By Example*. Addison-Wesley, 2002.
   ISBN 0-321-14653-0. Part I, the money example. Source of the pre-Meszaros
   setup-exercise-verify shape in dimension 9.
3. pytest. "How to use fixtures", section "Yield Fixtures".
   https://docs.pytest.org/en/stable/how-to/fixtures.html
   Verified 2026-08-02. Source of the quoted description of yield-based
   setup and teardown in dimensions 8 and the code example.
4. JUnit Team. *JUnit 5 User Guide*, current version 6.1.2 as served at the
   canonical URL. https://docs.junit.org/current/user-guide/
   Verified 2026-08-02. Source for the existence and role of the
   `@BeforeEach`, `@AfterEach`, `@BeforeAll`, and `@AfterAll` lifecycle
   annotations referenced in dimensions 8 and 9.
5. The Go Authors. "TableDrivenTests", Go Wiki.
   https://go.dev/wiki/TableDrivenTests
   Verified 2026-08-02. Source of the quoted description of table-driven
   testing and its idiomatic status in Go, used in dimensions 8 and 9.
6. Dan North. Original writing on Behaviour-Driven Development and the
   Given-When-Then vocabulary, as adopted by the Cucumber and Gherkin
   toolchains. Cited here for the lineage of the Given-When-Then alias in
   dimension 1. The Gherkin syntax itself is documented at
   https://cucumber.io/docs/gherkin/reference/, a live reference rather
   than a single dated source, consulted for the general shape of
   Given-When-Then step definitions described in dimension 8.
