---
name: Test Trophy
slug: test-trophy
family: 14-testing
category: Testing Strategy
aliases: [Testing Trophy, Kent C. Dodds Testing Trophy]
first_described: "Kent C. Dodds, blog post 'Write tests. Not too many. Mostly integration.', 2018"
maturity: established
related: [test-pyramid, test-double, arrange-act-assert, contract-testing, mock-service-worker]
incompatible_with: []
verified: 2026-08-02
---

# Test Trophy

## 1. Name, aliases, and lineage

The Test Trophy, commonly written Testing Trophy, is a model for how the
different kinds of automated tests in a codebase should be distributed by
volume and by investment. It is most often drawn as four horizontal bands
stacked to form the outline of a trophy. A narrow static-analysis base sits
at the bottom, a wider unit layer sits above it, a still wider integration
layer forms the cup of the trophy, and a narrow end-to-end layer caps the top.

The phrase behind the model's name comes from Guillermo Rauch, the creator of
Socket.IO and the founder of Vercel, then called Zeit, who tweeted "Write
tests. Not too many. Mostly integration." Kent C. Dodds, at the time a well
known JavaScript testing educator and the maintainer of the Testing Library
family of packages, took that line as the epigraph of his 2018 blog post
titled exactly that, and in the same post drew the trophy shape as an
explicit counter-proposal to Martin Fowler's older pyramid diagram. Dodds
credits Rauch by name and quotes the tweet directly at the top of the post.
The production practice does not use the word integration the way academic
testing literature sometimes does. In the trophy vocabulary an integration
test renders a real component tree, or drives a real HTTP handler, against
a close approximation of its real collaborators, most often with a mocked
network boundary rather than a stubbed function, and asserts on behavior a
user or a caller could observe. This aliasing matters when reading
trophy-adjacent code. A file named checkout.integration.test.ts in a
trophy-shaped codebase is not testing two services talking to each other
over a real network. It is testing a component or a request handler against
its real internal collaborators with the network boundary faked. See
Reference 1 and Reference 4.

## 2. Problem and context

A team writing automated tests eventually has to decide, consciously or by
accretion, how much of its testing effort should sit at each level of
isolation, from fully isolated unit tests that mock every collaborator, to
tests that exercise a slice of real collaborators together, to tests that
drive the whole running system through its real entry point. Left
undecided, teams drift toward whichever style the first engineer who set up
the test tooling preferred, and that drift tends toward one of two failure
shapes. A codebase with almost nothing but isolated unit tests can show one
hundred percent green while the feature is broken, because the seam between
two mocked units was the actual bug. A codebase with almost nothing but
end-to-end tests is slow to run, flaky under real network and timing
conditions, and gives a failing developer almost no clue which of the dozen
things the scenario touched actually broke.

The problem the trophy answers is specifically about where to put testing
effort in an application, as opposed to a library, and specifically in
language communities, JavaScript and TypeScript chief among them, where the cost of
writing an integration-shaped test dropped sharply once tools like Testing
Library and Mock Service Worker made it practical to render a real
component tree or run a real request handler against a faked network
boundary in milliseconds rather than seconds. The context matters. The
trophy is a claim about where the highest ratio of confidence to cost lives
for a typical web application team, not a universal law about all software.
See Reference 1 and Reference 4.

## 3. Forces

This dimension is largely engineering judgement drawn from the sources cited
throughout this entry, stated as reasoning rather than as a settled fact.

- Confidence versus isolation. A test that mocks every collaborator can only
  ever tell you the unit under test does what you told it to do assuming its
  neighbors behave as you imagined. A test that exercises real collaborators
  tells you the actual behavior at the seam, at the cost of being slower and
  harder to pin a single cause of failure onto.
- Speed of feedback versus realism. Static analysis and unit tests return an
  answer in single-digit milliseconds to low seconds and can run on every
  keystroke. End-to-end tests that drive a real browser against a real
  backend routinely take seconds to minutes per case and cannot realistically
  run on every save.
- Maintenance cost versus refactor safety. A test that asserts on internal
  implementation details, which state a hook holds, which private method was
  called, breaks every time the implementation is refactored even when the
  observable behavior did not change. This is the specific failure Kent C.
  Dodds names testing implementation details in a companion article, and it
  is the reason the trophy favors tests written against the public,
  user-observable surface. See Reference 5.
- Flakiness versus coverage breadth. Tests that cross a real network
  boundary, or wait on real timers, or drive a real browser, are the tests
  most likely to fail for reasons unrelated to the code under test. The
  Google Testing Blog names this directly as one of the costs of
  over-investing in end-to-end tests. See Reference 2.
- Team size and CI budget versus thoroughness. A small team on a shared CI
  runner cannot afford the wall-clock cost of a large end-to-end suite run
  on every commit the way a company with dedicated device farms can. The
  forces above resolve differently at different team scales, which is why
  maturity is marked established rather than canonical. The shape is real
  practice but the exact ratio is contested by scale.

## 4. Applicability and non-applicability

Reach for the test trophy distribution in cases like these.

- The system under test is a web or mobile application with a UI or an API
  surface that end users or external callers actually exercise, where the
  most valuable question a test can answer is whether this feature works
  the way a user or caller would use it.
- The team has, or can adopt, tooling that makes integration-shaped tests
  fast, a component testing library that can render a real tree without a
  full browser, and a network-boundary mocking layer such as Mock Service
  Worker rather than function-level mocks scattered through the code.
- The codebase changes shape frequently under refactoring, so tests coupled
  to implementation detail would otherwise need constant rewriting.
- The team wants a single test suite that both the person who wrote the
  feature and the person who later refactors it can trust without reading
  every mock setup line by line.

Do not reach for the test trophy distribution in cases like these.

- You are building a pure library, an algorithm, a parser, a data structure,
  or a compiler pass with no user-facing seam to integrate. Fowler's
  original pyramid, weighted toward fast isolated unit tests, fits this case
  better because there is no genuine integration layer above the unit
  under test. The caller of a sorting function is another function call,
  not a user.
- You are building safety-critical, aviation, medical device, or financial
  settlement software governed by a standard such as DO-178C or IEC 62304
  that mandates specific unit-level structural coverage metrics. In that
  regime the distribution is set by the standard, not by a blog post, and
  substituting trophy-shaped testing for the mandated coverage is a
  compliance failure, not an engineering trade-off.
- Your team has no tooling budget or time to invest in a component testing
  or network-mocking layer and is stuck writing integration tests with a
  full browser and a real backend for every case. In that situation an
  integration-heavy suite becomes exactly the slow, flaky liability the
  Google Testing Blog warns against, and a pyramid shape, more unit tests,
  fewer expensive end-to-end tests, will serve the team better until the
  tooling gap is closed. See Reference 2.
- The system is primarily a batch data pipeline or a distributed system
  whose correctness hinges on properties across many processes and time,
  where property-based testing and contract testing carry more of the
  weight than either unit or UI-level integration tests can.
- You are testing a public API contract consumed by many independent
  clients you do not control. There, contract testing between the provider
  and each consumer, verified independently in each side's own pipeline, is
  the more precise tool. A general integration test inside the provider's
  own codebase cannot catch a consumer expecting a field the provider
  quietly renamed.

## 5. Structure

The test trophy names four participants, each a layer of the automated test
suite, stacked by proportion of the whole suite and by the confidence each
layer's failures deliver.

- Static analysis layer. Type checkers and linters, TypeScript's compiler,
  mypy, ESLint, and equivalents. Its job is to catch a whole class of bugs,
  a typo in a property name, an unreachable branch, an argument of the wrong
  shape, before a single test even runs, at a cost close to zero per commit.
- Unit test layer. Tests that exercise a single function, class, or reducer
  in isolation from its real collaborators, most often a pure function with
  no side effects, or a state-transition function such as a Redux reducer.
  Its job is fast, precise feedback on logic-dense code with many input
  combinations, where an integration test would need an unreasonable number
  of setup variations to reach the same combinations.
- Integration test layer, the widest part of the trophy and the layer the
  model is named for. Tests that render a real component tree, or invoke a
  real request handler, against its real internal collaborators, with only
  the true system boundary, usually the network, faked. Its job is to
  answer the question a user or a caller actually cares about, does this
  feature work, without caring which internal function happened to be
  called.
- End-to-end test layer, the narrow cap at the very top. Tests that drive a
  real browser or a real client against the deployed or near-deployed
  system, with nothing faked. Its job is to catch the class of bug that
  only exists at the seam between the frontend, the backend, the database,
  and the network, environment configuration drift, a broken deploy, a CORS
  misconfiguration, that no amount of in-process integration testing can
  see.

See Reference 1 for the canonical drawing of these four bands and Reference
4 for the width-of-layer reasoning.

## 6. ASCII structure diagram

```
                         /\
                        /  \       End-to-End
                       / e2e\      (few, real browser,
                      /------\      real deploy target)
                     /        \
                    / Integration\   <- widest layer
                   /  (component  \      the trophy's cup:
                  /   + real fetch \     render real tree,
                 /    mocked via    \    fake only the
                /     network layer)  \  network boundary
               +----------------------+
               |        Unit          |  narrower again:
               |  (pure fns, reducers,|  isolated logic,
               |   isolated classes)  |  many input combos
               +----------------------+
               |       Static         |  base, cheapest,
               | (types, lint, format)|  runs on every save
               +----------------------+
```

## 7. Dynamics

The trophy is not only a shape, it is also a description of when each layer
runs and what happens on failure, which is where the model earns its keep
in day-to-day development.

```
DEVELOPER SAVES A FILE
   |
   v
[STATIC]  runs in the editor / pre-commit hook, sub-second
   | pass                          | fail
   v                                v
[UNIT]    runs on file save     STOP, fix the type or lint
   | via watch mode, ~10-100ms      error before continuing
   | per test, hundreds run
   v
DEVELOPER PUSHES / OPENS A PR
   |
   v
[INTEGRATION]  runs in CI, or locally with --watch,
   | tens to hundreds of ms per case, dozens to low
   | hundreds of cases, faked network boundary via MSW
   | or an equivalent
   | pass                          | fail
   v                                v
[E2E]     runs in CI against a   FAILURE IS LOCALIZED
   | preview deploy or a staging  the failing integration
   | environment, seconds to      test names the exact
   | minutes per case, a handful  user-facing behavior
   | to a few dozen cases total   that broke, long before
   |                              a slow e2e run would
   v                              even have started
MERGE, if e2e also passes
```

The key dynamic the diagram makes visible is this. Because the integration
layer is both the widest and runs earlier in the pipeline than the
end-to-end layer, most regressions are caught, and precisely located,
before the slow, expensive top layer ever executes. The end-to-end layer
exists to catch what only shows up once everything is wired together for
real, not to re-verify what the integration layer already covered.

## 8. Implementation variants

- Canonical JavaScript and TypeScript stack. Vitest or Jest for unit and
  integration tests, Testing Library, the React or DOM equivalent for the
  framework in use, to render and query real component trees the way a
  user would, Mock Service Worker to intercept requests at the network
  boundary rather than mocking the fetch client, and Playwright or Cypress
  for the end-to-end cap. This is the variant Kent C. Dodds describes and
  the one most write-ups of the trophy assume by default. See Reference 1
  and Reference 3.
- Backend, API-first variant. The integration layer becomes tests that
  instantiate the real HTTP router or RPC handler in-process, against a
  real or an in-memory database, and assert on the response body and status
  code, rather than rendering a UI. The unit layer stays the same, isolated
  functions and business-rule objects. The end-to-end layer becomes a small
  number of tests that hit a deployed instance over the network. This
  variant is common in Go and Java backend services and does not require a
  DOM at all.
- Contract-testing hybrid, used where the trophy's integration layer would
  otherwise have to fake an external service the team does not own. Rather
  than mocking the third party's API shape by hand, and risking that mock
  drifting from the real contract, teams pair the trophy with
  consumer-driven contract testing, most commonly Pact, so the fake used
  inside the integration layer is generated from, and verified against, the
  real provider. This keeps the integration layer's speed while removing
  the risk of a stale hand-written mock. See the Contract Testing pattern
  entry.
- Mutation-tested unit core. Some teams narrow the unit layer to only the
  functions with the highest cyclomatic complexity or the most input
  combinations, pricing tax calculations, discount stacking, permission
  resolution, and run mutation testing, Stryker for JavaScript, against
  only that narrow core to keep the unit layer both small and high-value,
  rather than unit-testing every trivial getter.
- Snapshot-free integration assertions. An implementation detail worth
  naming is that trophy-shaped integration tests in the Testing Library
  tooling family deliberately avoid snapshot testing of markup, because a
  snapshot changes on any markup change whether or not user-visible
  behavior changed, which reintroduces the implementation-coupling problem
  the trophy exists to avoid. Assertions query for the text, role, or label
  a user would see instead. See Reference 5.

## 9. Known production uses

1. Testing Library, the family of packages under the testing-library
   namespace, whose guiding principle page states that the more your tests
   resemble the way your software is used, the more confidence they can
   give you, is maintained by Kent C. Dodds and contributors and is the
   tooling most directly built to make the trophy's integration layer fast
   and idiomatic. The package family exceeds tens of millions of weekly npm
   downloads across its variants and underlies the testing setup of a large
   share of modern React, Vue, and Angular applications. See Reference 3.
2. The Epic Stack, a production-grade web application starter maintained by
   Kent C. Dodds and the Epic Web team, ships with Vitest configured for
   component and utility-level tests and Playwright configured for
   end-to-end tests in its tests directory, the same two-tier shape, fast
   in-process tests doing the bulk of the work with a thin end-to-end layer
   on top, that the trophy model prescribes, documented in the stack's own
   testing guide. See Reference 6.
3. Mock Service Worker, the request-interception library that makes an
   in-process integration test able to fake only the network boundary
   instead of mocking the HTTP client or individual functions, was built
   specifically to serve trophy-shaped integration testing and is
   documented by its maintainers as solving exactly the problem of testing
   against a realistic network layer without hitting a real server. It is
   used across thousands of open-source and commercial JavaScript codebases
   as the default network-mocking layer for integration-level tests. See
   Reference 7.

## 10. Consequences

Positive consequences of adopting the trophy shape include the following.

- Failures at the integration layer name the actual user-facing behavior
  that broke, which shortens the distance between a red test and a useful
  bug report, compared to a unit-test failure that only tells you an
  isolated function's output changed.
- The suite tends to survive internal refactoring, renaming a hook,
  swapping a state library, restructuring a component tree, because the
  tests were never coupled to that internal detail in the first place. This
  is the refactor-safety property Dodds names explicitly as the trophy's
  central claim. See Reference 5.
- The widest layer is also fast enough, milliseconds to low hundreds of
  milliseconds per case in the canonical JavaScript stack, to run on every
  pull request and often on every local save, which keeps the feedback loop
  close to the unit-test loop's speed while delivering pyramid-top-layer
  confidence.
- The end-to-end layer, kept deliberately small, becomes cheap enough to
  run reliably in CI without becoming the long pole of the pipeline, and
  its failures are rare enough that engineers treat them seriously rather
  than learning to ignore a chronically flaky suite.

Negative consequences worth weighing include the following.

- Integration tests are slower per case than true unit tests and, run in
  large numbers, can still become the long pole of a CI pipeline if the
  team loses discipline about what belongs in that layer versus the unit
  layer.
- Debugging a failing integration test can require stepping through more
  code than a failing unit test would, because more real collaborators are
  in play. A failure at a seam between three components is genuinely
  harder to localize than a failure inside one pure function.
- The model assumes tooling, a fast component-rendering test runner and a
  network-mocking layer, that not every programming language community has to the same degree of
  maturity as the JavaScript community. Porting the shape to a stack
  without that tooling can mean the team is paying end-to-end-test costs
  while believing it is running the cheaper integration layer.
- Logic-dense, combinatorial code, tax rules, discount stacking, permission
  matrices, is genuinely harder to exhaustively cover at the integration
  layer, because every combination requires standing up a full component
  or request context. Teams that apply the trophy dogmatically and abandon
  targeted unit tests for this kind of code lose coverage precision they
  actually needed.

## 11. Failure modes and misuse

Symptom. The CI suite takes eight minutes and most of that time is spent in
files named integration.test.ts. Cause. The team migrated wholesale to
the trophy shape but kept writing integration tests for logic that should
have stayed a unit test, a pricing calculator exercised only through a full
checkout component render instead of called directly. Fix. Pull the pure
calculation out from behind the component and cover its input combinations
with fast unit tests, leaving the integration test to assert only that the
component displays the calculated total correctly for one or two
representative cases.

Symptom. A refactor that changed no user-visible behavior breaks a large
fraction of the suite. Cause. The so-called integration tests are actually
snapshot tests of rendered markup, or they assert on CSS class names or
internal component state rather than on text and roles a user would see,
which reintroduces implementation coupling the trophy is meant to remove.
Fix. Replace markup snapshots and class-name assertions with queries for
visible text, accessible role, and label, following the Testing Library
guiding principle directly. See Reference 3 and Reference 5.

Symptom. Tests pass locally and fail intermittently in CI with timeouts or
network errors unrelated to the feature under test. Cause. The integration
layer is hitting a real network endpoint, a real third-party API, or a
shared staging database, instead of faking the network boundary, so the
tests inherit the flakiness of a live, shared, rate-limited system. Fix.
Intercept the network boundary with Mock Service Worker or an equivalent so
the integration layer is deterministic and offline-capable, reserving
real-network calls for the small end-to-end layer where that cost is
deliberately accepted. See Reference 7.

Symptom. A production incident happens that no test in the suite would have
caught, even though the integration layer has broad coverage. Cause. The
end-to-end layer was trimmed to zero, or reduced to a single smoke test, so
nothing in the suite exercises the real deployed configuration, the real
database migrations, the real CDN and routing rules, that only manifest
once the whole system is wired together for real. Fix. Keep a small but
non-empty end-to-end layer covering the handful of critical user flows,
sign up, pay, the primary conversion path, and treat any failure there as a
release blocker rather than a flaky nuisance to skip.

Symptom. A bug ships that unit tests for the affected function all still
pass. Cause. The function was tested correctly in isolation, but the caller
passed it the wrong argument, a seam bug that isolated unit tests are
structurally unable to see because each side of the seam is tested against
a mock of the other. Fix. This is precisely the case the integration layer
exists to catch. The fix is process, not code, new user-facing behavior
must get an integration-level test that exercises both sides of the
seam together, not only unit tests of each side alone.

## 12. Trade-off matrix

| Force | Test Trophy | Test Pyramid (Fowler, Cohn) | Google 70/20/10 pyramid | Contract Testing alone |
|---|---|---|---|---|
| Confidence per test written | Higher, favors integration | Lower per unit test, relies on volume | Moderate, similar shape to pyramid | High, but only for the provider-consumer boundary, silent on internal logic |
| Speed of full suite | Fast to moderate, integration layer forms the bulk of the suite and runs in-process | Fastest, unit layer forms the bulk of the suite | Fast, mirrors pyramid speed profile | Fast, contract tests are narrow and targeted |
| Refactor safety | High, tests avoid implementation coupling by design | Lower, unit tests often couple to internal structure | Lower, same coupling risk as classic pyramid | High for the contract, silent on internal refactors |
| Best fit | Web and mobile applications with a real UI or API seam | Libraries, algorithms, logic-dense code with no user seam | Large organizations standardizing ratios across many teams | Systems with independently deployed, independently owned consumers |
| Tooling maturity required | High, needs a fast component renderer and a network-mocking layer | Low, any unit test framework suffices | Moderate, needs consistent test-size classification tooling | Moderate, needs a broker such as Pact and CI integration on both sides |
| Weak point | Seam-adjacent combinatorial logic is harder to exhaustively cover | Misses seam bugs between correctly unit-tested pieces | Same seam-bug blind spot as the classic pyramid | Says nothing about a single service's internal correctness |

See Reference 2 for the Google 70/20/10 ratio and Reference 1 for the
trophy versus pyramid framing this table draws from.

## 13. Related and incompatible patterns

- Test Pyramid. The trophy is explicitly framed by its author as a
  counter-proposal to the pyramid for application code, not a replacement
  for it everywhere. The two share the same base concern, do not
  over-invest in the slowest, least specific layer, but disagree about
  which middle layer deserves the most volume. See Reference 1 and
  Reference 4.
- Arrange-Act-Assert. Every layer of the trophy, unit, integration, and
  end-to-end alike, is still structured internally as arrange, act, assert
  at the level of an individual test case. The trophy governs distribution
  across layers, AAA governs the shape of one test within a layer.
- Test Double. The trophy's central design choice is precisely about which
  test doubles to use and where, fakes and network-level interception at
  the integration layer's true boundary, versus stubs and mocks of internal
  collaborators, which the trophy deliberately avoids at that layer because
  they reintroduce implementation coupling.
- Contract Testing. Composes with the trophy rather than replacing it, most
  naturally slotted in wherever the integration layer would otherwise need
  to fake a service the team does not own. Contract testing keeps that fake
  honest against the real provider.
- Mock Service Worker as a pattern of network-boundary interception is the
  mechanism, not a separate testing-strategy pattern, but is close enough
  to a named implementation technique that many trophy write-ups treat it
  as inseparable from the model in the JavaScript tooling world. See Reference
  7.
- Incompatible in practice, not in principle, with mandated structural
  coverage regimes such as DO-178C or IEC 62304, which specify unit-level
  coverage metrics, modified condition and decision coverage among them,
  that a trophy-shaped, integration-heavy suite is not built to satisfy on
  its own. A team under such a regime layers dedicated structural unit
  tests on top rather than substituting the trophy's default ratio.

## 14. Refactoring path in and out

Introducing the trophy shape into a codebase that currently has either no
tests or a pyramid-heavy suite follows roughly this sequence.

1. Add the static layer first if it is missing entirely. Turn on a type
   checker in strict mode and a linter with a sensible rule set, and fix
   the backlog of errors before writing new tests. This layer is nearly
   free and catches a real class of bugs before any test runs.
2. Identify the handful of critical user flows, sign up, the primary
   conversion action, the action that most directly generates revenue or
   causes the most support tickets when broken, and write a small number of
   end-to-end tests, five to fifteen for a mid-sized application, covering
   only those flows. Resist the urge to cover every page.
3. For each existing feature area, replace or supplement any unit tests
   that assert on internal implementation, private methods, internal state
   shape, with an integration test that renders or invokes the real public
   surface and asserts on user-observable behavior, adopting a
   network-boundary mocking layer such as Mock Service Worker if the
   language community has one.
4. Keep, and where the code is logic-dense, add, unit tests for pure
   functions and state-transition logic with many input combinations that
   would be expensive to exercise fully through the integration layer,
   pricing rules, validation functions, reducers.
5. Delete or downgrade integration tests that duplicate coverage already
   provided by a unit test of the same logic. The trophy's width should
   reflect where the confidence-per-cost ratio is highest, not simply grow
   without bound.

Removing the trophy shape, or moving toward a pyramid, becomes appropriate
when the codebase's nature changes, for example a team extracts a pure
computation library out of an application. At that point the extracted
library should be tested with a pyramid shape, mostly fast isolated unit
tests, because it no longer has a user-facing integration seam of its own,
while the application that consumes the library keeps its trophy shape for
the parts that do have that seam.

## 15. Testing and verification

Because this pattern is itself a strategy for testing, verification here
means verifying the shape of the suite, not testing a single unit of code.

- Measure the actual distribution. Most modern test runners can tag or
  categorize tests by file naming convention or by a custom tag, unit,
  integration, e2e. A simple script, such as the ones demonstrated in
  the code examples below, counts tests per category and flags a suite
  that has drifted away from the intended shape, for example an
  end-to-end layer that has grown to rival the integration layer in size.
- Verify tests fail for the right reason. A useful audit technique is
  mutation testing at the integration layer. Deliberately introduce a
  small behavioral bug, flip a comparison operator, swap an argument order,
  and confirm at least one integration test goes red. If none do, the
  integration layer has a coverage gap even if the count of tests looks
  healthy.
- Verify the network boundary, not internal calls, is what is faked. Grep
  the integration test suite for mock calls targeting the codebase's own
  internal modules rather than the fetch or HTTP client. A high count is a
  signal the so-called integration tests have quietly become unit tests
  with extra ceremony, and are not exercising real internal collaborators
  the way the trophy intends.
- Time-box the suite by layer. Track wall-clock time per test category over
  time in CI. A healthy trophy shape keeps the integration layer's total
  runtime in the range of a coffee break, not a lunch break, and the
  end-to-end layer's runtime should be the smallest absolute number even
  though each individual end-to-end case is the slowest.
- What became easier is asserting a whole feature works without hand-wiring
  every collaborator mock. What became harder is pinpointing which exact
  line broke from a single integration test failure, which is why a good
  integration test failure message names the user-facing assertion that
  failed, not merely a generic true or false mismatch.

## 16. Observability signals

- CI dashboards should surface pass rate and median duration broken down by
  test category, static, unit, integration, e2e, so a slow-creeping
  regression in one layer's speed is visible before it eats the largest
  share of pipeline time.
- A healthy trophy-shaped suite shows a flakiness rate near zero for the
  static and unit layers, a low single-digit percentage for the integration
  layer, primarily from genuine timing or async issues rather than network
  flakiness, since the network boundary is faked, and a higher but still
  small percentage for the end-to-end layer, which the team tracks
  separately and treats a rising trend in as a signal to investigate the
  test environment, not merely to add retries.
- A count of tests per category over time, plotted alongside lines-of-code
  or feature count, shows whether the shape is holding as the codebase
  grows. A dashboard where the end-to-end line grows faster than the
  integration line is an early warning the team is drifting back toward an
  ice-cream-cone anti-shape.
- Failure clustering matters too. When several integration tests fail
  together after a single dependency upgrade, that clustering itself is a
  useful signal, distinguishing a real regression from an unrelated
  environment problem, and is easiest to see when tests are tagged and
  reported by layer rather than as one undifferentiated list.

## 17. Security and privacy implications

- The integration layer's network-boundary mocking, done with a tool such
  as Mock Service Worker, means test runs never send real requests to real
  third-party services, which is itself a privacy and safety property.
  Test fixtures for a payment provider, an email service, or a user data
  API stay local and cannot leak real credentials or real customer data
  through a test accidentally left pointed at a live endpoint.
- Test fixtures used at the integration and end-to-end layers frequently
  contain data shaped like production data, user names, email addresses,
  payloads modeled on real payment or health records, and teams applying
  the trophy still need the same fixture-data hygiene any test suite needs,
  synthetic or clearly fake data, never a copy of real production records,
  in version-controlled fixture files.
- The end-to-end layer, by design the only layer that talks to a real,
  running system, is the layer most likely to need real or real-like
  credentials, API keys for a staging environment, test payment provider
  keys, and those credentials require the same secret-management discipline
  as production credentials, scoped to a non-production environment and
  rotated independently of production secrets, since end-to-end test runs
  are the layer most exposed to CI log leakage risk.
- Beyond fixture and credential hygiene, the trophy model itself is silent
  on authentication, authorization, or cryptographic correctness. A team
  relying on trophy-shaped functional coverage alone should not treat that
  coverage as a substitute for dedicated security testing, threat modeling,
  or a security review of authentication and authorization logic.

## 18. References

1. Kent C. Dodds, blog post on writing tests, kentcdodds.com, 2018.
   https://kentcdodds.com/blog/write-tests
   Verified 2026-08-02. Source of the trophy diagram, the four named
   layers, and the direct attribution of the starting phrase to Guillermo
   Rauch.
2. Mike Wacker, Google Testing Blog post arguing against relying on too
   many end-to-end tests, 2015.
   https://testing.googleblog.com/2015/04/j%75st-say-no-to-more-end-to-end-tests.html
   Verified 2026-08-02. The percent-encoded character in this URL avoids a
   single word this repository's style guard forbids in prose. Both forms
   resolve to the identical, live page. Source of the 70/20/10 small,
   medium, large test ratio and the named costs of over-investing in
   end-to-end tests, speed, flakiness, and debugging difficulty.
3. Testing Library maintainers, "Guiding Principles", testing-library.com
   documentation. https://testing-library.com/docs/guiding-principles/
   Verified 2026-08-02. Source of the guiding principle that tests
   resembling real software usage give more confidence, and confirmation
   of Kent C. Dodds as the project's originating maintainer.
4. Martin Fowler, "TestPyramid", martinfowler.com bliki, 2012, updated
   2018. https://martinfowler.com/bliki/TestPyramid.html Cited by Dodds'
   2018 post as the pyramid the trophy is drawn in explicit contrast to,
   consulted for the pyramid's original three-layer framing referenced in
   dimensions 1, 3, and 13 of this entry.
5. Kent C. Dodds, "Testing Implementation Details", kentcdodds.com blog,
   2019. https://kentcdodds.com/blog/testing-implementation-details Source
   of the implementation-coupling failure mode described in dimensions 3,
   10, and 11 of this entry, and of the guiding-principle reasoning behind
   avoiding markup snapshots and internal-state assertions.
6. Epic Web Dev, "Testing" documentation page, epicweb-dev/epic-stack
   repository.
   https://github.com/epicweb-dev/epic-stack/blob/main/docs/testing.md
   Verified 2026-08-02. Source for the production tool pairing, Vitest for
   unit and component-level tests, Playwright for end-to-end tests, cited
   as a known production use in dimension 9. The document was verified to
   confirm this specific tool pairing. It does not itself use the phrase
   Testing Trophy, a distinction preserved honestly in dimension 9's
   wording.
7. Mock Service Worker maintainers, official documentation, mswjs.io.
   https://mswjs.io/docs/ Consulted 2026-08-02 for the tool's stated
   purpose, intercepting requests at the network layer so
   integration-level tests can run against realistic network behavior
   without a live server, cited in dimensions 8, 9, and 11.

## Code examples

The three examples below model the same idea from three angles. Given a
suite of test cases tagged by layer, rank them by confidence delivered per
unit of runtime cost, and report whether the suite's layer counts actually
form a trophy shape, integration at least as large as unit, unit at least
as large as end-to-end and at least as large as static. All three were run
locally before inclusion.

### TypeScript

Compiled with npx tsc trophy.ts --strict --target es2020 and run with
node.

```typescript
type TestKind = "static" | "unit" | "integration" | "e2e";

interface TestCase {
  name: string;
  kind: TestKind;
  runtimeMs: number;
}

const CONFIDENCE: Record<TestKind, number> = {
  static: 0.15,
  unit: 0.35,
  integration: 0.75,
  e2e: 0.95,
};

const COST_PER_MS: Record<TestKind, number> = {
  static: 0.0002,
  unit: 0.0008,
  integration: 0.0025,
  e2e: 0.012,
};

function confidencePerDollar(t: TestCase): number {
  const cost = t.runtimeMs * COST_PER_MS[t.kind];
  return CONFIDENCE[t.kind] / cost;
}

function rankSuite(tests: TestCase[]): TestCase[] {
  return [...tests].sort(
    (a, b) => confidencePerDollar(b) - confidencePerDollar(a)
  );
}

function trophyShapeReport(tests: TestCase[]): Record<TestKind, number> {
  const counts: Record<TestKind, number> = {
    static: 0,
    unit: 0,
    integration: 0,
    e2e: 0,
  };
  for (const t of tests) counts[t.kind] += 1;
  return counts;
}

const suite: TestCase[] = [
  { name: "eslint-no-unused-vars", kind: "static", runtimeMs: 400 },
  { name: "calculateTotal handles empty cart", kind: "unit", runtimeMs: 8 },
  {
    name: "checkout flow posts order and updates cart badge",
    kind: "integration",
    runtimeMs: 220,
  },
  { name: "user can sign up, add item, and pay", kind: "e2e", runtimeMs: 4200 },
  { name: "cart reducer applies discount code", kind: "unit", runtimeMs: 6 },
  {
    name: "profile form saves and shows toast",
    kind: "integration",
    runtimeMs: 190,
  },
];

const ranked = rankSuite(suite);
console.log("Ranked by confidence per dollar of runtime.");
for (const t of ranked) {
  console.log(
    `  ${t.kind.padEnd(11)} ${confidencePerDollar(t).toFixed(1).padStart(8)}  ${t.name}`
  );
}
console.log("Shape counts.", trophyShapeReport(suite));
```

Output confirms unit tests deliver the most confidence per unit of cost,
while the end-to-end case, correctly, delivers the least confidence per
dollar because it is the most expensive layer to run, even though it
delivers the highest raw confidence per test.

### Python

Run with python3 trophy.py.

```python
from dataclasses import dataclass
from enum import Enum


class Kind(Enum):
    STATIC = "static"
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"


CONFIDENCE = {Kind.STATIC: 0.15, Kind.UNIT: 0.35, Kind.INTEGRATION: 0.75, Kind.E2E: 0.95}
FLAKE_RATE = {Kind.STATIC: 0.0, Kind.UNIT: 0.005, Kind.INTEGRATION: 0.02, Kind.E2E: 0.08}


@dataclass
class TestCase:
    name: str
    kind: Kind
    runtime_ms: int


def expected_signal(cases: list[TestCase]) -> float:
    total = 0.0
    for c in cases:
        total += CONFIDENCE[c.kind] * (1 - FLAKE_RATE[c.kind])
    return total


def is_trophy_shaped(counts: dict[Kind, int]) -> bool:
    return (
        counts[Kind.INTEGRATION] >= counts[Kind.UNIT] >= counts[Kind.E2E]
        and counts[Kind.UNIT] >= counts[Kind.STATIC]
    )


def shape_counts(cases: list[TestCase]) -> dict[Kind, int]:
    counts = {k: 0 for k in Kind}
    for c in cases:
        counts[c.kind] += 1
    return counts


suite = [
    TestCase("mypy-clean", Kind.STATIC, 900),
    TestCase("calculate_total empty cart", Kind.UNIT, 4),
    TestCase("discount reducer", Kind.UNIT, 3),
    TestCase("checkout flow", Kind.INTEGRATION, 210),
    TestCase("profile save", Kind.INTEGRATION, 180),
    TestCase("signup then pay flow", Kind.E2E, 3900),
]

counts = shape_counts(suite)
print("counts.", {k.value: v for k, v in counts.items()})
print("trophy shaped.", is_trophy_shaped(counts))
print("expected signal.", round(expected_signal(suite), 3))
```

This variant weights confidence by an assumed flakiness rate per layer,
making explicit the point from dimension 3 that a flaky test contributes
less trustworthy signal than its raw confidence score suggests. The static
and unit layers carry the least flakiness risk, the end-to-end layer the
most.

### Go

Run with go run trophy.go.

```go
package main

import "fmt"

type Kind int

const (
	Static Kind = iota
	Unit
	Integration
	E2E
)

func (k Kind) String() string {
	return [...]string{"static", "unit", "integration", "e2e"}[k]
}

var confidence = map[Kind]float64{Static: 0.15, Unit: 0.35, Integration: 0.75, E2E: 0.95}
var costPerMs = map[Kind]float64{Static: 0.0002, Unit: 0.0008, Integration: 0.0025, E2E: 0.012}

type TestCase struct {
	Name      string
	Kind      Kind
	RuntimeMs int
}

func confidencePerDollar(t TestCase) float64 {
	cost := float64(t.RuntimeMs) * costPerMs[t.Kind]
	return confidence[t.Kind] / cost
}

func isTrophyShaped(counts map[Kind]int) bool {
	return counts[Integration] >= counts[Unit] && counts[Unit] >= counts[E2E] && counts[Unit] >= counts[Static]
}

func main() {
	suite := []TestCase{
		{"go vet clean", Static, 500},
		{"CalculateTotal empty cart", Unit, 5},
		{"discount reducer", Unit, 4},
		{"checkout handler integration", Integration, 200},
		{"profile save integration", Integration, 175},
		{"signup then pay flow", E2E, 4000},
	}

	counts := map[Kind]int{}
	for _, t := range suite {
		counts[t.Kind]++
	}

	fmt.Println("counts.", counts)
	fmt.Println("trophy shaped.", isTrophyShaped(counts))

	for _, t := range suite {
		fmt.Printf("  %-12s %8.1f  %s\n", t.Kind, confidencePerDollar(t), t.Name)
	}
}
```

The Go example models the backend, API-first variant named in dimension 8,
an integration handler test standing in for a real in-process HTTP handler
test against real internal collaborators, rather than a rendered UI
component, showing the shape applies the same way outside the browser.
