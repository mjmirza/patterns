---
name: Given-When-Then
slug: given-when-then
family: 14-testing
category: Testing
aliases: [GWT, Four-Phase Test variant, Arrange-Act-Assert (Given-Then framing)]
first_described: "Daniel Terhorst-North and Chris Matts, early 2000s, as part of Behavior-Driven Development"
maturity: canonical
related: [test-double, page-object, builder, four-phase-test]
incompatible_with: []
verified: 2026-08-02
---

# Given-When-Then

## 1. Name, aliases, and lineage

The canonical name is Given-When-Then, usually shortened to GWT. It is a style
for expressing a test or a specification as three labelled sections. Given
sets up the starting state of the system. When performs the single action or
event under test. Then states the observable outcome that must hold.

The technique was developed by Daniel Terhorst-North and Chris Matts as part
of Behavior-Driven Development, the discipline North built out of Test-Driven
Development in the early 2000s while looking for a naming convention that
would stop developers from asking where to start when writing a test and stop
business readers from being excluded by test-first jargon (Martin
Fowler, "GivenWhenThen", martinfowler.com bliki,
https://martinfowler.com/bliki/GivenWhenThen.html, verified 2026-08-02, which
states the technique "is an approach developed by Daniel Terhorst-North and
Chris Matts as part of Behavior-Driven Development"). Fowler's page also
records the closest formal relative. Given-When-Then is "a reformulation of
the Four-Phase Test pattern," the setup, exercise, verify, teardown structure
that Kent Beck's xUnit family already used, and it sits next to the informal
convention Bill Wake named Arrange-Act-Assert, which carries the identical
three-part shape under different labels (same source).

The concrete syntax most engineers meet first is Gherkin, the plain-text
language that Cucumber and its ports (SpecFlow for .NET, Behave for Python,
Cucumber-JVM for Java) parse into executable steps. The Gherkin reference
states plainly that the purpose of a `Given` step is to "put the system in a
known state," that a `Then` step's outcome "should be on an observable
output," and that `And` and `But` exist purely so a scenario with several
steps of the same kind reads fluidly rather than repeating the keyword
(Cucumber Ltd, "Gherkin Reference," cucumber.io docs,
https://cucumber.io/docs/gherkin/reference/, verified 2026-08-02). The same
reference notes a detail that surprises newcomers. Cucumber's step matcher
ignores which keyword introduced a step, so "Given X" and "Then X" collide as
duplicate step definitions if their text is identical. The keyword is a
device for the human reader, not a dispatch mechanism for the runner.

A second lineage worth naming because it is frequently conflated with GWT.
Gherkin's own predecessor inside the Ruby community was RSpec's `describe` and
`it` blocks, and the BDD framework JBehave, which North also built, used the
same three-word structure in plain text years before Cucumber existed. Given-
When-Then is therefore not tied to any one tool. It is a naming discipline
for structuring a test body, and it appears both as literal prose parsed by a
framework and as a comment or method-naming convention inside an ordinary
xUnit-style test with no Gherkin runner at all.

## 2. Problem and context

A test file with no shape reads as an undifferentiated block of setup calls,
one action, and a pile of assertions, and a reader cannot tell at a glance
which lines are preconditions, which line is the behavior under test, and
which lines are the actual check. The problem sharpens in three concrete
ways.

A newcomer writing their first test does not know where the test starts. Do
you assert first and work backward, or build the object graph first and hope
the right assertion falls out. Fowler's account of the technique's origin
records exactly this complaint from developers new to test-first work, which
Given-When-Then answers by giving a fixed order to write and read in.

A business reader, product owner, or domain expert who is not a
programmer cannot read a JUnit method body and confirm it says what the
business rule says. A three-clause template written as plain sentences, "given
a cart with two items, when the customer applies a valid promo code, then the
total is discounted by ten percent," is legible to that person without
needing to read code, which is the entire premise of Behavior-Driven
Development and the reason Cucumber's Gherkin format exists as a
human-readable executable specification rather than only a code convention.

A test suite that grows past a few dozen cases develops mixed concerns inside
individual tests. Setup code, the action, and multiple unrelated assertions
interleave, so a single failing test can fail for several unrelated reasons at
once and the diff a reader must inspect to find the cause grows. A fixed
three-part shape forces one action per test and pushes multi-fact checking
into a clearly bounded Then section, which is the same discipline the
Four-Phase Test pattern names for xUnit-style tests generally.

The context in which the pattern belongs is any executable check, unit test,
integration test, or acceptance test, where a single stimulus produces an
observable, checkable result and the reader benefits from knowing which part
of the test is precondition, which part is action, and which part is
verification.

## 3. Forces

- **Readability for a non-programmer.** Favoured strongly. This is the
  pattern's whole reason to exist in the BDD lineage. A plain-English Gherkin
  scenario is reviewable by a product owner who has never opened an IDE.
- **Precision and expressiveness of assertions.** Partly sacrificed in the
  Gherkin form. Step text must stay generic enough to be reused across
  scenarios, which pushes detailed comparison logic into step definition code
  the business reader never sees, so the visible specification can drift from
  what the code actually checks.
- **Test isolation and single responsibility.** Favoured. One Given, one
  When, one Then per scenario is the intended discipline, and a scenario that
  needs two Whens is a signal the scenario covers two behaviors.
- **Onboarding speed for new contributors.** Favoured. A fixed three-part
  order removes the where-do-I-start problem for anyone writing their first
  test in the style.
- **Runtime cost and CI duration.** Sacrificed when combined with a full
  Gherkin runner and step-matching regex layer, and end-to-end infrastructure
  such as a browser driver, because the indirection between plain text and
  executable code adds parsing and matching overhead per scenario, and Given-
  When-Then style is disproportionately used at the acceptance-test layer
  where the system under test is the whole application rather than one unit.
- **Maintenance cost of the step library.** Sacrificed as the suite grows.
  Cucumber-style step definitions accumulate into a shared vocabulary that
  must be kept consistent, deduplicated, and discoverable, and an
  undisciplined team lets duplicate or near-duplicate steps proliferate.
- **Coupling between specification and implementation detail.** The pattern
  favours decoupling when Given and When steps describe business intent
  ("given a logged-in customer") rather than mechanism ("given a session
  cookie named SID is set"), and it silently reintroduces coupling the moment
  a team lets implementation detail leak into step text, at which point the
  specification stops being reviewable by a non-technical reader and the
  main force the pattern optimizes for is lost.

## 4. Applicability and non-applicability

Reach for Given-When-Then when the following hold.

- The behavior under test can be described as one starting state, one
  stimulus, and one observable outcome. This covers the overwhelming majority
  of unit and integration tests regardless of whether a Gherkin runner is in
  use.
- A non-technical reader, product owner, business analyst, or QA
  engineer with no programming background needs to read, write, or review the
  specification, which is the case Behavior-Driven Development and Gherkin
  were built for.
- The team wants living documentation, executable specifications that stay
  correct because a broken scenario fails the build, rather than a prose
  requirements document that quietly diverges from the shipped behavior.
- An acceptance-test or end-to-end layer needs a shared vocabulary of
  business-level actions (log in, add to cart, apply coupon) that many
  scenarios reuse, which amortizes the cost of building step definitions
  across the whole suite.
- A team is standardizing test structure across many contributors and wants a
  mechanically checkable convention (a linter or code-review rule) for what a
  well-formed test body looks like.

Do NOT reach for Given-When-Then, or reach for it with restraint, in these
cases, and the reason matters more than the rule.

- **A pure, single-input, single-output function with no meaningful state.** A
  parser, a formatter, or an arithmetic function tested with a small table of
  input-output pairs is better served by a parameterized or table-driven test
  than by three narrative labels around a one-line assertion. Wrapping
  `add(2, 3) == 5` in Given, When, Then adds ceremony without adding
  readability.
- **The team has no non-technical reader and no living-documentation goal.**
  If every reader of the suite is a programmer and nobody reviews scenarios in
  plain English, the Gherkin indirection (feature files, step regex matching,
  a glue layer) buys nothing over calling functions directly inside an
  Arrange-Act-Assert-shaped unit test, and it adds a real maintenance cost, see
  dimension 11.
- **The scenario genuinely needs multiple independent actions to describe one
  business transaction, such as a saga or a multi-step wizard.** Forcing a
  single When onto a five-step checkout flow either produces one enormous When
  clause that hides sequencing, or an artificial split into several scenarios
  that cannot express the ordering dependency between them. A state-machine
  test or a scenario outline with an explicit step table serves this case
  better than a single When.
- **Performance-sensitive test suites where thousands of table-driven cases
  run per commit.** The narrative wrapper and, in the Gherkin form, the
  regex-based step matching, add measurable overhead per case at that volume
  compared to a bare parameterized test loop.
- **The specification is really a data validation matrix, not a behavior.**
  Testing that twelve different malformed email strings are all rejected is a
  parameterized-input problem. A Given-When-Then scenario per malformed string
  multiplies boilerplate for no narrative gain, because there is no
  meaningfully different "given" or "when" across the twelve cases, only a
  different input value.
- **The team cannot yet write a Then clause that describes an observable
  outcome rather than an implementation detail.** Fowler's page states plainly
  that the Then section should describe changes expected due to the specified
  behavior, and the Gherkin reference reinforces that an outcome should be on
  an observable output. A team that keeps writing Then clauses asserting
  internal method calls or private field values has not solved a testing
  problem by adopting the labels, it has only renamed the same brittle test.

## 5. Structure

Three named phases, in fixed order, each with a distinct responsibility.

- **Given.** Establishes the precondition, the state of the world before the
  behavior under test runs. Implemented as object construction, fixture
  loading, test-double wiring, or a sequence of prior domain operations that
  bring the system to the state the scenario needs. May be a single line or a
  short chain of setup calls, but must never itself contain the action under
  test.
- **When.** Performs exactly one stimulus, the single action, event, command,
  or message that the scenario exists to verify the effect of. Ideally one
  method call or one dispatched event. A When section with more than one
  meaningfully distinct action is a signal the scenario is testing more than
  one behavior.
- **Then.** States the expected, observable outcome. An assertion or a set of
  closely related assertions about state that changed, a value that was
  returned, an event that was published, or a side effect that occurred. The
  Gherkin reference's guidance that a `Then` step's outcome "should be on an
  observable output" applies whether or not a Gherkin runner is in use. assert
  what a caller of the system can see, not an internal implementation detail.
- **And, But (optional connectors).** Not a fourth phase. A syntactic device,
  in both prose Gherkin and in code comments following the same convention,
  that continues the most recent Given, When, or Then without repeating the
  keyword, used when a scenario genuinely needs several preconditions or
  several related assertions.

In the Gherkin form there are two further participants worth naming, because
production Cucumber-family suites are built around them.

- **Feature file.** The plain-text document holding one or more scenarios
  under a shared feature description, the unit a non-technical reader opens.
- **Step definition.** The code, tied to a regular expression or a Cucumber
  Expression, that a runner matches against each Given, When, or Then line
  and executes. This is the layer where the narrative meets the system under
  test, and it is invisible to the reader of the feature file.

## 6. ASCII structure diagram

```
   +----------------------------------------------------------+
   |                     Scenario / Test                      |
   |------------------------------------------------------------
   |                                                            |
   |  +----------------+   sets up state    +----------------+ |
   |  |     Given      |------------------->|  System under  | |
   |  |  (precondition)|                    |     test       | |
   |  +----------------+                    +----------------+ |
   |                                               |            |
   |  +----------------+   single stimulus         v            |
   |  |      When      |------------------> [ mutation / call ] |
   |  |    (action)    |                           |            |
   |  +----------------+                           v            |
   |                                        +----------------+  |
   |  +----------------+   asserts on       |  Observable    |  |
   |  |      Then      |<-------------------|  outcome       |  |
   |  |   (outcome)    |                    +----------------+  |
   |  +----------------+                                        |
   +------------------------------------------------------------+

   In the Gherkin variant, Given/When/Then are plain-text lines in a
   .feature file, each matched at runtime to a step definition.

   .feature file line          step definition (code)
   "Given a cart with 2 items" -----> matches regex -----> setup code
   "When a 10% coupon is applied" --> matches regex -----> action code
   "Then the total is discounted"---> matches regex -----> assertion code
```

## 7. Dynamics

Two runtime shapes exist, and it matters which one a codebase uses because
they fail differently and are debugged differently.

**Direct form, no external runner.** The three phases are ordinary code
inside one test method, separated by blank lines or comments reading Given,
When, Then. Nothing parses text at runtime, the labels are documentation only.

```
Test runner            Test method body
    |                       |
    |-- invoke test ------->|
    |                       |-- Given. build fixture, seed state
    |                       |-- When.  call the one action
    |                       |-- Then.  assert on the result
    |<-- pass/fail ---------|
```

**Gherkin form, with a Cucumber-family runner.** The feature file is parsed
first, each line is matched to a registered step definition, and the step
definitions execute in the same order the feature file lists them, sharing
state through a per-scenario context object (often called a World in
Cucumber, or an autowired context object in JBehave and SpecFlow ports).

```
CI job         Cucumber runner        Step definitions        SUT
  |                  |                       |                 |
  |-- run suite ---->|                       |                 |
  |                  |-- parse .feature ---->|                 |
  |                  |-- match "Given .." -->|-- Given code --->|
  |                  |                       |   (build state)  |
  |                  |-- match "When .." --->|-- When code ---->|
  |                  |                       |   (one action)   |
  |                  |-- match "Then .." --->|-- Then code ---->|
  |                  |                       |   (assertion)    |
  |                  |<-- pass/fail per step-|                 |
  |<-- report -------|                       |                 |
```

One timing detail that matters in production suites. If a Given step or a
When step throws, Cucumber-family runners typically mark the remaining steps
in that scenario as skipped rather than failed, which is a common source of
confusion for a reader who sees a scenario reported as failed on its Then step
when the real fault happened earlier in an unrelated Given. Reading the full
step trace, not only the first red line, is required to locate the actual
failure.

## 8. Implementation variants

**Bare xUnit style, no framework.** Given, When, Then exist only as comments
or blank-line-separated blocks inside a normal `@Test`, `def test_...`, or
`it(...)` body. Zero dependencies, zero indirection, and the fastest to run.
This is the variant most codebases actually use, and it is the one to default
to unless a non-technical reader genuinely needs the specification.

**Gherkin plus a Cucumber-family runner.** Cucumber-JVM, Cucumber.js,
Behave (Python), SpecFlow and Reqnroll (.NET), Godog (Go). Feature files are
plain text, versioned alongside code, and readable without opening an IDE.
Adds a step-matching layer, a shared-context object per scenario, and a
separate build step to keep step definitions and feature files in sync.

**Fluent builder chaining, "given().when().then()".** A DSL such as
REST-assured (Java, HTTP API testing) or Kotlin's Kotest exposes literal
`given()`, `when()`, `then()` methods that return a chainable builder, so the
three-part shape is enforced by the type system rather than by comments or a
text parser. This variant keeps GWT readability without a text-parsing layer,
at the cost of tying the test to that specific fluent API.

**Scenario outline / example table.** The Gherkin family extends a single
scenario with a table of example rows, each row supplying different values
for the same Given-When-Then shape, collapsing what would otherwise be many
near-duplicate scenarios into one narrative plus a data table. This is the
Gherkin-native answer to the table-driven test case named as a
non-applicability concern in dimension 4, and it resolves that concern when a
non-technical reader genuinely needs to see the data.

**Given-When-Then as a naming convention with a linter.** Some teams enforce
the three-section discipline without any runner at all, using a code-review
checklist or a static-analysis rule that a test method body contains
recognisable Given/When/Then comment markers or that only one distinct call
into the system under test appears between the Arrange block and the assert
block. This variant gets the single-responsibility discipline without any
runtime cost or extra dependency.

**Property-based framing.** A property-based test (see the property-based
testing entry) can be described as Given a generator of arbitrary inputs
satisfying a precondition, When the operation runs, Then an invariant holds
for all generated inputs, which is Given-When-Then with the Given widened
from one fixture to a generator and the Then widened from one expected value
to a universally quantified property.

## 9. Known production uses

**Cucumber, the reference implementation of the pattern's Gherkin syntax.**
Cucumber's own documentation states that the Given step's purpose is to "put
the system in a known state" and that a Then step's outcome "should be on an
observable output," which is the canonical, tool-maintained statement of the
pattern's contract (Cucumber Ltd, "Gherkin Reference," cucumber.io docs,
https://cucumber.io/docs/gherkin/reference/, verified 2026-08-02).

**SpecFlow / Reqnroll for .NET.** SpecFlow (rebranded and continued as the
open-source project Reqnroll after SpecFlow's commercial sunset) ports the
identical Gherkin Given/When/Then syntax to .NET, generating a step-binding
class from attributed methods that a build step matches against feature
files, used widely across .NET projects for acceptance testing (SpecFlow /
Reqnroll project documentation, https://docs.reqnroll.net/latest/, verified
2026-08-02, which documents `[Given]`, `[When]`, `[Then]` step attributes
matching the same three-clause structure).

**Behave for Python.** Behave implements the same Gherkin syntax for Python
projects, registering `@given`, `@when`, `@then` decorated functions as step
implementations matched against `.feature` files, and is the most widely used
BDD runner among Python testing tools (Behave project documentation,
https://behave.readthedocs.io/en/latest/, verified 2026-08-02).

**REST-assured for Java HTTP API testing.** REST-assured exposes a fluent
`given().contentType(...).when().get(...).then().statusCode(200)` chain as its
primary API shape, encoding Given-When-Then directly into the type-level DSL
rather than into parsed text, and is a de facto standard for Java REST API
test code (REST-assured project documentation and usage guide,
https://rest-assured.io/, verified 2026-08-02, whose front page and usage
examples present the given-when-then chain as the library's core syntax).

**xUnit-style test suites documented under the Four-Phase Test name.**
Martin Fowler's own account explicitly frames Given-When-Then as "a
reformulation of the Four-Phase Test pattern," the setup-exercise-verify-
teardown shape that Gerard Meszaros catalogued for the whole xUnit family
(JUnit, NUnit, pytest, and their relatives), which means every xUnit-style
suite that follows the setup/exercise/verify convention, whether or not it
uses the words Given, When, Then, is running the structurally identical
pattern under different labels (Martin Fowler, "GivenWhenThen,"
https://martinfowler.com/bliki/GivenWhenThen.html, verified 2026-08-02).

## 10. Consequences

Positive.

- A fixed, predictable structure removes the where-do-I-start problem for a
  contributor writing their first test, because Given, When, Then always
  come in that order.
- In the Gherkin form, the specification is legible and reviewable by a
  non-technical reader without reading code, which is the pattern's
  founding purpose inside Behavior-Driven Development.
- A well-formed scenario is naturally single-responsibility, one action, one
  outcome, which makes a failing test's cause easier to isolate than a test
  with several intermixed actions and assertions.
- In the Gherkin form, feature files become living documentation. Because a
  broken scenario fails the build, the specification cannot silently drift
  out of sync with the shipped behavior the way a prose requirements document
  can.
- A shared step-definition vocabulary in the Gherkin form amortizes cost.
  Once "given a logged-in customer" exists, every future scenario that needs
  a logged-in customer reuses it for free.

Negative.

- In the Gherkin form, an entire extra layer exists between the readable
  specification and the executable code, feature files, step matching, and a
  glue layer, which is infrastructure to build and maintain that a bare
  Arrange-Act-Assert test does not need.
- Step definitions can drift from feature-file text in wording while still
  matching by regex, and a poorly maintained step library accumulates
  duplicate or near-duplicate steps that different scenarios call by slightly
  different phrasing, fragmenting the shared vocabulary the pattern is
  supposed to build.
- The three labels alone guarantee nothing about test quality. A Then clause
  that asserts an internal implementation detail rather than an observable
  outcome is exactly as brittle under the Given-When-Then label as under any
  other label, the pattern gives structure, not correctness.
- Overuse on cases that do not need narrative readability, single pure
  functions, data-validation matrices, adds ceremony that a table-driven test
  or a plain assertion communicates faster.
- A non-technical reader's trust in the specification depends on the
  step definitions genuinely doing what the text claims, and nothing in the
  pattern itself verifies that. A step named "Given a valid customer" can
  silently stop constructing a genuinely valid customer as the domain model
  evolves, and the feature file keeps reading as if it still does.

## 11. Failure modes and misuse

**Implementation detail leaking into step text.** Symptom. A feature file
line reads "Given the SESSION_TOKEN cookie is set to a JWT signed with
HS256," which no product owner can review or approve. Cause. The team wrote
the specification from the code outward instead of from the business
behavior outward. Fix. Rewrite the Given in business language ("given a
logged-in customer") and push the mechanism into the step definition, where
implementation detail belongs.

**Multiple Whens in one scenario.** Symptom. A scenario body contains three
consecutive `When` lines performing unrelated actions, and when it fails, it
is unclear from the report which action actually broke. Cause. The scenario
is really testing a multi-step workflow rather than one behavior. Fix. Split
into several scenarios each with one When, or, if the sequencing itself is
the thing under test, use a scenario outline or an explicit sequence-diagram-
style integration test rather than forcing the workflow into one GWT
scenario.

**Then asserting on internal state instead of observable output.** Symptom.
The Then step reaches into a private field, a mock's call count, or an
internal database table directly, and the test breaks on every refactor even
when the externally observable behavior has not changed. Cause. The team
treated Given-When-Then as a structural label without applying the underlying
discipline that Then should check what a caller can observe. Fix. Rewrite the
assertion against the public return value, the response body, or a published
event, per the Gherkin reference's guidance that an outcome "should be on an
observable output."

**Step definition explosion and duplicate steps.** Symptom. Two step
definitions with near-identical regex patterns both match slightly different
wordings of "the same" precondition, and the team cannot tell which one a
new scenario will actually invoke, or the build fails with an ambiguous-match
error. Cause. No ownership or review process for the shared step library as
the suite grew. Fix. Establish a single canonical phrasing per business
concept, search the existing step library before adding a new step, and
periodically consolidate near-duplicates.

**Given block silently performing the action under test.** Symptom. A test
passes even when the code path exercised by When is broken, because the
Given block already produced the state the Then clause checks. Cause. Setup
code accidentally duplicates the behavior the When section exists to verify,
often introduced when a fixture helper is reused carelessly across scenarios.
Fix. Audit any Given that calls the same method the When section calls, and
separate fixture construction from the operation under test.

**Treating a data-validation matrix as narrative scenarios.** Symptom. Twelve
nearly identical Given-When-Then scenarios exist, differing only in one input
string, producing hundreds of lines of feature-file boilerplate for what is
really a twelve-row input table. Cause. The team defaulted to one scenario
per case instead of using a scenario outline with an example table, or a
parameterized test in the non-Gherkin variant. Fix. Collapse into a single
scenario outline (Gherkin) or a table-driven test (bare xUnit style), see
dimension 4.

**Silent skip masquerading as a Then failure.** Symptom. A CI report shows a
scenario failing on its Then step, but the real fault was an exception thrown
during Given, and the runner marked every step after the failure as skipped
rather than failed, so the reported failure line does not name the actual
cause. Cause. Misreading a Cucumber-family runner's step-level pass/fail/skip
report as if only the first reported red line matters. Fix. Always read the
full per-step trace for a failing scenario, not only the summary line.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Given-When-Then (Gherkin) | Bare Arrange-Act-Assert | Table-driven / parameterized test | Property-based test | Page Object plus assertions only |
|---|---|---|---|---|---|
| Readable by a non-programmer | Strong. Plain-text feature files | Poor. Requires reading code | Poor. A data table with no narrative | Poor. Requires reading a property definition | Poor. No narrative layer at all |
| Setup cost / infrastructure | High. Runner, step matching, glue layer | Low. No extra dependency | Low. Native to the test framework | Medium. A generator library | Medium. A page abstraction layer per screen |
| Enforces single action per test | Encouraged by convention, not enforced | Encouraged by convention, not enforced | Not applicable, one row per input | Not applicable, applies to all generated inputs | Not applicable |
| Good fit for pure single-input functions | Poor, adds ceremony | Fair | Strong. Designed for exactly this | Strong when a true invariant exists | Not applicable |
| Good fit for multi-step business workflows | Fair with scenario outlines, poor with one giant When | Fair | Poor | Poor | Strong when combined with a GWT-shaped test |
| Living documentation value | Strong. Broken scenario fails the build | Weak. Reads as code only | Weak | Weak | Weak |
| CI runtime overhead at high test-case volume | Higher, parsing plus regex matching per scenario | Lowest | Low | Medium, generation and shrinking cost | Medium, driver overhead |
| Risk of step-definition drift from stated intent | Real and requires active maintenance | Not applicable, no separate text layer | Not applicable | Not applicable | Not applicable |

Reading of the table. Gherkin-style Given-When-Then earns its infrastructure
cost specifically where a non-technical reader must review the specification
or where living documentation is a genuine organizational goal. Bare
Arrange-Act-Assert gets the same single-responsibility discipline at a
fraction of the setup cost when no such reader exists. Table-driven and
property-based tests are the right tool when the thing varying across cases
is a value, not a narrative. A Page Object is orthogonal, it structures how a
When step drives a UI, and composes cleanly underneath any of the other rows.

## 13. Related and incompatible patterns

- **Four-Phase Test.** The direct ancestor in the xUnit tradition, setup,
  exercise, verify, teardown. Given-When-Then is, in Fowler's own words, "a
  reformulation" of it, dropping the explicit teardown phase (handled by
  framework-level fixtures in most modern runners) and adding narrative
  labels aimed at a non-technical reader.
- **Arrange-Act-Assert.** The same three-part shape under Bill Wake's
  alternative naming, aimed at a programmer audience rather than a business
  audience. The two are interchangeable in structure, choosing between them
  is a naming and audience decision, not a structural one.
- **Test Double (mock, stub, fake, spy).** Composes directly underneath
  Given. A Given clause frequently constructs or configures a test double to
  put a collaborator into the needed state before the When section runs.
- **Builder.** Composes underneath Given, and increasingly underneath Then.
  A test-data builder constructs the fixture object graph a Given clause
  needs without exposing every constructor argument at the call site, which
  keeps Given readable, see the Builder entry.
- **Page Object.** Composes underneath When and Then in UI-level acceptance
  tests. The Page Object encapsulates how to drive and inspect a screen, the
  Given-When-Then scenario stays at the business-narrative level and never
  names a CSS selector directly.
- **Scenario Outline / Example Table.** An extension inside the Gherkin
  family, not a separate pattern, that resolves the data-validation-matrix
  non-applicability case named in dimension 4 by attaching a table of
  example rows to a single Given-When-Then narrative.
- **Property-based testing.** Related by generalisation. A property-based
  test can be read as a Given-When-Then whose Given is a generator rather
  than one fixture and whose Then is a universally quantified invariant
  rather than one expected value, see dimension 8.
- **Specification by Example / Executable Specification.** The broader
  discipline Given-When-Then serves. The pattern is the syntactic vehicle,
  Specification by Example is the practice of deriving the scenarios from
  concrete, agreed examples with a domain expert before any code exists.
- **Mystery Guest and Eager Test, from the xUnit Test Patterns catalog of
  test smells.** Conflicts in practice, not in principle. A Given clause that
  silently depends on shared external fixture data (a Mystery Guest) or a
  scenario whose Given performs far more setup than the behavior under test
  needs (an Eager Test) both undermine the readability the pattern exists to
  provide, even though nothing about Given-When-Then itself causes either
  smell.

## 14. Refactoring path in and out

Introducing the pattern into a test suite that has none.

1. Pick one existing test with an unclear or undifferentiated body and
   identify, by reading it line by line, which statements build state,
   which single statement performs the action under test, and which
   statements check the result.
2. Insert blank lines or comments marking Given, When, Then around those
   three groups, without changing any code yet. This alone often reveals
   that the test performs more than one action, which is worth noticing
   before proceeding.
3. If more than one action exists, decide whether the test is really testing
   one behavior with incidental extra calls (move the extra calls into
   Given) or genuinely testing multiple behaviors (split into multiple
   tests, each with exactly one When).
4. Extract repeated Given setup into a shared builder or fixture helper only
   once the same setup literally repeats across two or more tests, extracting
   before that point produces an abstraction with only one caller.
5. If a non-technical reader needs to review the suite, migrate the clearest,
   highest-value scenarios into a Gherkin feature file and wire step
   definitions that call the exact same production code path the bare test
   already called, rather than re-implementing the behavior a second time.
6. Establish a naming convention or lint rule (a code-review checklist item
   is sufficient at small scale) so future tests are written in the same
   shape from the start, closing the loop so the discipline does not erode.

Removing the pattern, or removing the Gherkin layer specifically, when it
stops earning its place. Signals include a feature-file suite nobody outside
engineering reads or reviews, step definitions that have accumulated
duplicate near-matches nobody has time to consolidate, or a table-driven case
disguised as ten near-identical scenarios.

1. Confirm no non-technical reader currently reviews or authors
   scenarios in the feature files, check version control history for authors
   outside the engineering team as one signal.
2. For each feature file, note whether its scenarios vary a single input
   value (a candidate for a table-driven test) or whether they need genuine
   narrative structure (a candidate to keep, converted to a bare
   Given-When-Then unit test instead of a Gherkin scenario).
3. Port the step definitions' logic directly into ordinary test method
   bodies, preserving the Given, When, Then comment structure so the
   single-responsibility discipline is not lost in the migration.
4. Delete the feature files and the Cucumber-family dependency once every
   scenario has an equivalent bare test and the suite passes.
5. Keep the naming convention. What is removed is the text-parsing and
   step-matching infrastructure, not the three-part discipline itself, which
   remains valuable independent of whether a Gherkin runner is present.

## 15. Testing and verification

This dimension is about testing code that is itself structured as
Given-When-Then, and about verifying the pattern is applied well, which is
partly a matter of practice rather than a fact any single source states.

Easier because of the pattern.

- A reviewer can check a pull request's new tests for the single-action rule
  mechanically. Does exactly one call into the system under test appear
  between the Given block and the Then block. A test failing this check is
  immediately identifiable as testing more than one behavior.
- Because the Then section is meant to assert only on observable output, a
  test written correctly in this style tends to survive internal refactors
  that do not change externally visible behavior, which is a direct
  consequence of the discipline the Gherkin reference states for the Then
  keyword.
- In the Gherkin form, a domain expert can literally execute the review by
  reading the feature file and confirming each scenario's Given, When, Then
  matches the agreed business example, without needing a code walkthrough.

Harder because of the pattern.

- The Gherkin form adds a genuine testing target of its own. The step
  definitions need coverage confirming that "Given a logged-in customer"
  really does construct a valid, authenticated customer as the domain model
  evolves, because nothing in the feature file itself verifies that the step
  definition still does what its text claims.
- Debugging a failing scenario in the Gherkin form requires understanding two
  layers, the feature file and the matched step definition, rather than one
  contiguous method body, which slows down root-causing a failure compared to
  a bare xUnit-style test.

Techniques that apply.

- **Step-definition contract test.** Where a step is reused across many
  scenarios, write one focused unit test directly against the step
  definition's code confirming it produces the state or performs the action
  it claims, independent of any feature file.
- **Mutation testing on the code under test, run against the GWT suite.**
  Because Then assertions in a well-formed scenario check observable output,
  a mutation-testing run is a strong signal of whether the suite's assertions
  are meaningful or vacuous. A scenario whose Then never fails under any
  mutation of the code it claims to cover has an assertion problem, not a
  structure problem.
- **Ambiguous-step detection.** Most Cucumber-family runners can be run with
  a dry-run or strict mode that fails the build on an ambiguous step match,
  which is the mechanical defence against the duplicate-step failure mode in
  dimension 11.
- **Golden-file review of feature files in code review.** Because feature
  files are plain text, a diff of a `.feature` file in a pull request is
  itself a readable artifact a non-technical reviewer can approve, which is a
  verification technique unique to the Gherkin variant of the pattern.

## 16. Observability signals

Given-When-Then is a test-authoring pattern, so its observability surface is
almost entirely about the CI pipeline and the test report, not a running
production system, and this dimension is largely engineering judgement about
what a healthy suite looks like on a dashboard rather than a sourced claim.

What to record.

- Per-scenario pass, fail, and skip counts from each CI run, broken out by
  feature file in the Gherkin variant, so a spike in skipped scenarios (which
  usually means a Given step is throwing before the Then assertion runs, see
  dimension 7) is visible without reading individual logs.
- Step-definition match time and total scenario execution time, so a
  regression in the parsing and matching layer itself, distinct from a
  regression in the system under test, is separately visible.
- A count of ambiguous-step warnings or errors from a strict-mode CI run,
  tracked over time as a proxy for step-library health.
- For long-running acceptance suites, per-scenario duration outliers, since
  Given-When-Then scenarios at the acceptance-test layer often drive an
  external dependency (a browser, a real HTTP call) whose latency is the
  largest share of a scenario's total run time.

A healthy suite on a dashboard. Skipped-scenario count stays near zero and
only moves when a genuine upstream dependency is intentionally excluded.
Ambiguous-step warnings stay at zero, because any nonzero count means the
step library already has an unresolved duplicate. Per-scenario duration is
stable release over release, with outliers investigated rather than
tolerated, since a slow scenario in a suite meant to be reviewed by
non-technical readers undermines the fast-feedback goal BDD suites are
built for.

A failing suite. Skipped-scenario count climbs steadily, which usually means
a shared Given step started throwing and nobody has traced it because the
reported failure line points at a Then step further down the scenario, see
the silent-skip failure mode in dimension 11. Or step-definition match time
grows disproportionately to scenario count, which usually means the step
library has accumulated overlapping regex patterns that the matcher must
disambiguate on every run.

## 17. Security and privacy implications

The pattern is close to silent on security in the narrow sense that
Given-When-Then names a test structure, not a runtime component, and it has
no attack surface of its own once the build completes. Judgement, not a
sourced claim. The implications that matter in practice come from what teams
commonly put into feature files and step definitions.

**Secrets and credentials embedded in Given clauses.** Because Gherkin
feature files are plain text checked into version control and often read by
people outside the immediate engineering team for review purposes, a Given
step written as "given a customer with API key sk-live-..." leaks a real
credential into a widely readable artifact. Given clauses that need
credentials should reference a named fixture or environment variable, never
a literal secret value, the same discipline any source-controlled file needs.

**Personal data in example scenarios.** Because scenarios are meant to be
concrete and readable, authors are tempted to copy a real customer record
into a Given clause to make the example feel authentic. That is personal
data checked into the repository's history, which most data-protection
regimes treat the same as personal data in any other source file. Use
synthetic example data, never a copied production record, in any Given
clause or example table.

**Step-definition privilege escalation in shared CI.** Where step
definitions run with broad-access credentials to reach a shared test
environment (a staging database, a cloud test account), and feature files
are editable by a wide contributor base including external reviewers on an
open-source project, a maliciously worded scenario could be crafted to
match an overly permissive step definition and trigger an unintended action
against that shared environment. Treat step definitions with real external
access the same as any other code path with production-adjacent
credentials, and require the same review gate.

On data flow the pattern itself is neutral. It has no bearing on how test
data reaches a system under test beyond making that data visible in plain
text where a code-only test might have kept it inside a compiled fixture
object, which is a mild net increase in exposure surface for whatever data
appears in Given clauses and example tables, worth weighing against the
readability benefit the pattern is chosen for.

## Code examples

Three languages, chosen because Given-When-Then appears idiomatically in each
in a different shape. Java shows the bare xUnit-style variant with narrative
comments, the most common real-world form. TypeScript shows the same bare
form plus a short illustration of the fluent given/when/then chain style used
by libraries such as REST-assured, adapted to a plain in-memory example so it
runs with no external dependency. Python shows the Behave-style Gherkin form,
step definitions plus a feature file, which is the canonical executable-
specification shape the pattern is best known for.

### Java

```java
import java.util.ArrayList;
import java.util.List;

final class ShoppingCart {
    private final List<Integer> itemPricesCents = new ArrayList<>();
    private int discountPercent = 0;

    void addItem(int priceCents) {
        itemPricesCents.add(priceCents);
    }

    void applyDiscount(int percent) {
        discountPercent = percent;
    }

    int totalCents() {
        int subtotal = itemPricesCents.stream().mapToInt(Integer::intValue).sum();
        return subtotal - (subtotal * discountPercent / 100);
    }
}

final class ShoppingCartTest {
    static void testDiscountAppliesToTotal() {
        // Given a cart with two items totalling 2000 cents
        ShoppingCart cart = new ShoppingCart();
        cart.addItem(1200);
        cart.addItem(800);

        // When a 10 percent discount is applied
        cart.applyDiscount(10);

        // Then the total reflects the discount
        int total = cart.totalCents();
        if (total != 1800) {
            throw new AssertionError("expected 1800, got " + total);
        }
    }

    public static void main(String[] args) {
        testDiscountAppliesToTotal();
        System.out.println("PASS");
    }
}
```

### TypeScript

Bare form first.

```typescript
class ShoppingCart {
  private itemPricesCents: number[] = [];
  private discountPercent = 0;

  addItem(priceCents: number): void {
    this.itemPricesCents.push(priceCents);
  }

  applyDiscount(percent: number): void {
    this.discountPercent = percent;
  }

  totalCents(): number {
    const subtotal = this.itemPricesCents.reduce((a, b) => a + b, 0);
    return subtotal - Math.floor((subtotal * this.discountPercent) / 100);
  }
}

function testDiscountAppliesToTotal(): void {
  // Given a cart with two items totalling 2000 cents
  const cart = new ShoppingCart();
  cart.addItem(1200);
  cart.addItem(800);

  // When a 10 percent discount is applied
  cart.applyDiscount(10);

  // Then the total reflects the discount
  const total = cart.totalCents();
  if (total !== 1800) {
    throw new Error(`expected 1800, got ${total}`);
  }
}

testDiscountAppliesToTotal();
console.log("PASS");
```

Fluent given/when/then chain style, the shape REST-assured popularised for
Java HTTP tests, adapted here to a plain synchronous example with no network
dependency.

```typescript
class GivenWhenThen<T> {
  private state: T;
  constructor(initial: T) {
    this.state = initial;
  }
  when(action: (state: T) => T): GivenWhenThen<T> {
    this.state = action(this.state);
    return this;
  }
  then(assertion: (state: T) => void): void {
    assertion(this.state);
  }
}

function given<T>(initial: T): GivenWhenThen<T> {
  return new GivenWhenThen(initial);
}

given({ items: [1200, 800], discountPercent: 0 })
  .when((cart) => ({ ...cart, discountPercent: 10 }))
  .then((cart) => {
    const subtotal = cart.items.reduce((a, b) => a + b, 0);
    const total = subtotal - Math.floor((subtotal * cart.discountPercent) / 100);
    if (total !== 1800) throw new Error(`expected 1800, got ${total}`);
    console.log("PASS (fluent chain)");
  });
```

### Python

The Gherkin form. A feature file and its matching Behave step definitions,
the canonical executable-specification shape.

```gherkin
Feature: Shopping cart discount

  Scenario: Applying a percentage discount to a cart
    Given a cart with items priced 1200 and 800 cents
    When a 10 percent discount is applied
    Then the total is 1800 cents
```

```python
from behave import given, when, then


class ShoppingCart:
    def __init__(self):
        self.item_prices_cents: list[int] = []
        self.discount_percent = 0

    def add_item(self, price_cents: int) -> None:
        self.item_prices_cents.append(price_cents)

    def apply_discount(self, percent: int) -> None:
        self.discount_percent = percent

    def total_cents(self) -> int:
        subtotal = sum(self.item_prices_cents)
        return subtotal - (subtotal * self.discount_percent // 100)


@given("a cart with items priced {price_a:d} and {price_b:d} cents")
def step_impl(context, price_a: int, price_b: int) -> None:
    context.cart = ShoppingCart()
    context.cart.add_item(price_a)
    context.cart.add_item(price_b)


@when("a {percent:d} percent discount is applied")
def step_impl(context, percent: int) -> None:
    context.cart.apply_discount(percent)


@then("the total is {expected:d} cents")
def step_impl(context, expected: int) -> None:
    actual = context.cart.total_cents()
    assert actual == expected, f"expected {expected}, got {actual}"
```

The same scenario expressed as a bare unittest-style test with no Gherkin
runner, the form most Python codebases actually run day to day.

```python
class ShoppingCart:
    def __init__(self):
        self.item_prices_cents: list[int] = []
        self.discount_percent = 0

    def add_item(self, price_cents: int) -> None:
        self.item_prices_cents.append(price_cents)

    def apply_discount(self, percent: int) -> None:
        self.discount_percent = percent

    def total_cents(self) -> int:
        subtotal = sum(self.item_prices_cents)
        return subtotal - (subtotal * self.discount_percent // 100)


def test_discount_applies_to_total() -> None:
    # Given a cart with two items totalling 2000 cents
    cart = ShoppingCart()
    cart.add_item(1200)
    cart.add_item(800)

    # When a 10 percent discount is applied
    cart.apply_discount(10)

    # Then the total reflects the discount
    total = cart.total_cents()
    assert total == 1800, f"expected 1800, got {total}"


if __name__ == "__main__":
    test_discount_applies_to_total()
    print("PASS")
```

## 18. References

1. Martin Fowler. "GivenWhenThen." martinfowler.com bliki.
   https://martinfowler.com/bliki/GivenWhenThen.html
   Verified 2026-08-02. Source for the attribution to Daniel Terhorst-North
   and Chris Matts, the Four-Phase Test and Arrange-Act-Assert relationship,
   and the definition of the three sections quoted in dimension 1 and
   dimension 5.
2. Cucumber Ltd. "Gherkin Reference." cucumber.io documentation.
   https://cucumber.io/docs/gherkin/reference/
   Verified 2026-08-02. Source for the Given/When/Then/And/But contract, the
   "observable output" guidance for Then, and the ambiguous-duplicate-step
   behavior described in dimensions 1, 5, and 11.
3. SpecFlow / Reqnroll project. Documentation.
   https://docs.reqnroll.net/latest/
   Verified 2026-08-02. Source for the .NET port of Given/When/Then step
   attributes cited as a production use in dimension 9.
4. Behave project. Documentation.
   https://behave.readthedocs.io/en/latest/
   Verified 2026-08-02. Source for the Python Gherkin runner cited as a
   production use in dimension 9, and the basis for the Python code example.
5. REST-assured project. Documentation and usage guide.
   https://rest-assured.io/
   Verified 2026-08-02. Source for the fluent given/when/then chain style
   cited in dimensions 8 and 9, and the basis for the TypeScript fluent
   example's shape.
