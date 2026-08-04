---
name: Arrange-Act-Assert
slug: arrange-act-assert
family: 14-testing
category: Testing
aliases: [AAA, 3A]
first_described: "Wake 2001"
maturity: canonical
related: [four-phase-test, given-when-then, mock, stub, fake, spy, dummy, test-driven-development]
incompatible_with: []
verified: 2026-08-02
---

# Arrange-Act-Assert

## 1. Name, aliases, and lineage

The canonical name is Arrange-Act-Assert, almost always shortened to AAA or 3A
in conversation and in code review comments. Bill Wake observed the pattern in
the test code he was reading and reviewing, named it, and published it on his
own site in 2001. Wake states this plainly in his own retrospective on the
pattern. "I observed and named the pattern in 2001. Arrange-Act-Assert has
been the full name the whole time, but it has been variously abbreviated as
AAA or 3A" (Bill Wake, "3A - Arrange, Act, Assert," xp123.com,
https://xp123.com/articles/3a-arrange-act-assert/, verified 2026-08-02). Wake
did not invent the practice of separating setup from execution from checking.
He named a shape that experienced test writers were already converging on
independently, and the name is what made the shape teachable and searchable.

Wake's own account also credits a second, later citation that most developers
encounter first. Kent Beck's *Test-Driven Development. By Example*,
Addison-Wesley, 2003, references the same three-part shape on page 97, and
Wake notes that Beck's book came after his own 2001 observation rather than
before it (per the same xp123.com retrospective cited above, verified
2026-08-02). Because Beck's book reached a far larger audience than Wake's
blog post, AAA is sometimes misattributed to Beck. The correct lineage, per
Wake's own published account, is that Wake named it first and Beck's book
popularized it.

The pattern has two close relatives that use different words for the same
three cuts. Gerard Meszaros catalogs the same structure as the Four-Phase Test
in his book *xUnit Test Patterns. Refactoring Test Code*, Addison-Wesley,
2007, in the pattern he names Four-Phase Test, splitting a test into Fixture
Setup, Exercise SUT (system under test), Result Verification, and Fixture
Teardown. Martin Fowler's summary of the relationship states it directly. "the
approach breaks scenarios into three sections. The given part describes the
state of the world before you begin the behavior you are specifying... Bill
Wake came up with the formulation as Arrange, Act, Assert" and maps the two
vocabularies phase for phase, Setup to Given, Exercise to When, Verify to Then
(Martin Fowler, "GivenWhenThen," martinfowler.com,
https://martinfowler.com/bliki/GivenWhenThen.html, verified 2026-08-02).
Given-When-Then itself was developed by Daniel Terhorst-North and Chris Matts
as part of Behavior-Driven Development, with North crediting Ivan Moore for
real inspiration, per the same Fowler page. So there are, in practice,
three names in circulation for one structural idea, plus a fourth phase
(teardown) that Meszaros keeps explicit and that Wake's three-word name folds
into the surrounding test-runner lifecycle rather than naming directly. This
entry treats Arrange-Act-Assert as the primary name because it is the name
most widely used inside code comments and code review vocabulary in
non-BDD-tooling codebases, and treats Four-Phase Test and Given-When-Then as
sibling names for the same underlying idea, each attached to a different
tooling community.

## 2. Problem and context

A test that has no imposed shape tends to accrete in whatever order the writer
thought of things. Setup code, the call that exercises the behavior, and the
checks that confirm the result end up interleaved. A reader arriving at the
test for the first time, usually because it recently failed and they need to
understand why, has to read the whole body line by line to reconstruct three
separate questions. What state did this test start from. What did it actually
do. What was it trying to prove. When those three questions are answered by
lines scattered through the method in whatever order occurred to the original
author, the reader pays a real cost on every single failure, which is exactly
the moment when the reader can least afford confusion.

The problem gets worse as a codebase grows, because tests are read far more
often than they are written. A production method might be read a handful of
times between changes. A test method is read every time it fails, every time
someone tries to understand the behavior it documents, and every time someone
extends the surrounding suite by copying the nearest existing test as a
starting point. Meszaros makes exactly this point in framing the Four-Phase
Test pattern. tests read like specifications only when their structure is
predictable enough that a reader can find the specification inside them
without re-deriving it each time.

The context in which Arrange-Act-Assert becomes the right answer has a
specific shape. There is a single unit of behavior under test, one system
under test with a beginning state, one triggering action, and one or a small
cluster of closely related outcomes to check. The pattern presumes the test is
short enough that three labeled sections fit on one screen. It presumes the
test author is willing to accept a small amount of setup duplication across
tests in exchange for each individual test being self-contained and readable
without cross-referencing a shared fixture file. And it presumes the
underlying test runner does not force a rigid setup and teardown lifecycle
onto every test uniformly, which is why Microsoft's own .NET testing guidance
recommends "helper methods instead of Setup and Teardown," on the grounds that
a shared `Setup` attribute run before every test in a class "often results in
bloated and hard to read tests" because each test generally needs different
preconditions (Microsoft, "Best practices for writing unit tests," Microsoft
Learn, https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-best-practices,
verified 2026-08-02). Outside that context, in particular for tests that
legitimately perform several unrelated actions against a long-lived fixture,
or for tests whose entire point is a sequence of interleaved actions and
checks, forcing a rigid three-line shape produces its own confusion, covered
in dimension 4.

## 3. Forces

This dimension is largely engineering judgement about which pressure a team is
optimizing for, informed by the sourced material above rather than itself an
independently sourced claim line by line.

- **Readability at failure time.** Strongly favored. A reader who opens a
  failing test wants the fastest possible path to "what was expected versus
  what happened," and a labeled Assert section is exactly that path.
- **Consistency across a suite.** Favored. Once every test in a codebase
  follows the same three-part shape, a reviewer can skim any test written by
  anyone and immediately locate the phase relevant to whatever they are
  checking, without first learning that particular author's personal style.
- **Test length.** Mildly sacrificed. Explicit blank lines or comments between
  phases add visible whitespace and sometimes a comment line per phase, a real
  but small cost against a test with no visible structure at all.
- **Setup reuse.** Sacrificed at the margin. A shared `Setup` fixture reused
  across many tests can be shorter in aggregate than repeating the same three
  or four arrangement lines in every test, but the Microsoft guidance cited
  above and the general test-isolation literature treat that reuse as a false
  economy once the shared fixture accumulates preconditions that most
  individual tests do not need.
- **Determinism and isolation.** Favored indirectly. The discipline of writing
  a complete Arrange section forces the author to notice every dependency the
  Act step actually needs, which surfaces hidden shared or global state before
  it becomes a source of flaky failures. This is a second-order benefit of the
  pattern's shape rather than a direct claim from the sources.
- **Assertion focus.** Favored. Keeping Act to one action, argued for
  explicitly in the "Avoid multiple Act tasks" section of the Microsoft
  guidance cited above, on the grounds that a test with several Act calls
  makes it hard to tell which action produced a given failure and that most
  frameworks stop running the remaining assertions once one fails, hiding
  information about the other actions.
- **Onboarding cost.** Favored for the team, sacrificed briefly for a new
  contributor. The shape has to be learned once, after which it applies to
  every test in every file, which is a smaller total cost than learning each
  author's ad hoc ordering per file.
- **BDD tooling fit.** Neutral to favored, situationally. A team already
  running Cucumber or a Given-When-Then style spec framework gains nothing
  from also writing Arrange, Act, Assert comments, because the tooling already
  imposes the equivalent three-part shape through its own keywords, covered in
  dimension 8.

No pattern here is free. The price paid for readability and consistency is a
small amount of extra vertical space per test and a mild loss of the
compression that a well-factored shared fixture can offer.

## 4. Applicability and non-applicability

Reach for Arrange-Act-Assert when the following hold.

- The test exercises one unit of behavior with one clear triggering action and
  a small, closely related set of outcomes to check.
- The test is read by people other than its author, which is nearly every test
  in a team codebase, and readability at failure time matters more than
  minimizing line count.
- The codebase already has, or is trying to establish, a consistent test
  shape, so that any reviewer can follow any test the same way, regardless of
  who wrote it.
- The test author wants a forcing function that surfaces hidden dependencies,
  because writing a complete and honest Arrange section makes implicit
  preconditions visible before they cause flaky tests later.
- Unit tests and most integration tests, where the system under test is a
  single component or a small, bounded collaboration, and the setup can be
  built directly in the test body or a small local helper.

Non-applicability. Do NOT force Arrange-Act-Assert in the following cases, and
the reason for each is what makes the exception genuine rather than laziness.

- **The scenario is inherently a sequence of interleaved actions and checks.**
  A state-machine test that drives a system through several transitions,
  checking an invariant after each one, is honestly shaped as
  act-assert-act-assert-act-assert. Wedging every action into one giant Arrange
  block followed by one giant Act block followed by one giant Assert block
  destroys the very thing the pattern exists to protect, a test a reader can
  follow without holding the whole thing in their head at once. The right
  answer here is usually several smaller AAA tests, one per transition, but
  when that is not possible the honest shape is a labeled sequence of
  act-assert pairs, not a distorted single triad.
- **A property-based test that runs the same action across many generated
  inputs.** The Act and Assert here are the invariant-checking function
  itself, run by the property framework hundreds of times per execution. There
  is still an arrange step, the generator configuration, but forcing the
  per-example logic into visible AAA comments inside a shrinking loop adds
  nothing.
- **The test is a Given-When-Then scenario running under Cucumber, Kotest's
  BehaviorSpec, or an equivalent BDD framework.** The framework's own keywords
  already impose and name the same three phases, and adding AAA comments on
  top is pure noise, see dimension 8.
- **A snapshot or golden-file test.** The entire test is often one line, run
  the system and compare the output to a stored artifact. There is no useful
  separate Assert phase to label, because the framework does the comparison.
- **Performance and load tests.** These typically run the action repeatedly
  under varying conditions and assert on statistical properties of the run as
  a whole, not on the outcome of a single triggering action, so the one-Act
  discipline described in dimension 3 does not transfer.
- **A test whose entire subject is interaction ordering itself.** When the
  behavior under test is the sequence in which a collaborator's methods are
  called, not a single resulting state, the useful structure is closer to
  "arrange the collaborator, then interleave calls with in-line verification
  of the call order," which some frameworks express as a single continuous
  Act-and-Assert block rather than a clean split.
- **Exploratory or characterization tests written to understand legacy
  behavior before refactoring.** These are deliberately messy, run-and-observe
  scripts, not documentation-grade specifications, and imposing AAA structure
  on throwaway exploration is wasted effort that should instead go into the
  clean test written once the behavior is understood.

## 5. Structure

Arrange-Act-Assert is not a structure of collaborating classes the way a GoF
pattern is. it is a structure imposed on the body of a single test method or
test function. The participants are phases inside that one body, not separate
types.

- **Arrange.** Builds the starting state the test needs. constructs the system
  under test, configures its collaborators, seeds any input data. Everything
  the Act phase will depend on is established here and nowhere else, so that
  the Act line reads as a pure trigger against a state the reader already
  understands.
- **Act.** Performs exactly one triggering action against the system under
  test, the call whose behavior the test exists to specify. Ideally a single
  statement or a single expression assigned to a result variable, so a reader
  can point at one line and say "this is the thing being tested."
- **Assert.** Compares the observed outcome, the return value, the resulting
  state, a thrown exception, or a recorded interaction, against the expected
  outcome, and fails the test with a clear message when they diverge.
- **Fixture Teardown (the implicit fourth phase).** Present in Meszaros's
  Four-Phase Test as an explicit phase, and present in Arrange-Act-Assert only
  implicitly, handled by the test runner's own lifecycle, a using block, a
  deferred call, or a framework-managed rollback, rather than written out as a
  fourth labeled section in the test body itself. Most AAA-style tests never
  write this phase because the resources involved, an in-process object graph,
  need no explicit cleanup, but any test that opens a real external resource
  still needs a real teardown even when the AAA comments do not show one.

## 6. ASCII structure diagram

```
+----------------------------------------------------------+
|                    Test Method Body                      |
|                                                            |
|  +------------------+   builds     +--------------------+ |
|  |     Arrange      | -----------> |  System Under Test | |
|  | (constructs SUT, |              |   + collaborators  | |
|  |  seeds input)    |              +--------------------+ |
|  +------------------+                        |            |
|                                               | one call   |
|                                               v            |
|                                    +--------------------+  |
|                                    |        Act         |  |
|                                    | (single triggering |  |
|                                    |     action)         |  |
|                                    +--------------------+  |
|                                               |            |
|                                    result /   |            |
|                                    state /    v            |
|                                    exception  |            |
|                                    +--------------------+  |
|                                    |       Assert        | |
|                                    |  compares observed  | |
|                                    |  outcome to expected| |
|                                    +--------------------+  |
+----------------------------------------------------------+
     (framework-managed teardown runs after this method,
      outside the three labeled phases)
```

## 7. Dynamics

At runtime, a single AAA test executes strictly top to bottom, and that strict
ordering is itself part of the contract, not an accident of how it happens to
be written.

```
Test runner          Arrange block        SUT / collaborators   Assert block
    |                      |                       |                |
    |--- invoke test ----->|                       |                |
    |                      |--- construct -------->|                |
    |                      |--- configure -------->|                |
    |                      |--- seed input -------->|                |
    |                      |  (Arrange complete,                     |
    |                      |   state fully known)                    |
    |                      |----- Act: one call --->|                |
    |                      |                       |--- executes -->|
    |                      |<--- result/exception --|                |
    |                      |----- hand off result -------------------->|
    |                      |                       |     compare observed
    |                      |                       |     vs expected value
    |<---------------------------- pass / fail -----------------------|
    |--- framework teardown (implicit, outside AAA phases) ---------->|
```

The sequence has one property that most of the failure modes in dimension 11
trace back to. once execution crosses from Arrange into Act, nothing should
mutate the starting state that Arrange established, and once execution crosses
from Act into Assert, nothing should trigger a second action. A test that
violates either boundary, by arranging something mid-Act or acting again
mid-Assert, has silently become a different, unlabeled structure wearing AAA's
comments.

## 8. Implementation variants

The three-word shape appears differently depending on the tooling and the
language, and recognizing the variant matters more than memorizing one literal
form.

- **Comment-labeled AAA.** The most common variant in plain xUnit-family
  frameworks (JUnit, NUnit, xUnit.net, pytest, Jest, Vitest, Go's `testing`
  package). Three inline comments, `// Arrange`, `// Act`, `// Assert`, mark
  the boundaries directly in the test body, exactly as shown in the Microsoft
  .NET guidance's own before-and-after examples cited in dimension 2.
- **Blank-line-only AAA.** The same three-part shape with the boundaries
  marked only by a blank line between sections, relying on the reader's
  familiarity with the convention rather than an explicit label. Common once a
  team has fully internalized the shape and finds the comments redundant.
- **Given-When-Then keyword DSL.** BDD frameworks turn the same three phases
  into first-class syntax. Cucumber's Gherkin defines the mapping explicitly.
  "Given steps are used to describe the initial context of the system," which
  functions as the Arrange phase, "When steps are used to describe an event,
  or an action," the Act phase, and "Then steps are used to describe an
  expected outcome... the step definition of a Then step should use an
  assertion," the Assert phase (Cucumber, "Gherkin Reference," cucumber.io,
  https://cucumber.io/docs/gherkin/reference/, verified 2026-08-02). Kotest's
  `BehaviorSpec` gives the same three keywords first-class status inside
  Kotlin test code itself, without a separate feature-file language, letting a
  test read `given("a broomstick") { when_("I sit on it") { then("I should be
  able to fly") { ... } } }` (Kotest, "Testing Styles,"
  https://kotest.io/docs/framework/testing-styles.html, verified 2026-08-02).
- **Four-Phase Test with explicit teardown.** Meszaros's fuller catalog form,
  used when the fixture genuinely needs an explicit fourth phase, a database
  transaction rollback, a temp directory deletion, a mock server shutdown,
  written as its own labeled block rather than folded silently into the test
  runner's lifecycle.
- **Parameterized or table-driven AAA.** A single Arrange-Act-Assert shape
  repeated across a table of inputs and expected outputs, common in Go's
  table-driven test convention and in parameterized test attributes (`@Theory`
  in xUnit.net, `@pytest.mark.parametrize` in pytest, `t.Run` sub-tests in Go).
  The Arrange phase here includes selecting the current row from the table;
  Act and Assert stay identical across rows, which is exactly the technique
  the Microsoft guidance recommends as the fix for the "Avoid multiple Act
  tasks" anti-pattern, converting several near-duplicate tests each with one
  Act into a single parameterized test with one Act per row.
- **Language-native assertion chains as compressed AAA.** In languages that
  favor fluent assertion libraries, AssertJ in Java, Chai in JavaScript, the
  Assert phase compresses into a single fluent expression, but the underlying
  three-part shape, build state, trigger one action, check the result, stays
  the same; only the Assert phase's surface syntax differs.

## 9. Known production uses

- **Microsoft's official .NET testing guidance** documents Arrange-Act-Assert
  by name as the recommended shape for .NET unit tests, with before-and-after
  code examples that add explicit `// Arrange`, `// Act`, `// Assert` comments
  to a test that previously mixed the phases, and a dedicated section, "Avoid
  multiple Act tasks," warning against combining more than one action inside a
  single test (Microsoft, "Best practices for writing unit tests," Microsoft
  Learn, https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-best-practices,
  verified 2026-08-02).
- **Cucumber**, one of the most widely deployed behavior-driven-development
  tools across Ruby, Java, JavaScript, and .NET codebases, implements the
  same three-phase structure as first-class Gherkin syntax, with its own
  reference documentation stating explicitly that Given, When, and Then map to
  putting the system in a known state, performing an action, and asserting an
  expected outcome (Cucumber, "Gherkin Reference," cucumber.io,
  https://cucumber.io/docs/gherkin/reference/, verified 2026-08-02).
- **Kotest**, the primary property-based and specification-style testing
  framework for the Kotlin language, ships `BehaviorSpec` as one of its
  built-in testing styles specifically to give Given-When-Then structure
  first-class status inside ordinary Kotlin test source files, without
  requiring a separate feature-file language (Kotest, "Testing Styles,"
  https://kotest.io/docs/framework/testing-styles.html, verified 2026-08-02).
- **Gerard Meszaros's xUnit Test Patterns catalog**, the reference work that
  the wider xUnit-family testing community, JUnit, NUnit, and their many
  ports, draws its shared vocabulary from, names the same shape Four-Phase
  Test and treats it as the default organizing structure for any test written
  against an xUnit-style framework (Gerard Meszaros, *xUnit Test Patterns.
  Refactoring Test Code*, Addison-Wesley, 2007, the pattern named Four-Phase
  Test).

## 10. Consequences

This dimension states a degree of cost and benefit that is a matter of
engineering judgement informed by the sourced material above, not itself an
independently verifiable claim per line.

Positive.

- A failing test becomes fast to diagnose, because the reader can jump
  straight to the labeled Assert section, see exactly what was expected, and
  work backward only as far as they need to.
- The discipline of writing a complete Arrange section surfaces hidden
  dependencies and implicit shared state before they become the cause of an
  intermittent failure somewhere else in the suite.
- New team members can read any test in the suite the same way once they have
  learned the shape once, which lowers the cost of learning an unfamiliar
  codebase's test suite specifically.
- Restricting Act to one action, as the Microsoft guidance recommends
  explicitly, makes each test's failure attributable to exactly one line, which
  matters because most test frameworks stop reporting after the first failed
  assertion, so a test with several actions and only the first one's outcome
  actually gets checked hides information about the rest.
- The pattern composes cheaply with parameterized and table-driven testing,
  because the Arrange and Assert logic can be shared across rows while each
  row supplies different Act inputs and expected outcomes.

Negative.

- Strict adherence produces visible ceremony, three comment lines and often a
  blank line each, in every single test, which adds real vertical space across
  a suite with thousands of tests.
- The pattern says nothing about how much duplicated Arrange code is
  acceptable across many similar tests, and teams that mechanically avoid
  shared fixtures in the name of AAA can end up with substantial copy-pasted
  setup code that itself becomes a maintenance burden.
- Forcing the shape onto scenarios that are honestly a sequence of interleaved
  actions and checks, covered in dimension 4, produces either an unreadable
  single mega-test or an artificial and misleading structure.
- The pattern gives no guidance on assertion quality. a test can be
  perfectly AAA-shaped and still assert something so loose, or so tightly
  coupled to implementation detail, that it provides little real protection,
  see dimension 11.
- Comment-labeled AAA is easy to fake. adding the three comments without
  actually separating the concerns, for example performing part of the
  Arrange work inside the Act line, gives a false signal of discipline that a
  skimming reviewer will not catch without reading closely.

## 11. Failure modes and misuse

Failure modes 5 and 6 in the table below are drawn from general testing
practice and code review experience rather than from a single citable source;
they describe symptoms observed repeatedly across xUnit-family codebases.

| Symptom | Cause | Fix |
|---|---|---|
| A test fails and the failure message alone gives no clue what actually changed, only that some deeply nested assertion did not match | The Assert phase asserts on an entire object graph or a whole collection with a generic equality check instead of the specific field the test cares about | Assert on the narrowest meaningful value, or use a diffing assertion library that reports exactly which field diverged |
| A test occasionally fails on CI but never locally, and the failure moves around between unrelated tests | The Arrange phase relies on state left behind by a previous test, a shared static, a database row from another test, an un-reset clock or random seed | Make Arrange fully self-contained. construct fresh state, reset shared singletons, and isolate the database transaction per test |
| A refactor that changes no observable behavior still breaks a large fraction of the suite | Assertions check internal implementation details, private method call counts, exact SQL text, internal field values, rather than externally observable outcomes | Move assertions to the public contract, the return value or the externally visible state, and reserve interaction assertions for the collaborators the behavior genuinely depends on |
| A single test failure produces ten more failures in the same run and it is unclear which one is the real cause | Several tests share Arrange logic through a mutable fixture object, and the first Act mutates that shared fixture, corrupting the state the remaining tests assume | Give every test its own fresh Arrange, never share a mutable fixture instance across tests without an explicit and complete reset between them |
| A reviewer approves a test with `// Arrange`, `// Act`, `// Assert` comments, but the test still reads confusingly | The comments were added mechanically without actually separating the phases, for example a configuration call sits in the Act block, or an assertion runs before the triggering action completes | Read past the comments and verify the phase boundaries are real. no state-building calls after the labeled Act line, no triggering calls after the labeled Assert line |
| A test with multiple Act calls passes locally but a later change makes only the second Act's assertion fail, and nobody notices for weeks because the first assertion kept passing | Multiple triggering actions were combined into one test to save keystrokes, each with its own assertion, exactly the anti-pattern the Microsoft guidance names "multiple Act tasks" | Split into one test per Act, or convert to a parameterized test with one Act shared across rows, as described in dimension 8 |
| The test suite takes minutes to run and developers stop running it locally before pushing | Arrange sections repeatedly build expensive real collaborators, a real database connection, a real HTTP client, instead of a lightweight test double | Replace expensive real collaborators in the Arrange phase with the appropriate test double, Dummy, Stub, Fake, Spy, or Mock, chosen by the role the collaborator actually plays in the test, see dimension 13 |
| A BDD-style Given-When-Then feature file duplicates plain-language explanation of a test that a unit test right below it already covers precisely | The team adopted Given-When-Then keyword syntax for every test regardless of audience, rather than reserving it for scenarios genuinely meant to be read by non-programmers | Use comment-labeled or blank-line AAA for developer-facing unit tests, and reserve the keyword DSL for scenarios that exist to be reviewed by product owners or testers, per the applicability guidance in dimension 4 |

## 12. Trade-off matrix

Comparison against the two named sibling structures and one named alternative
organizing approach, across the forces named in dimension 3.

| Force | Arrange-Act-Assert (comment/blank-line) | Given-When-Then (Cucumber, Kotest BehaviorSpec) | Four-Phase Test (Meszaros, explicit teardown) | Shared class-level Setup/Teardown fixture |
|---|---|---|---|---|
| Readability at failure time | High, phases are visually distinct inside the failing method | High, and additionally readable by non-programmers because the keywords are natural language | High, and the teardown phase is explicit rather than implicit | Lower, the precondition a failing test actually depends on is often defined outside the failing method entirely |
| Setup reuse across many tests | Low by convention, each test typically re-states its own Arrange | Low to moderate, Background/context blocks allow some shared Given steps | Low, same convention as AAA | High, one Setup method serves every test in the class |
| Risk of shared mutable state between tests | Low, because each test constructs its own state | Low for the same reason | Low for the same reason | Higher, a Setup fixture reused across tests can leak state if any test mutates it, see the failure mode table above |
| Audience | Developers reading and reviewing code | Developers, testers, and product owners jointly, when feature files are the shared artifact | Developers, with an explicit resource-cleanup contract | Developers, with implicit trust in the shared fixture's correctness |
| Tooling cost | None, plain comments in any framework | Requires a BDD framework and, for Cucumber, a separate feature-file authoring workflow | None beyond framework-provided teardown hooks | Framework-provided `Setup`/`TearDown` attributes, present in most xUnit-family frameworks |
| Fit for a sequence of interleaved actions | Poor, forces an artificial single-Act shape, see dimension 4 | Moderate, And/But keywords extend a scenario across several steps naturally | Moderate for the same reason | Poor for the same reason as AAA |

## 13. Related and incompatible patterns

Arrange-Act-Assert composes tightly with the test-double family that occupies
the rest of this repository's testing catalog. the Arrange phase is precisely
where a Dummy, Stub, Fake, Spy, or Mock gets constructed and wired into the
system under test, and the choice among those five roles determines what the
Assert phase is even able to check, a state-verifying assertion against a
Stub's returned value versus a behavior-verifying assertion against a Mock's
recorded call. Test-Driven Development is the workflow-level pattern that
Arrange-Act-Assert most often serves. Kent Beck's own book, which cites the
same three-part shape, describes a red-green-refactor cycle in which each
cycle begins by writing exactly one AAA-shaped test for the next small
increment of behavior.

The Four-Phase Test and Given-When-Then names are not competitors to
Arrange-Act-Assert so much as the same idea wearing different clothes for a
different audience or a different tooling world, as established earlier in
this entry's lineage section. Choosing one over another inside a single
codebase is a convention decision, not a structural incompatibility, though
mixing all three naming styles inside one suite without a stated reason does
cost the consistency benefit described in dimension 3.

Nothing about Arrange-Act-Assert is structurally incompatible with any other
pattern in this catalog. it constrains only the internal shape of a test
method's body. Where it does create genuine friction is with heavy shared
class-level fixtures, `@BeforeEach`/`@BeforeClass`-style setup that runs
implicitly before every test in a class, because a shared fixture pulls part
of the Arrange phase outside the test body the reader is looking at, which is
the specific trade-off named in the "Setup reuse" row of dimension 12.

## 14. Refactoring path in and out

Introducing Arrange-Act-Assert into an existing, unshaped test.

1. Identify the single triggering action, the one call whose behavior the
   test exists to specify, and move every line that must run before it above
   that call.
2. Move every line that checks an outcome, an assertion, an exception check, a
   recorded-call check, below the triggering call.
3. Add the three labeling comments, or a blank line between each phase, so the
   boundaries are visible without having to read every line to find them.
4. If the triggering call is currently duplicated, because the original test
   performed more than one action, split the test into one test per action,
   per the "Avoid multiple Act tasks" guidance cited in dimension 9, or
   convert the shared parts into a parameterized test as described in
   dimension 8.
5. If any Arrange line depends on state left behind by a previous test, make
   it self-contained by constructing that state fresh inside this test's own
   Arrange phase, which is also the fix named in the flaky-test row of
   dimension 11.

Removing Arrange-Act-Assert, or more precisely, relaxing it, when a test has
outgrown the shape.

1. Confirm the test genuinely needs an interleaved act-assert-act-assert
   sequence, per the non-applicability list in dimension 4, rather than simply
   being poorly split.
2. If it is a genuine state-machine or sequence test, split each transition
   into its own smaller AAA test where possible, since one clean assertion per
   transition is almost always more valuable than one long test asserting an
   entire sequence at once.
3. Where splitting is not possible, because the transitions genuinely depend
   on shared, expensive state, label each act-assert pair explicitly with a
   comment naming the transition, preserving the spirit of labeled phases
   even though the literal one-Arrange-one-Act-one-Assert shape no longer
   fits.
4. If the team is migrating toward BDD tooling for a specific class of
   scenario, convert the Arrange, Act, Assert comments into the equivalent
   Given, When, Then keywords rather than deleting the structure entirely, per
   the mapping given in dimension 8.

## 15. Testing and verification

This dimension is inherently about practice rather than an independently
sourced factual claim, and is presented as such.

Arrange-Act-Assert does not need its own separate test, because it is a shape
imposed on tests themselves rather than production code, but the shape is
checkable in code review and, to a partial degree, mechanically. A reviewer
checking whether a test genuinely follows AAA looks for three things. exactly
one triggering call that is not itself an assertion, no state-mutating call
after that trigger, and no state-mutating call inside the Assert section.
Static analysis tools that flag "multiple assertions" or "assertion roulette,"
several unrelated assertions with no message distinguishing which one failed,
catch a related but distinct problem, an over-loaded Assert phase rather than
a broken Arrange/Act boundary, and are a useful additional check rather than a
substitute for reading the test.

Because AAA-shaped tests build their own state in the Arrange phase, they are,
as a direct consequence, easier to run in any order and in parallel, since
nothing depends on another test having run first. A suite that cannot pass
when its tests are shuffled or run in parallel is strong evidence that some
tests are silently sharing state through a mechanism the Arrange phase does
not make visible, most often a shared mutable fixture or a real, un-isolated
external resource such as a database.

## 16. Observability signals

A healthy AAA-shaped suite shows a specific, recognizable pattern in its own
test-run output and history. individual test names read as full sentences
describing behavior, per the naming convention the Microsoft guidance
recommends, method under test, scenario, expected behavior, and failure
output points directly at one specific expected-versus-actual mismatch rather
than a stack trace through unrelated setup code. Test run duration per test
stays low and consistent, because a properly isolated Arrange phase avoids
slow, shared, real dependencies.

A degrading suite shows the opposite pattern and is worth watching for over
time. an increasing count of tests whose Assert phase reports a diff across an
entire object rather than a single field, a rising rate of intermittent
failures that move between unrelated tests run-to-run, which points at shared
mutable Arrange state, and Arrange sections that grow in line count over time
without a corresponding growth in the behavior being tested, which points at
either an accreting shared fixture being copy-pasted per test or a system
under test whose construction has become too complicated to build directly,
both of which are signals worth raising in review rather than routine
maintenance to absorb silently.

## 17. Security and privacy implications

Arrange-Act-Assert is a test-authoring convention with no runtime component of
its own, so it introduces no attack surface directly. Its one real security
and privacy implication is indirect and lives entirely inside the Arrange
phase. because Arrange is the section where realistic-looking input data gets
constructed, it is also the section most likely to accumulate copy-pasted
production data, a real customer name, a real email address, a real API key
pulled from a log during debugging, if the test author reaches for a quick,
realistic example rather than synthetic data. A consistent, labeled Arrange
phase makes this risk easier to check for specifically because the section
that constructs input data is always in the same, predictable place in every
test, which is a real, if modest, benefit for a team running secret-leak or
PII scanners against a test suite. The absence of a labeled structure would
not change the underlying risk, real data can leak into any unstructured
test's setup lines too, but it would make that risk harder to scan for
systematically, since the setup lines are not consistently distinguishable
from the rest of the method.

## 18. References

- Bill Wake, "3A - Arrange, Act, Assert," xp123.com,
  https://xp123.com/articles/3a-arrange-act-assert/, verified 2026-08-02.
- Kent Beck, *Test-Driven Development. By Example*, Addison-Wesley, 2003, page
  97, cited per Wake's retrospective above as the earliest widely read
  publication to reference the same shape after Wake's original 2001
  observation.
- Gerard Meszaros, *xUnit Test Patterns. Refactoring Test Code*,
  Addison-Wesley, 2007, the pattern named Four-Phase Test.
- Martin Fowler, "GivenWhenThen," martinfowler.com,
  https://martinfowler.com/bliki/GivenWhenThen.html, verified 2026-08-02.
- Cucumber, "Gherkin Reference," cucumber.io,
  https://cucumber.io/docs/gherkin/reference/, verified 2026-08-02.
- Kotest, "Testing Styles," kotest.io,
  https://kotest.io/docs/framework/testing-styles.html, verified 2026-08-02.
- Microsoft, "Best practices for writing unit tests," Microsoft Learn,
  https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-best-practices,
  verified 2026-08-02.

## Code examples

### TypeScript

```typescript
class Wallet {
  private cents: number;

  constructor(startingCents: number) {
    this.cents = startingCents;
  }

  withdraw(amountCents: number): void {
    if (amountCents > this.cents) {
      throw new Error("insufficient funds");
    }
    this.cents -= amountCents;
  }

  balance(): number {
    return this.cents;
  }
}

function assertEqual(actual: number, expected: number, label: string): void {
  if (actual !== expected) {
    throw new Error(`${label}: expected ${expected}, got ${actual}`);
  }
}

function testWithdrawReducesBalanceByAmount(): void {
  // Arrange
  const wallet = new Wallet(500);

  // Act
  wallet.withdraw(200);

  // Assert
  assertEqual(wallet.balance(), 300, "balance after withdrawal");
}

testWithdrawReducesBalanceByAmount();
console.log("ok");
```

### Python

```python
class ShoppingCart:
    def __init__(self):
        self._items = []

    def add_item(self, price_cents, quantity):
        self._items.append((price_cents, quantity))

    def total_after_discount(self, percent):
        subtotal = sum(price * qty for price, qty in self._items)
        return subtotal - (subtotal * percent // 100)


def test_total_after_discount_applies_percent_off_subtotal():
    # Arrange
    cart = ShoppingCart()
    cart.add_item(price_cents=1000, quantity=2)

    # Act
    total = cart.total_after_discount(percent=10)

    # Assert
    assert total == 1800


if __name__ == "__main__":
    test_total_after_discount_applies_percent_off_subtotal()
    print("ok")
```

### Go

```go
package main

import "testing"

type Order struct {
	items []int
}

func (o *Order) AddItem(priceCents int) {
	o.items = append(o.items, priceCents)
}

func (o *Order) Total() int {
	sum := 0
	for _, price := range o.items {
		sum += price
	}
	return sum
}

func TestTotalSumsAllItemPrices(t *testing.T) {
	// Arrange
	order := &Order{}
	order.AddItem(1200)
	order.AddItem(800)

	// Act
	total := order.Total()

	// Assert
	if total != 2000 {
		t.Fatalf("expected 2000, got %d", total)
	}
}
```
