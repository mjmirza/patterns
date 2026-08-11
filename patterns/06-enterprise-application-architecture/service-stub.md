---
name: Service Stub
slug: service-stub
family: 06-enterprise-application-architecture
category: Base Patterns
aliases: [Test Stub, Stub Server]
first_described: "David Rice, in Martin Fowler, Patterns of Enterprise Application Architecture, Addison-Wesley, 2002"
maturity: canonical
related: [gateway, separated-interface, layer-supertype, remote-facade, registry, stub, fake, mock, testcontainers, contract-test, adapter, proxy]
incompatible_with: []
verified: 2026-08-02
---

# Service Stub

## 1. Name, aliases, and lineage

The canonical name is Service Stub. It is catalogued as one of the Base
Patterns in Martin Fowler, *Patterns of Enterprise Application Architecture*,
Addison-Wesley, 2002, chapter 18, and the individual write-up on Fowler's own
site records that the Service Stub entry itself was authored by David Rice and
published on 5 March 2003 (martinfowler.com, "Service Stub", entry attributed
to David Rice, dated 5 March 2003, part of the *Patterns of Enterprise
Application Architecture* catalog index at
https://martinfowler.com/eaaCatalog/, verified 2026-08-02). The page states the
pattern's job in one sentence, it "removes dependence upon problematic
services during testing" (martinfowler.com/eaaCatalog/serviceStub.html,
verified 2026-08-02).

Two aliases are in genuine circulation. **Test Stub** is used loosely in
architecture discussions for the same idea, though it collides with a
narrower, more common meaning. Gerard Meszaros catalogued Test Stub as one of
five kinds of test double in *xUnit Test Patterns. Refactoring Test Code*,
Addison-Wesley, 2007, and that unit-level meaning, a substitute for any single
collaborator inside a test, is documented separately in this catalog under
Stub, family 14 (see this repository's own `patterns/14-testing/stub.md`).
Service Stub, the entry in hand, is the architecture-level specialisation of
that same idea, scoped specifically to an out-of-process, third-party, or
otherwise problematic SERVICE, and wired in per deployment environment rather
than per unit test. **Stub Server** is the second alias, used when the
substitute is implemented as an actual local process speaking the vendor's
wire protocol, an HTTP server bound to localhost, for example, rather than as
a plain in-process object.

One naming trap is worth flagging up front because it recurs constantly in
code review. The word "mock" is used in casual speech for almost any test
substitute, and several popular open source projects are literally named with
it, MockServer among them. Fowler's own, stricter vocabulary disagrees with
that usage. "Mocks are pre-programmed with expectations which form a
specification of the calls they are expected to receive. They can throw an
exception if they receive a call they don't expect," while "Stubs provide
canned answers to calls made during the test, usually not responding at all
to anything outside what's programmed in for the test" (Martin Fowler, "Mocks
Aren't Stubs", published 2 January 2007,
https://martinfowler.com/articles/mocksArentStubs.html, verified 2026-08-02).
A Service Stub, in almost every real deployment, answers calls without
verifying that the calls were made in a particular order or count. It is a
Stub in Fowler's own sense, by his own name for the pattern, whatever the
tool that implements it happens to be called.

## 2. Problem and context

An enterprise system routinely depends on a service it does not own and
cannot fully control. A credit bureau that scores an applicant. A government
tax authority that returns the rate for a jurisdiction. A payment processor.
An address-validation vendor. A partner's pricing engine that has not shipped
yet, or has shipped but only to a staging environment the whole team shares.

The problem shows up as a pattern of symptoms rather than a single failure.
The continuous integration build turns red not because the code is wrong but
because the vendor's sandbox happened to be down for maintenance during the
run. A developer working from a train or a coffee shop with an unreliable
connection cannot make progress on a feature that has nothing to do with the
network itself. A per-call fee attached to a live credit check means "run the
full suite before every commit" is no longer a free habit, it is a line item
someone in finance eventually asks about. A shared sandbox account has its
own request quota, and the whole team competes for the same quota during a
release crunch, so one engineer's load test starves everyone else's normal
development traffic. And an entire class of behavior, "what does our code do
when the vendor returns a 503, or a malformed body, or times out after 28
seconds," is close to impossible to provoke reliably against the real thing,
even though it is exactly the behavior most worth testing.

Fowler's own framing of the fix is direct. Replacing the service during
testing with "a Service Stub that runs locally, fast, and in memory improves
your development experience" (martinfowler.com/eaaCatalog/serviceStub.html,
verified 2026-08-02). The context in which that fix actually applies has
three parts. First, the dependency genuinely sits outside the team's control,
a different organisation's uptime, a different organisation's pricing model,
a different organisation's release calendar. Second, the interaction is
narrow, or can be narrowed, to a handful of operations a substitute can
honestly answer, rather than an open-ended surface nobody could hope to
imitate faithfully. Third, the team that owns the calling code also owns, or
can add, the seam at which a substitute implementation can be swapped in,
because a service nobody can decouple from cannot be stubbed no matter how
much everyone wishes it could be.

## 3. Forces

The pattern trades real fidelity for speed and control, and the trade is
visible along several axes at once.

- **Speed versus fidelity.** The stub answers in microseconds because it does
  no I/O. The price is that it can only ever be as faithful as the scenarios
  someone bothered to encode into it.
- **Determinism versus realism.** A canned answer is the same every time,
  which is exactly what a reliable test suite wants and exactly what a live,
  rate-shifting, market-driven service will never give you. The service
  itself may be non-deterministic by nature, a currency conversion rate, a
  live inventory count, a fraud score, and none of that variability belongs
  inside a unit test.
- **Isolation versus drift.** Isolating the team from the vendor's outages
  also isolates the team from the vendor's real behavior changes. The stub
  can quietly stop matching reality while every test built against it stays
  green (developed further in dimension 11).
- **Cost versus coverage.** A free, local stub removes the metered cost of a
  live call, but every branch the stub does not encode is a branch that ships
  untested, discovered for the first time in production.
- **Secret sprawl versus operational simplicity.** Once local development and
  most of CI run against a stub, real vendor credentials no longer need to
  live on every laptop and every CI runner, which shrinks the set of places a
  production secret can leak from. The cost is that the fewer environments
  ever exercise the real credential path, the fewer chances anyone has to
  notice that path silently broke.
- **Team topology.** A platform or integrations team can own the stub as a
  shared, versioned artifact, matching the same boundary reasoning that
  Separated Interface and Registry rely on elsewhere in this family, letting
  feature teams build against a stable local contract while the platform team
  manages the actual vendor relationship.
- **One more moving part.** The stub is code. It has to be written, kept
  running, versioned, and kept honest. A team that adds a Service Stub and
  never revisits it has added a maintenance burden that looks free on day one
  and is not free on day four hundred.

## 4. Applicability and non-applicability

Reach for a Service Stub when most of the following hold.

- The dependency is a service the team does not control, whether a
  third-party vendor, another organisation's system, or an internal partner
  team whose release schedule runs on its own clock.
- The dependency is measurably problematic in a concrete way, unreliable,
  slow, rate limited, billed per call, or non-deterministic by design (a live
  rate, a random fraud score, the current time).
- The interaction is already narrow, or can be narrowed with a Gateway or
  Separated Interface, to a handful of operations a substitute can honestly
  answer without pretending to reimplement the vendor's entire business.
- The team needs to provoke error and edge-case behavior, a timeout, a
  malformed body, a specific error code, on demand, which the real service
  will not reliably reproduce.
- Continuous integration must run unattended and must not depend on live
  network access to infrastructure outside the organisation's own control.

Do NOT reach for a Service Stub in the following cases, and the reasoning
behind each is the part worth remembering, not only the rule.

- **The dependency is fast, free, deterministic, and already runs inside the
  organisation's own infrastructure**, a database on the same network, an
  internal service with no external SLA risk. Isolating a test from it is
  still sometimes worth doing, but the better tool is usually a Fake or a
  disposable container (see this catalog's Testcontainers entry, family 14),
  because a real, lightweight instance of the dependency is available and a
  hand-maintained stub adds a second implementation to keep in sync for no
  real gain.
- **The very thing the test exists to prove is the integration itself.** An
  acceptance or contract test whose job is to demonstrate that this system
  and the real vendor still agree cannot be satisfied by a stub, because the
  stub is precisely the thing standing between the test and the defect it
  needs to catch. That layer belongs to a Contract Test (family 14) run
  against the real service or its provider-verified sandbox, with the Service
  Stub reserved for the layers of the test pyramid beneath it.
- **A regulator or a certification process requires exercising the vendor's
  approved test environment specifically.** A PCI-DSS payment certification,
  for instance, is not satisfied by a hand-rolled canned-response substitute,
  because the certification is asserting something about the real
  integration path, not about the calling code's internal logic.
- **Nobody on the team is positioned to keep the stub honest.** If no one
  owns re-verifying the stub's canned answers against the vendor's actual
  contract on any schedule, the stub will drift silently (dimension 11).
  Where that ownership genuinely cannot be established, a lighter,
  self-refreshing approach, recording real request and response pairs with a
  tool such as VCR and replaying them, "record your test suite's HTTP
  interactions and replay them during future test runs for fast,
  deterministic, accurate tests" (VCR project, GitHub README,
  https://github.com/vcr/vcr, verified 2026-08-02), can serve better than a
  hand-authored stub that nobody revisits.
- **The engineering cost of a second implementation exceeds the flakiness it
  would prevent.** A dependency called twice a day from a low-stakes nightly
  batch job, where an occasional retry is cheap and acceptable, rarely earns
  a parallel stub implementation.
- **The consequence of a wrong canned answer reaching a real decision is
  severe enough that any risk of the stub leaking into a live path is
  unacceptable**, a clinical decision support call or a safety interlock, for
  example. In those cases the operational discipline needed to guarantee the
  stub can never answer for real (dimension 17) may cost more scrutiny than
  the pattern is worth, and an architecture that removes the ambiguity
  entirely, a hard compile-time or deployment-time separation rather than a
  runtime switch, is worth the extra ceremony.

## 5. Structure

Five participants, named by the role each plays.

- **Client.** The application code that needs an answer from the service. It
  is written against ServiceInterface only and never imports either
  implementation directly.
- **ServiceInterface.** A narrow interface expressed in the application's own
  vocabulary, not the vendor's wire format, listing only the operations the
  application actually calls. This is a Separated Interface (family 06) in
  its own right, and in practice the two patterns are almost always found
  together.
- **RealServiceGateway.** The production implementation of ServiceInterface.
  It performs the real network call, handles the vendor's authentication, and
  translates the vendor's own error shapes into the application's own
  exception types. It is frequently itself an instance of Gateway (family
  06).
- **ServiceStub.** A second implementation of the identical interface. It
  performs no I/O, and answers from data held in memory, whether hard-coded,
  loaded from a small fixture, or programmed per test through a builder
  method.
- **Selector.** The composition-time decision that hands the Client one
  implementation or the other, keyed off environment (test, CI, staging,
  production). In practice this is a dependency-injection container profile,
  an explicit factory function, or, in the simplest codebases, a single `if`
  in a bootstrap file. The single most important property of the Selector,
  developed in dimension 11, is what it does when the environment is
  ambiguous or unset, and the safe answer is to fail loudly rather than
  default silently to the stub.

## 6. ASCII structure diagram

```
              +----------------------------+
              |           Client           |
              |----------------------------|
              | knows only ServiceInterface|
              +----------------------------+
                            |
                            | calls
                            v
              +----------------------------+
              |      ServiceInterface      |
              |----------------------------|
              | + rateFor(zip): Rate       |
              +----------------------------+
                     ^              ^
                     | implements   | implements
                     |              |
      +---------------------+  +---------------------+
      |  RealServiceGateway  |  |     ServiceStub     |
      |----------------------|  |---------------------|
      | + rateFor(zip): Rate |  | + rateFor(zip): Rate|
      | calls the vendor     |  | returns canned data,|
      | over the network     |  | no network I O      |
      +---------------------+  +---------------------+
                     ^                     ^
                     |  selects one at     |
                     |  boot time          |
                     +----------+----------+
                                |
                       +------------------+
                       |  Wiring, i.e.    |
                       |  the environment |
                       |  or DI selector  |
                       +------------------+
```

## 7. Dynamics

The property worth stating first is that Selector decides once, at
composition time, not per call. The Client never asks "am I talking to the
real thing right now." It holds one reference for the lifetime of the
process, or for the lifetime of a test, and calls it exactly as it would call
the real thing.

```
Bootstrap        Selector           Client          ChosenImpl(stub or real)
   |                 |                 |                       |
   |-- APP_ENV=test->|                 |                       |
   |                 |-- new ServiceStub() ---------------------->|
   |                 |-- bind to ServiceInterface -->|            |
   |                 |                 |                       |
   |                 |                 |-- rateFor("94103") ---->|
   |                 |                 |                       |
   |                 |                 |            (stub. no network call,
   |                 |                 |             looks up canned map)
   |                 |                 |<-- 0.0863 -------------|
   |                 |                 |                       |
   ...  a request for a zip the stub was never programmed for  ...
   |                 |                 |-- rateFor("99999") ---->|
   |                 |                 |<-- raises. no canned    |
   |                 |                 |    rate for zip 99999   |
   |                 |                 |  (a real coverage gap,  |
   |                 |                 |   made loud instead     |
   |                 |                 |   of silently wrong)    |
```

Two timing details matter in practice. First, if the ServiceStub is a real,
protocol-level local server rather than a plain in-process object, there is a
second bootstrap step where the server itself must finish binding to a port
before Selector hands its base URL to the Client, and a Client that races
ahead of that bind will see connection-refused errors that have nothing to do
with the pattern and everything to do with startup ordering. Second, a stub
that raises loudly on an unprogrammed input, as shown above, is a design
choice worth making on purpose. A stub that instead silently returns a zero
or a default value on any unrecognised input hides exactly the coverage gap
that failure mode 3 (dimension 11) describes.

## 8. Implementation variants

**Hard-coded stub.** One method, one literal return value, always. The
fastest to write and the first thing most teams reach for. It works only
until a second test needs a different scenario, at which point it must
either grow a parameter or be replaced by a configurable variant.

**Configurable stub.** The stub exposes a setter or builder that lets a test
program the response before exercising the Client, `stub.program("94103",
0.0863)` in the code example that follows. This is the shape most teams
converge on, and it maps directly to the "Configurable Test Stub" naming used
in the general test-double literature this catalog covers separately under
Stub, family 14.

**Scenario-keyed stub.** Canned responses are looked up by input, a map from
zip code to rate, from account id to credit score, useful whenever the Client
itself branches on the service's answer and the test needs to drive every
branch.

**Record-and-replay stub.** The first test run hits the real service and
records the exchange to a fixture file, replaying that fixture on every later
run with no network call. VCR (Ruby) and its ports to other ecosystems follow
this shape, "record your test suite's HTTP interactions and replay them
during future test runs" (VCR README, https://github.com/vcr/vcr, verified
2026-08-02). The trade is close to zero authoring effort against a real
maintenance cost, fixtures must be re-recorded on a schedule or they drift
exactly like a hand-written stub would (dimension 11).

**Protocol-level stub server.** A small process bound to localhost that
speaks the vendor's real wire protocol, HTTP and JSON most commonly, so the
Client's own HTTP transport code, request building, header handling, response
parsing, error mapping, is exercised unmodified. Only the base URL changes.
WireMock and stripe-mock both take this shape (dimension 9). This variant is
the right choice specifically when the code worth testing includes the
transport layer itself, not only the business logic sitting above
ServiceInterface.

**Vendor-hosted sandbox.** Some vendors run their own stand-in environment,
Stripe's test mode and PayPal's Sandbox among the best known, speaking the
real protocol against test credentials with no real money movement. As
engineering judgement rather than a sourced claim, this is better understood
as the vendor supplying its own instance of a Service Stub than as the
consuming team implementing the pattern, because Fowler's own criterion for
the pattern, that it "runs locally, fast, and in memory"
(martinfowler.com/eaaCatalog/serviceStub.html, verified 2026-08-02), is only
partly satisfied. A hosted sandbox is fast and safe, but it is neither local
nor free of network variance, and a vendor outage of the sandbox itself
reintroduces the exact problem the pattern exists to remove.

**Vendor-distributed local emulator.** A full local process, distributed by
the platform vendor itself, that reproduces a real API surface closely enough
to run production-shaped code against it. The Google Cloud Pub/Sub emulator
is the clearest example (dimension 9). Judged strictly against Fowler's
taxonomy this sits closer to a Fake, "actually have working implementations,
but usually take some shortcut which makes them not suitable for production"
(Fowler, "Mocks Aren't Stubs", verified 2026-08-02), than to a hand-coded
canned-response Stub, but it serves the identical architectural role
described in this entry and teams routinely file it under the same name.

## 9. Known production uses

**WireMock.** An open source HTTP API stub server, described by its own
documentation as a tool that helps teams "create stable test and development
environments, isolate yourself from flakey 3rd parties and simulate APIs that
don't exist yet" (WireMock documentation, https://wiremock.org/docs/, verified
2026-08-02). It runs as a local process, is configured with request-matching
rules and canned responses, and is widely embedded directly into JVM, .NET,
and language-agnostic Docker-based test suites specifically to remove a live
third-party HTTP dependency from CI.

**stripe-mock.** Stripe's own official test double for its payments API,
described in its README as "a mock HTTP server based on the real Stripe API"
that "accepts the same requests and parameters that the Stripe API accepts,"
maintained by Stripe for use in the test suites of Stripe's server-side SDKs
(stripe/stripe-mock, GitHub README, https://github.com/stripe/stripe-mock,
verified 2026-08-02). Stripe's own documentation is explicit that the
responses are "completely hardcoded" and that the tool is meant for "basic
sanity checks" rather than a full behavioral substitute, which is a useful,
vendor-stated confirmation of the non-applicability boundary in dimension 4.

**Moto.** A Python library that intercepts calls made through the AWS SDK
(boto3) and answers them locally instead of reaching real AWS infrastructure,
so that code written against AWS services can be tested "without making real
requests to AWS infrastructure." Moto additionally "comes with a stand-alone
server allowing you to mock out the AWS HTTP endpoints," explicitly so that
languages other than Python can stub the same AWS calls over the network
(Moto documentation, "Getting Started",
https://docs.getmoto.org/en/latest/docs/getting_started.html, verified
2026-08-02).

**Google Cloud Pub/Sub emulator.** Google's own first-party local substitute
for its Pub/Sub messaging service, described in Google's documentation as
providing "local emulation of the production Pub/Sub service," letting a team
develop and validate Pub/Sub-dependent code on a local machine, avoiding both
network calls to production infrastructure and the billing that would
otherwise accrue during development and testing (Google Cloud documentation,
"Pub/Sub emulator", https://docs.cloud.google.com/pubsub/docs/emulator,
verified 2026-08-02). This is the clearest instance in production use of the
vendor-distributed local emulator variant from dimension 8.

## 10. Consequences

Positive.

- Local development and the bulk of the test suite become deterministic,
  fast, and able to run with no network connectivity at all.
- Per-call vendor fees and shared sandbox quota contention are removed from
  the normal development loop entirely.
- Error and edge-case behavior, timeouts, malformed responses, specific
  vendor error codes, can be provoked on demand, on purpose, which the real
  service will rarely cooperate with.
- Development against a partner or vendor integration can proceed ahead of
  that vendor's own sandbox being ready, because ServiceInterface only needs
  to be agreed on paper, not delivered by anyone else first.
- Real vendor credentials no longer need to reach every developer machine and
  every CI runner, shrinking the number of places a genuine production secret
  is stored.

Negative.

- A second implementation now exists that must be written, and every future
  change to the vendor's real contract is a change that must be manually
  mirrored into it, or the two silently diverge.
- Contract drift is the headline risk, discussed fully in dimension 11, a
  test suite can stay entirely green while the real integration is broken.
- A passing test against a friendly stub proves nothing about authentication
  behavior, real error-code fidelity, or the system's behavior under real
  network conditions such as partial responses or slow drips of data.
- If the wiring that selects an implementation is ever wrong in a live
  environment, real customers can be served fabricated data, a serious
  operational and, in some domains, safety and compliance risk (dimension
  17).
- Hand-written stubs accumulate their own undocumented assumptions over
  time and, without discipline, become an informal, unversioned, unreviewed
  specification of a vendor's API that lives only in test code.

## 11. Failure modes and misuse

**Silent contract drift.** Symptom. A production incident traced to the real
service returning a new field, a changed shape, or a new error code the
application has never handled, while the entire test suite stayed green
throughout. Cause. Nobody re-verifies the stub's canned responses against the
real service on any schedule, so the stub encodes a snapshot of a contract
that is months or years stale. Fix. Pair the Service Stub with a scheduled
Contract Test (family 14) run against the real sandbox, nightly or on every
vendor SDK bump, and treat a contract-test failure with the same priority as
a broken unit test, not as a lower-tier, ignorable check.

**Stub reachable in production.** Symptom. Real customers receive obviously
fake data, a hard-coded "$0.00" tax figure, a sample credit score that is
always exactly the same round number. Cause. The environment-selection wiring
defaults to the stub whenever a configuration value is missing or malformed,
rather than refusing to start, or a URL left pointed at a stub host survives
a deploy unnoticed. Fix. Make Selector fail loudly, refuse to boot, throw at
startup, when the environment claims to be production and no explicit,
validated real-service configuration is present. Add a deployment-pipeline
smoke check that asserts, from outside the process, which implementation type
is actually wired for each ServiceInterface before a rollout is called
healthy.

**Stub over-fitted to the happy path.** Symptom. A fully green test suite, and
then an unhandled exception in production the first time the vendor returns a
timeout, a 503, or a malformed body the code has genuinely never been
exercised against. Cause. The stub only ever returns one successful canned
value, so every branch that exists to handle failure has zero test coverage,
and it looks fine because nothing ever fails inside the test. Fix. Deliberately
extend the stub, or add a distinct scenario-driven variant, to return each
error condition the vendor's own documentation describes, and require a test
per condition asserting the Client degrades correctly, not merely that it
does not crash.

**Business logic creeping into the stub.** Symptom. The stub grows
conditionals, loops, and computed values that increasingly mirror the
vendor's own pricing or tax arithmetic, and later a bug is traced to the
stub's own logic quietly masking a real bug in the Client's own summation
code. Cause. Over time, someone extends the stub to "look more realistic"
instead of keeping it a dumb, literal data source, and it becomes an
unreviewed, second implementation of business logic that properly belongs to
the vendor, not to this codebase. Fix. Keep the stub to table lookups and
literal returns only. A genuine need for realistic, computed behavior is a
signal to reach for a vendor-hosted sandbox or a Fake built explicitly from
the vendor's own published reference behavior, not to hand-author business
rules inside test infrastructure.

**Team-wide flake from a shared local stub.** Symptom. An identical commit
passes on one engineer's machine and fails in continuous integration, or
fails intermittently on a shared CI runner. Cause. A protocol-level stub
server was implemented as a listener bound to a hard-coded local port, and a
second stub instance, or an unrelated process, is already holding that port
on the runner. Fix. Bind the stub server to port zero so the operating system
assigns a free port, and inject the resolved base URL into the Client under
test at run time, never hard-code a port number anywhere the stub or the
Client can see it.

## 12. Trade-off matrix

Compared against the named alternatives that address the same felt problem,
an external dependency making tests slow, flaky, or expensive.

| Approach | Speed | Determinism | Fidelity to real contract | Setup and maintenance cost | Works fully offline | Catches integration regressions |
|---|---|---|---|---|---|---|
| Real service, called live | Slow, network-bound | Low, subject to vendor state and outages | Highest, it is the real thing | None to build, but ongoing sandbox management | No | Yes, directly |
| Service Stub (this pattern) | Fastest, in-process or localhost | Highest, canned answers | Only as good as the encoded scenarios, decays without upkeep | Moderate to write, moderate to keep current | Yes | No, by design |
| Fake (family 14) | Fast, in-process | High | Higher than a Stub if faithfully reimplemented, still an approximation | High, a real behavioral reimplementation is more work than canned data | Yes | No, but closer than a Stub for logic bugs |
| Testcontainers (family 14) | Slower than a Stub, real process startup | High once started | Very high, it is the real dependency's own image | Low authoring effort if an image exists, none if it does not | Usually, image must be pulled once | Partially, catches version and config regressions in the real dependency |
| Record and replay, VCR-style | Fastest after first recording | High between recordings | Accurate at time of recording, decays afterward exactly like a Stub | Low authoring effort, recurring re-recording cost | Yes, after first recording | No, unless re-recorded regularly |
| Contract Test against real or hosted sandbox | Slow, network-bound like the real service | Depends on the sandbox's own stability | Highest achievable without full production | Moderate, needs sandbox access and credentials | No | Yes, that is its entire purpose |

The honest reading of the table is that no single row wins across every
column, which is exactly why Service Stub and Contract Test are described
together in dimension 11 rather than as competitors. Service Stub wins the
inner development loop. Contract Test, or the real service, is what actually
proves the integration still holds.

## 13. Related and incompatible patterns

**Gateway** (family 06). A Service Stub is, in the overwhelming majority of
real codebases, a second implementation of a Gateway's own interface.
Gateway supplies the narrow surface; Service Stub supplies a substitute body
behind it.

**Separated Interface** (family 06). This is literally the interface
ServiceInterface realises in this entry's structure. Placing the interface in
a package neither the real implementation nor the stub depends on is what
lets test code depend on the interface and the stub, and never on the real
implementation's package at all, so a test build never even needs to link
against the vendor's SDK.

**Layer Supertype** (family 06). When RealServiceGateway and ServiceStub
share genuinely cross-cutting behavior, request logging, a shared error
type, a common retry-count field for diagnostics, that shared code can live
in a common supertype. Most of the time it should not, because the stub
deliberately skips network concerns like retries and timeouts that only make
sense for the real implementation.

**Remote Facade** (family 06). When the real service is itself accessed
through a coarse-grained remote facade, the ServiceInterface mirrors that
same coarse shape rather than the vendor's raw wire-level calls, which keeps
the number of methods the stub has to answer small and stable.

**Registry** (family 06). Occasionally used as the mechanism that hands out
the correct implementation, real or stub, by environment, particularly in
codebases that predate a full dependency-injection container.

**Stub, Fake, Mock, Dummy, Spy** (family 14). Service Stub is an
architecture-level instance of the general Stub role described in this
catalog's testing family, scoped specifically to an out-of-process service
dependency and wired per environment rather than constructed per test. It is
not a Mock in Fowler's stricter sense, dimension 1, because in its usual form
it does not verify that particular calls occurred; a variant that does record
and assert on calls has crossed into Spy territory and is worth naming
honestly as such in code review rather than calling it a stub out of habit.

**Testcontainers** (family 14). A different answer to the same felt problem,
avoid a flaky, slow, or unavailable external dependency, achieved by running
the real dependency in a disposable local container instead of writing a
substitute for it. Prefer Testcontainers when a lightweight, real,
containerisable version of the dependency exists. Prefer Service Stub when it
does not, which is the common case for a proprietary third-party SaaS API
with no distributable image.

**Contract Test** (family 14). The necessary companion pattern that keeps a
Service Stub honest over time. A Service Stub with no accompanying contract
test is not wrong on day one, but it degrades toward the silent-drift failure
mode described in dimension 11 as the real service evolves and the stub does
not.

**Adapter and Proxy** (family 01, GoF). Structurally, a ServiceStub is best
read as a Proxy standing in for the real subject behind a shared interface,
except its motivation is test and development isolation rather than the
classic GoF Proxy motivations of access control or lazy initialisation.
ServiceInterface itself is frequently realised as an Adapter over whatever
shape the vendor's own SDK happens to expose, translating it into the
application's own vocabulary.

No structural incompatibility is recorded against this pattern. The one
combination worth calling out as a recognised anti-pattern, rather than a
formal incompatibility, is shipping a Service Stub with no accompanying
Contract Test, which is documented fully as the first failure mode in
dimension 11.

## 14. Refactoring path in and out

Introducing the pattern into code that calls a problematic service directly.

1. Find every call site that reaches the third-party or otherwise problematic
   service. In an older codebase these are often scattered rather than
   centralised.
2. Introduce a Separated Interface expressing only the operations the
   application actually needs, named in the application's own vocabulary,
   not the vendor's.
3. Extract the existing calling code, network client, credential handling,
   error translation, into a RealServiceGateway class implementing that
   interface. This step is itself the Extract Class refactor, applied so that
   what was inline network code becomes one class implementing one interface.
4. Replace every call site with a call through the interface, obtained via
   constructor injection or a factory, never constructed inline at the point
   of use.
5. Write ServiceStub against the same interface, starting with the smallest
   set of canned answers that lets the existing test suite pass with no
   network access at all.
6. Wire environment-based selection so tests and local development default to
   the stub and staging and production default to the real gateway, with an
   unset or ambiguous environment defaulting to a hard failure rather than
   silently choosing the stub, closing the loop opened by failure mode 2 in
   dimension 11.
7. Add a scheduled Contract Test against the real service, closing the loop
   opened by isolating the team from the real service's own evolution in step
   6.

Removing the pattern, once it stops earning its place, a fast, official
vendor sandbox has matured, or the dependency has been internalised as an
in-process library.

1. Confirm a genuinely cheaper, faster, and reliable enough way to exercise
   real behavior now exists, an official sandbox with no real flakiness, a
   distributable container image, or an in-process library replacing what
   used to be a network call.
2. Point the test-time wiring at that new option, leaving ServiceInterface
   itself unchanged, since the whole point of the interface was to make this
   swap cheap.
3. Run both the old stub-backed suite and the new suite in parallel for a
   period before deleting ServiceStub, since deleting it immediately risks
   silently losing coverage of an error path that only the stub was ever
   programmed to exercise.
4. Retire the environment-selection branching entirely once a single
   implementation genuinely serves every environment, rather than leaving
   dead branches for a stub nobody constructs anymore.

## 15. Testing and verification

RealServiceGateway is usually tested narrowly and separately from the main
suite, tagged as an integration test run against a real sandbox account on a
slower cadence, specifically so its own translation logic, mapping the
vendor's error shapes into the application's own exception types, has
coverage without slowing down the suite everyone runs on every commit.

The Selector itself deserves a small, direct test of its own, asserting that
selecting the test environment actually yields a ServiceStub instance and not
accidentally a RealServiceGateway. This is a meta-test that guards directly
against failure mode 2 in dimension 11, and it is inexpensive relative to the
incident it prevents.

Because the stub is cheap and deterministic to construct, the bulk of the
business logic that consumes ServiceInterface should be tested purely against
it, with every scenario the Client is expected to handle correctly, the
happy path, each documented error condition, a malformed response, programmed
explicitly rather than inferred.

What genuinely becomes harder is end-to-end confidence that the real
integration still functions as the stub assumes it does. That gap is
precisely what Contract Test exists to close, and it should be run on its own
slower schedule, nightly or on merges to a main branch, rather than gating
every commit, because it depends on network access the fast inner loop must
not depend on.

Test doubles for the stub's own internals are rarely warranted. If the stub
needs its own tests to trust, that is itself a signal that it has grown logic
worth doubling, which is failure mode 4 in dimension 11, business logic
creeping into infrastructure that should hold nothing but data.

## 16. Observability signals

Log, at process startup, which concrete implementation was wired for each
ServiceInterface, at a log level visible in every environment's normal boot
output, so a misconfiguration is caught by a human reading the logs before a
deploy is called healthy rather than discovered later through a customer
complaint.

Expose a health-check field or metric naming the active implementation per
service dependency, and alert if any non-test environment ever reports the
stub as active. This is the direct, mechanical, observable counterpart to the
prevention described for failure mode 2, catching the case where prevention
alone was not enough.

For a protocol-level stub server, log every incoming request that did not
match any configured scenario. An unmatched request against a stub inside an
otherwise passing test almost always means the Client's request shape has
silently changed, and the test is not actually exercising the path it appears
to exercise.

Track, on the same dashboard that shows deployment health, how long it has
been since the stub's canned responses were last verified against the real
service by the scheduled Contract Test. A stale verification date is a
staleness signal worth surfacing before it becomes a production incident.

## 17. Security and privacy implications

A Service Stub built for a service that handles sensitive data, a credit
score, an identity verification result, a health-related answer, must never
be built from a copy of a real production response. A fixture checked into
source control is effectively permanent and readable by everyone with repo
access, current employees, past employees whose access was never fully
revoked, and, in an open source or contractor context, outside parties.
Canned data belongs to synthetic, deliberately invented values only.

Because a stub bypasses the real service's own authentication and
authorization enforcement entirely, a client accidentally wired to a stub in
a context where auth checks are expected, an entitlements or authorization
service in particular, can silently be granted access it should have been
denied. The observability practice above, loud logging of the active
implementation, is a partial mitigation. The stronger discipline is that an
authorization or entitlement dependency generally should not be stubbed to
"always allow" as its default canned behavior; every scenario the stub
answers for an auth-shaped dependency should be an explicit, reviewed case,
not a permissive fallback.

Real vendor credentials no longer need to reach every developer machine and
every CI runner once a Service Stub replaces the real call across most
environments, which genuinely shrinks the number of places a live production
secret is stored, worth recording here as a real security improvement rather
than only as the convenience noted under Consequences.

A local, protocol-level stub server bound to all network interfaces instead
of loopback, on a shared CI runner or on a developer's machine connected to
an untrusted network, can expose whatever canned data or logic it holds to
other processes on that same network. Bind stub servers to loopback only,
127.0.0.1 or the platform equivalent, never to a wildcard address.

## 18. References

- Martin Fowler, "Service Stub", entry authored by David Rice, published 5
  March 2003, part of *Patterns of Enterprise Application Architecture*,
  https://martinfowler.com/eaaCatalog/serviceStub.html, verified 2026-08-02.
- Martin Fowler, *Patterns of Enterprise Application Architecture*,
  Addison-Wesley, 2002, chapter 18, Base Patterns (the martinfowler.com entry
  above states the full explanation appears in chapter 18 of the book).
- Martin Fowler, "Patterns of Enterprise Application Architecture" catalog
  index, listing Service Stub among the Base Patterns,
  https://martinfowler.com/eaaCatalog/, verified 2026-08-02.
- Martin Fowler, "Mocks Aren't Stubs", published 2 January 2007,
  https://martinfowler.com/articles/mocksArentStubs.html, verified 2026-08-02.
- Martin Fowler, "TestDouble", bliki entry defining Dummy, Fake, Stub, Spy,
  and Mock, https://martinfowler.com/bliki/TestDouble.html, verified
  2026-08-02.
- Gerard Meszaros, *xUnit Test Patterns. Refactoring Test Code*,
  Addison-Wesley, 2007. The general Test Stub taxonomy this entry
  specializes for out-of-process services; the unit-level pattern itself is
  documented in this catalog's own `patterns/14-testing/stub.md` entry.
- WireMock documentation, https://wiremock.org/docs/, verified 2026-08-02.
- Stripe, "stripe-mock" README, https://github.com/stripe/stripe-mock,
  verified 2026-08-02.
- Moto documentation, "Getting Started",
  https://docs.getmoto.org/en/latest/docs/getting_started.html, verified
  2026-08-02.
- Google Cloud documentation, "Pub/Sub emulator",
  https://docs.cloud.google.com/pubsub/docs/emulator, verified 2026-08-02.
- VCR project, README, https://github.com/vcr/vcr, verified 2026-08-02.

## Code examples

Working, minimal implementations of the same TaxRateService example across
four languages. Each defines ServiceInterface, a RealServiceGateway stand-in,
a configurable ServiceStub, and a Selector that fails loudly outside test
environments when no real credential is present. All four were compiled or
run directly against the toolchains available on this machine, `tsc
--strict`, `python3 -m py_compile` and a direct run, `go vet` and `go run`,
and `rustc`, all confirmed successful. Java is omitted because no Java
Runtime is installed on this machine, so a `javac` claim could not be
verified and is not made.

```typescript
interface TaxRateService {
  rateFor(zip: string): Promise<number>;
}

class RealTaxRateService implements TaxRateService {
  constructor(private baseUrl: string, private apiKey: string) {}

  async rateFor(zip: string): Promise<number> {
    const res = await fetch(`${this.baseUrl}/rates/${zip}`, {
      headers: { Authorization: `Bearer ${this.apiKey}` },
    });
    if (!res.ok) {
      throw new Error(`tax service returned ${res.status}`);
    }
    const body = (await res.json()) as { rate: number };
    return body.rate;
  }
}

class StubTaxRateService implements TaxRateService {
  private canned = new Map<string, number>([
    ["94103", 0.0863],
    ["10001", 0.08875],
  ]);

  program(zip: string, rate: number): void {
    this.canned.set(zip, rate);
  }

  async rateFor(zip: string): Promise<number> {
    const rate = this.canned.get(zip);
    if (rate === undefined) {
      throw new Error(`no canned rate programmed for zip ${zip}`);
    }
    return rate;
  }
}

function buildTaxRateService(env: string): TaxRateService {
  if (env === "production" || env === "staging") {
    const key = process.env.TAX_API_KEY;
    if (!key) {
      throw new Error("TAX_API_KEY must be set outside test environments");
    }
    return new RealTaxRateService("https://tax.example.com", key);
  }
  return new StubTaxRateService();
}

async function main(): Promise<void> {
  const service = buildTaxRateService(process.env.APP_ENV ?? "test");
  const rate = await service.rateFor("94103");
  console.log(`rate for 94103 is ${rate}`);
}

main();
```

```python
from __future__ import annotations
import os
from abc import ABC, abstractmethod
from typing import Optional
from urllib.request import urlopen, Request
import json


class TaxRateService(ABC):
    @abstractmethod
    def rate_for(self, zip_code: str) -> float: ...


class RealTaxRateService(TaxRateService):
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url
        self.api_key = api_key

    def rate_for(self, zip_code: str) -> float:
        req = Request(f"{self.base_url}/rates/{zip_code}")
        req.add_header("Authorization", f"Bearer {self.api_key}")
        with urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read())
        return float(body["rate"])


class StubTaxRateService(TaxRateService):
    def __init__(self) -> None:
        self._canned: dict[str, float] = {"94103": 0.0863, "10001": 0.08875}

    def program(self, zip_code: str, rate: float) -> None:
        self._canned[zip_code] = rate

    def rate_for(self, zip_code: str) -> float:
        rate = self._canned.get(zip_code)
        if rate is None:
            raise KeyError(f"no canned rate programmed for zip {zip_code}")
        return rate


def build_tax_rate_service(env: str) -> TaxRateService:
    if env in ("production", "staging"):
        key: Optional[str] = os.environ.get("TAX_API_KEY")
        if not key:
            raise RuntimeError("TAX_API_KEY must be set outside test environments")
        return RealTaxRateService("https://tax.example.com", key)
    return StubTaxRateService()


def main() -> None:
    service = build_tax_rate_service(os.environ.get("APP_ENV", "test"))
    print(f"rate for 94103 is {service.rate_for('94103')}")


if __name__ == "__main__":
    main()
```

```go
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
)

type TaxRateService interface {
	RateFor(zip string) (float64, error)
}

type RealTaxRateService struct {
	BaseURL string
	APIKey  string
}

func (r *RealTaxRateService) RateFor(zip string) (float64, error) {
	req, err := http.NewRequest("GET", r.BaseURL+"/rates/"+zip, nil)
	if err != nil {
		return 0, err
	}
	req.Header.Set("Authorization", "Bearer "+r.APIKey)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return 0, err
	}
	var payload struct {
		Rate float64 `json:"rate"`
	}
	if err := json.Unmarshal(body, &payload); err != nil {
		return 0, err
	}
	return payload.Rate, nil
}

type StubTaxRateService struct {
	canned map[string]float64
}

func NewStubTaxRateService() *StubTaxRateService {
	return &StubTaxRateService{canned: map[string]float64{
		"94103": 0.0863,
		"10001": 0.08875,
	}}
}

func (s *StubTaxRateService) Program(zip string, rate float64) {
	s.canned[zip] = rate
}

func (s *StubTaxRateService) RateFor(zip string) (float64, error) {
	rate, ok := s.canned[zip]
	if !ok {
		return 0, fmt.Errorf("no canned rate programmed for zip %s", zip)
	}
	return rate, nil
}

func buildTaxRateService(env string) (TaxRateService, error) {
	if env == "production" || env == "staging" {
		key := os.Getenv("TAX_API_KEY")
		if key == "" {
			return nil, fmt.Errorf("TAX_API_KEY must be set outside test environments")
		}
		return &RealTaxRateService{BaseURL: "https://tax.example.com", APIKey: key}, nil
	}
	return NewStubTaxRateService(), nil
}

func main() {
	env := os.Getenv("APP_ENV")
	if env == "" {
		env = "test"
	}
	service, err := buildTaxRateService(env)
	if err != nil {
		panic(err)
	}
	rate, err := service.RateFor("94103")
	if err != nil {
		panic(err)
	}
	fmt.Printf("rate for 94103 is %v\n", rate)
}
```

```rust
use std::collections::HashMap;
use std::env;

trait TaxRateService {
    fn rate_for(&self, zip: &str) -> Result<f64, String>;
}

struct RealTaxRateService {
    base_url: String,
    api_key: String,
}

impl TaxRateService for RealTaxRateService {
    fn rate_for(&self, zip: &str) -> Result<f64, String> {
        let url = format!("{}/rates/{}", self.base_url, zip);
        let _auth = format!("Bearer {}", self.api_key);
        Err(format!("real network call to {} not performed in this example", url))
    }
}

struct StubTaxRateService {
    canned: HashMap<String, f64>,
}

impl StubTaxRateService {
    fn new() -> Self {
        let mut canned = HashMap::new();
        canned.insert("94103".to_string(), 0.0863);
        canned.insert("10001".to_string(), 0.08875);
        StubTaxRateService { canned }
    }

    fn program(&mut self, zip: &str, rate: f64) {
        self.canned.insert(zip.to_string(), rate);
    }
}

impl TaxRateService for StubTaxRateService {
    fn rate_for(&self, zip: &str) -> Result<f64, String> {
        self.canned
            .get(zip)
            .copied()
            .ok_or_else(|| format!("no canned rate programmed for zip {}", zip))
    }
}

fn build_tax_rate_service(env: &str) -> Result<Box<dyn TaxRateService>, String> {
    if env == "production" || env == "staging" {
        let key = env::var("TAX_API_KEY")
            .map_err(|_| "TAX_API_KEY must be set outside test environments".to_string())?;
        return Ok(Box::new(RealTaxRateService {
            base_url: "https://tax.example.com".to_string(),
            api_key: key,
        }));
    }
    Ok(Box::new(StubTaxRateService::new()))
}

fn main() {
    let app_env = env::var("APP_ENV").unwrap_or_else(|_| "test".to_string());
    let service = build_tax_rate_service(&app_env).expect("failed to build service");
    let rate = service.rate_for("94103").expect("no canned rate");
    println!("rate for 94103 is {}", rate);
}
```
