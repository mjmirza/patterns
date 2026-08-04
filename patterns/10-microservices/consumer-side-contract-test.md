---
name: Consumer-Side Contract Test
slug: consumer-side-contract-test
family: 10-microservices
category: Testing
aliases: [Consumer-Driven Contract Test, CDC Test, Pact Test]
first_described: "Robinson 2006, Consumer-Driven Contracts: A Service Evolution Pattern"
maturity: canonical
related: [service-component-test, transactional-outbox, idempotent-consumer, api-gateway, distributed-tracing]
incompatible_with: []
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

The canonical name in the microservices testing literature is Consumer-Side
Contract Test, used by Chris Richardson's microservices.io pattern catalog to
describe a test written and owned by the team that consumes a remote service,
asserting that the consumer's code can construct valid requests to that
service and correctly parse its responses (microservices.io, Testing
strategies, verified 2026-08-02). The wider industry term for the same idea,
and the one most engineers reach for first, is Consumer-Driven Contract test,
often shortened to CDC test.

The lineage traces to Ian Robinson's 2006 article "Consumer-Driven Contracts,
A Service Evolution Pattern," published on martinfowler.com. Robinson argued
that a service's contract should be shaped by the union of what its actual
consumers need, not defined unilaterally by the provider team and handed
down (Fowler.com, Consumer-Driven Contracts, Ian Robinson, 12 June 2006,
verified 2026-08-02). Robinson's original pattern was organizational and
architectural, describing how contracts should be negotiated. The testing
technique that operationalizes it, generating an executable contract from
consumer-side tests and replaying it against the provider, was formalized
later by the Pact project, first released by the REA Group team in New
Zealand and now maintained by the Pact Foundation (docs.pact.io, verified
2026-08-02).

In everyday conversation the three names, consumer-side contract test,
consumer-driven contract test, and Pact test, are used almost
interchangeably, because Pact is by a wide margin the most common tool that
implements the pattern. This entry uses "consumer-side contract test" for
the general pattern and "Pact" when discussing the specific tool mechanics,
since not every implementation of the pattern uses Pact.

## 2. Problem and context

A team owns a service that calls another team's service over HTTP, gRPC, or
an asynchronous message channel. Both teams deploy independently, on their
own schedule, several times a day in a mature organization. The consuming
team cannot run the real provider in their test suite for every commit,
because the provider may be down, may be slow, may require test data the
consumer does not control, or may not exist yet if the two teams are
building in parallel. So the consuming team mocks the provider's responses
in their tests, based on documentation, a shared wiki page, or a Slack
message from three weeks ago describing the API shape.

That mock is a guess. Nothing forces it to stay accurate. The provider team
changes a field name, removes a field the consumer's mock never included but
the real code silently depended on, or changes a status code from 200 to
202, and every one of the consumer's unit tests keeps passing against the
now-wrong mock. The break surfaces only in staging, or in production, hours
or days after the provider's deploy, at which point the two teams are paging
each other trying to reconstruct what changed and who is at fault.

The context in which this problem is acute is specifically a microservices
or service-oriented architecture with independent deployability as a stated
goal. Sam Newman describes exactly this tension in Building Microservices.
Independent deployability is one of the primary reasons to adopt
microservices, but it only works if teams can be confident a change will not
silently break a consumer they have never talked to (Newman, Building
Microservices, 2nd edition, O'Reilly, 2021, chapter 1, "What Is a
Microservice"). A monolith does not have this problem in the same form,
because a compiler or a single shared test suite catches the break at build
time. Across a network boundary, with a separate deploy pipeline on each
side, nothing catches it automatically unless something is built to.

## 3. Forces

**Test speed and reliability against test realism.** Running the actual
provider gives the highest-fidelity assurance but is slow, flaky under
shared test environments, and often impossible to run per commit in CI. A
consumer-side contract test runs in milliseconds against a mock, but the mock
is only as trustworthy as the mechanism that keeps it synchronized with
reality.

**Team autonomy against cross-team coordination.** The entire point of
splitting services is to let teams move independently. A pattern that
requires the provider team to manually review and approve every consumer's
expectations before each release reintroduces the coordination cost the
architecture was meant to remove. The pattern favors autonomy, and pushes
the synchronization work into an automated verification step rather than a
meeting.

**Coupling depth.** A contract that captures every field in a provider's
response, including fields the consumer never reads, couples the two
services more tightly than necessary, since a provider adding an unused
field would break the contract for no functional reason. The pattern favors
a narrow contract, capturing only what the consumer actually consumes, over
a complete schema.

**Confidence before deploy against cost of the safety net.** A contract
broker with a can-i-deploy gate (see dimension 9) adds infrastructure, a
shared service both teams depend on, and a CI step on every pipeline. That
infrastructure cost buys the ability to say, before deploying, whether a
proposed change will break any known consumer. Teams with two or three
internal integrations sometimes decide the coordination overhead of the
broker outweighs the benefit and rely on manual contract review instead.

**Symmetry of who tests what.** The pattern deliberately makes the consumer
team responsible for stating its own expectations, rather than the provider
team guessing what consumers need or writing an exhaustive integration
suite that tests every possible consumer. This shifts effort to the party
with the actual knowledge of what is used, at the cost of making the
provider team dependent on consumers publishing contracts promptly.

## 4. Applicability and non-applicability

Use a consumer-side contract test when.

- Two services are owned by different teams (or will be deployed and scaled
  independently even if the same team owns both) and communicate over a
  network boundary, whether synchronous HTTP or RPC, or asynchronous
  messaging.
- The consuming team wants fast, deterministic tests in their own CI
  pipeline without booting the real provider, its database, or its
  downstream dependencies.
- Both teams can agree to run a verification step, either via a shared
  broker or via published pact files copied into the provider's repository,
  as part of the provider's own CI pipeline.
- The interaction surface is stable enough to be described as a finite set
  of interactions (a small number of endpoints or message types), because
  the technique does not scale gracefully to open-ended, dynamically typed,
  or free-form payloads.

Do not use a consumer-side contract test when.

- The provider is a third party outside your organization that will never
  run your consumer's contract verification step. Pact and the wider
  pattern assume the provider team can be brought into the loop. Against a
  truly external API (a payment gateway, a public SaaS API) a contract test
  against a mock still catches your own regressions, but it can never catch
  a break the provider introduces, because there is no verification step on
  their side. Use an integration or smoke test against a sandbox
  environment instead, or in addition.
- The interaction is a single, extremely stable, well-versioned public API
  with a formal OpenAPI or protobuf schema and its own compatibility
  guarantees. In that case a schema-validation test against the published
  schema may deliver most of the benefit with far less machinery, and full
  contract testing is redundant overhead.
- The team wants full behavioral or business-logic verification of the
  provider. A consumer-side contract test only proves that a specific
  request produces a response of the expected shape. It does not, and is
  not meant to, verify the provider's business correctness, its
  performance under load, or its behavior under concurrent access. Those
  need separate integration, load, and full-flow tests.
- The two sides genuinely cannot coordinate at all, not even through a
  shared broker or a periodic file exchange. Some regulated, air-gapped, or
  adversarial-trust environments fall here. The pattern depends on some
  channel of cooperation existing.

## 5. Structure

- **Consumer.** The service (or client) that calls another service. Owns
  the contract test. Defines, in code, every interaction it actually needs,
  a specific request it will send, and the specific shape of response it
  needs back to function.
- **Contract (pact file).** A serialized, language-agnostic artifact,
  typically JSON, produced by running the consumer's contract tests. It
  records each interaction as a request-response pair, plus matching rules
  that say which parts of the response are load-bearing (a field must
  exist and be a string) versus incidental (an exact example value that
  need not match byte for byte in the real provider).
- **Mock provider.** A local, in-process HTTP server (or message-broker
  stand-in) that the consumer's tests run against. It is generated from the
  same interaction definitions that produce the contract, so the mock and
  the contract can never drift apart from each other, only from the real
  provider.
- **Contract broker (optional but standard).** A shared, queryable store
  (the Pact Broker is the reference implementation) that consumers publish
  contracts to and providers pull contracts from. It also stores
  verification results and exposes a can-i-deploy query (docs.pact.io,
  Pact Broker, verified 2026-08-02).
- **Provider verification test.** A test, run by the provider team in the
  provider's own CI pipeline, that replays every interaction from every
  consumer's published contract against the real, running provider (often
  with test-data setup via provider states) and asserts the real responses
  satisfy the contract's matching rules.

## 6. ASCII structure diagram

```
+-------------------------------------------------------------+
|                        CONSUMER repo                        |
|                                                               |
|  +-----------------+       generates       +--------------+ |
|  | Consumer test    | ---------------------> | pact.json    | |
|  | (asserts against |                        | (the         | |
|  |  a mock provider)| <----------------------|  contract)   | |
|  +-----------------+     runs against         +------+-------+ |
|          |                                          |         |
|          v                                          |         |
|  +-----------------+                                |         |
|  | Mock Provider    |                                |         |
|  | (in-process,     |                                |         |
|  |  generated from  |                                |         |
|  |  same defs)      |                                |         |
|  +-----------------+                                |         |
+-------------------------------------------------------------+
                                                        |
                                                        v  publish
                                          +--------------------------+
                                          |      Contract Broker      |
                                          | (stores pacts + results,  |
                                          |  answers can-i-deploy)    |
                                          +-------------+-------------+
                                                        |  pull
                                                        v
+-------------------------------------------------------------+
|                        PROVIDER repo                         |
|                                                                |
|  +-----------------+      replays          +---------------+  |
|  | Verification test| ---------------------> | Real provider |  |
|  | (per interaction |                        | service       |  |
|  |  in the contract)| <----------------------|               |  |
|  +-----------------+   real response, checked +---------------+  |
|          |               against matching rules                 |
|          v                                                       |
|  publish verification result back to the Contract Broker         |
+-------------------------------------------------------------+
```

## 7. Dynamics

```
1. Consumer developer writes a test. "When I call GET /orders/42,
   the mock should return an order with an id (number) and a
   status (one of a known set of strings)."
2. Running the consumer test suite.
   a. The Pact (or equivalent) library spins up a local mock server.
   b. The mock server is configured with the expected interaction.
   c. The consumer's real client code makes the real HTTP call,
      hitting the mock, not the real provider.
   d. The test asserts on the consumer's own parsed result.
   e. On success, the library serializes every interaction used
      during the test run into a pact.json file.
3. CI publishes pact.json to the Contract Broker, tagged with the
   consumer's version (often a commit SHA or semantic version).
4. Provider CI, on every commit, pulls the latest pact(s) tagged
   for the environment it is about to deploy to.
5. For each interaction in each pact.
   a. Verification test sets up the "provider state" the
      interaction assumes ("order 42 exists").
   b. Verification test sends the exact recorded request to the
      REAL running provider.
   c. The real response is checked against the pact's matching
      rules, not against exact string equality.
   d. Result (pass or fail per interaction) is published back to
      the Broker, associated with the provider's version.
6. Before either side deploys, its CI runs "can-i-deploy," a query
   to the Broker asking whether its version, verified against the
   currently deployed version of its counterpart, is known good.
   A "no" blocks the deploy.
```

## 8. Implementation variants

**Consumer-driven via a broker (the canonical Pact workflow).** Consumers
publish contracts to a central broker; providers pull and verify against
every consumer that matters for the target environment; can-i-deploy gates
releases on both sides. This is the variant described in dimensions 5 to 7
and is what most teams mean when they say "contract testing" today
(docs.pact.io, verified 2026-08-02).

**Consumer-driven without a broker, via file exchange.** Smaller teams, or
teams that reject the operational cost of running a broker, sometimes copy
the generated pact JSON file directly into the provider's repository (as a
fixture committed alongside the provider's own test suite) rather than
running a shared service. This loses the can-i-deploy matrix and the
version-compatibility history, but keeps the core mechanic. the consumer's
expectations, expressed as data, drive the provider's verification test.

**Provider-driven contract test (the inverse, worth naming to avoid
confusion).** Some teams write contract tests from the provider side. The
provider team defines the schema it will support and consumers verify
their code against it. This is a different pattern with a different name,
often called schema-based contract testing or, when built on OpenAPI,
consumer-side schema validation. It sacrifices the "captures only what is
actually used" property that makes consumer-driven contracts narrow and
low-coupling. This entry's pattern is specifically consumer-driven, not
provider-driven, and the distinction matters when choosing a tool.

**Bidirectional contract testing.** A hybrid, popularized by PactFlow around
2021, where the provider publishes an OpenAPI specification and the
consumer's Pact contract is checked for compatibility against that
specification, without the provider ever running a live verification test
against the consumer's exact interactions. This trades some fidelity
(no live replay against a real running instance) for removing the
requirement that the provider team adopt Pact's verification tooling at
all, useful when the provider is a large legacy system or a third party
that already publishes OpenAPI but will not run consumer-driven
verification tests.

**Message-based (asynchronous) contract tests.** The same idea applied to
Kafka topics, SQS queues, or any event-driven channel, where the "request"
side does not exist and the contract is purely a statement that a message
handler expects to be able to deserialize and process a given message
shape. Pact supports this via its message pact format, verifying that a
message handler can process a given message body without needing a live
broker in the loop (docs.pact.io, Pact for message queues, verified
2026-08-02).

## 9. Known production uses

**M1 Finance**, a financial technology company, is documented by PactFlow as
having "rapidly rolled out contract testing with PactFlow" during a period
of hypergrowth, using it to keep its many services safely deployable as the
engineering team scaled (pactflow.io/case-studies, verified 2026-08-02).

**Boost Insurance** is documented by PactFlow as reporting an "80% increase
in service stability" attributed to adopting PactFlow contract testing
across its services (pactflow.io/case-studies, verified 2026-08-02).

**Booking.com, Agoda, Culture Amp, and Motorola** are listed by PactFlow as
organizations using Pact or PactFlow for contract testing, alongside the
statement that "thousands of companies use Pactflow to deploy with ease"
(pactflow.io/case-studies, verified 2026-08-02). This entry cites the named
companies specifically and treats the aggregate "thousands" figure as a
vendor marketing claim rather than an independently verifiable production
use, per the judgement-versus-sourced-claim distinction in this
repository's template.

**REA Group**, the Australian real estate advertising company, originated
Pact internally to solve exactly the consumer-provider synchronization
problem described in dimension 2, before it was open-sourced and became
the Pact Foundation project now maintained independently (docs.pact.io,
About Pact, verified 2026-08-02).

## 10. Consequences

Positive.

- Consumer tests run fast and deterministically, in process, with no
  network dependency on the real provider, its database, or its
  downstream services.
- A provider change that would break a real consumer is caught in the
  provider's own CI pipeline, before deploy, rather than discovered in
  staging or production hours later.
- The contract is generated from real, executed test code, not hand-written
  documentation, so it cannot silently drift out of sync with what the
  consumer's tests actually assert, the way a wiki page or an OpenAPI spec
  maintained by hand can.
- Because the contract only captures interactions the consumer's tests
  actually exercise, the provider team gets a precise, low-noise signal of
  what is genuinely depended upon, versus a full schema that may include
  fields nobody reads.
- The can-i-deploy gate turns whether a change broke a consumer from a
  question answered by post-incident investigation into a question
  answered automatically before the deploy happens.

Negative.

- A contract test is not an integration test. It proves shape and
  matching-rule compliance, not business correctness, so teams that treat
  a green contract suite as proof the two services genuinely work together
  are misled. It needs to sit alongside, not instead of, some amount of
  real integration testing.
- Introducing the pattern requires cross-team buy-in. The provider team
  must agree to run a verification step in their pipeline, which is a real
  process and cultural change, not merely a library the consumer team can
  adopt unilaterally.
- A broker becomes a new piece of shared infrastructure with its own
  availability and access-control requirements. If the broker is down,
  can-i-deploy checks fail closed or must be bypassed, either of which
  has operational consequences.
- Provider states (the setup step that puts the provider into the
  condition an interaction assumes, "order 42 exists") are extra test
  scaffolding the provider team must write and maintain, and they can
  themselves drift from reality if not kept honest.
- For a consumer with many downstream providers, the discipline of writing
  and maintaining a contract per interaction is nontrivial ongoing effort,
  and teams under delivery pressure are prone to letting contracts go
  stale or skipping them for "quick" integrations.

## 11. Failure modes and misuse

Symptom. The contract suite is green, but the two services still break in
production. Cause. The contract only encodes a matching rule ("status is a
string"), not the full domain of valid values, so a provider can return a
technically matching but semantically wrong value (a status the consumer's
code does not have a case for) and the contract test never notices. Fix.
Tighten matching rules to enumerate the actual known-valid set where the
domain is small and stable, and accept that contract tests are a
shape-and-existence check, not a substitute for a small number of genuine
full-flow smoke tests on the critical path.

Symptom. Provider verification tests are constantly red, and the provider
team starts ignoring the failures. Cause. Consumers are publishing
contracts for interactions they no longer actually use, often because a
consumer removed a code path but never regenerated and republished its
pact file, so the provider is being held to a promise nobody is depending
on anymore. Fix. Version and tag contracts by deployed environment, and
have consumers republish (or explicitly retire) contracts as part of every
deploy, so the broker's view of what is depended on right now stays
current, and prune contracts for consumer versions that are no longer
deployed anywhere.

Symptom. The same interaction is defined slightly differently across five
different consumer test files, and the provider verification test run
takes ten minutes because of duplicated near-identical interactions.
Cause. No shared contract-definition helper or DSL was established inside
the consumer team, so every developer hand-rolls interaction definitions
from scratch, including their own drift in header casing, field ordering
assumptions, or copy-pasted stale examples. Fix. Centralize common
interaction builders in one place inside the consumer codebase and have
individual tests compose from them, the same discipline applied to Page
Object patterns in UI test suites.

Symptom. A genuinely breaking provider change slips through, because
can-i-deploy passed. Cause. The consumer had not deployed in weeks, so
the "currently deployed" version of the consumer the Broker checks against
was an old, stale tag, and the provider change only broke the consumer's
newest, unpublished code, which had no contract on file yet. Fix. This is
a coordination gap, not a tooling bug. Contract testing only protects
against breaks in interactions that have been captured in a published,
tagged contract. An unpublished or un-updated contract cannot protect
anyone, so publishing on every commit or every deploy, not periodically,
is the actual mitigation.

Symptom. Teams adopt the pattern, then quietly abandon it within a year.
Cause, drawn from repeated field reports rather than a single citation.
The initial setup (broker infrastructure, CI wiring on both sides,
provider-state scaffolding) is done by one motivated engineer, and when
that person moves teams the maintenance burden has no clear owner, so
contract files silently stop being updated and the safety property erodes
without anyone noticing until the next incident. Fix. Treat contract test
maintenance as an explicit, assigned responsibility inside the on-call or
code-owner rotation of both the consumer and provider teams, the same as
any other test suite, rather than a one-time setup task.

## 12. Trade-off matrix

| Force | Consumer-side contract test (Pact-style) | Full integration test | Provider-published OpenAPI + schema validation | Shared library / RPC-generated client with compile-time types |
|---|---|---|---|---|
| Test speed | Fast, in-process mock, no network | Slow, requires real environments | Fast, schema check is local | Fast, but only catches shape errors the type system encodes |
| Confidence in real interop | High for shape and matching rules, none for business logic | Highest, exercises real systems start to finish | Medium, catches shape drift only if the spec is kept current | Medium, catches structural drift, not runtime response content |
| Cross-team coordination cost | Moderate, both sides adopt tooling and process | Low to set up per team, high to keep environments stable | Low, provider owns the spec unilaterally | Low, but requires shared build tooling or a monorepo |
| Coupling introduced | Narrow, only actually used fields | None extra beyond runtime coupling | Broad, full schema, including unused fields | Tight compile-time coupling, breaks build not merely tests |
| Catches provider break before deploy | Yes, via can-i-deploy gate | Only if the pipeline runs the real integration before every deploy, rarely feasible at that cadence | Only if consumer re-validates against spec regularly | Yes, at compile time, if the client is regenerated per provider version |
| Works against a third-party or external provider | Poorly, needs provider cooperation | Yes, via a sandbox environment if the third party offers one | Yes, if the third party publishes and honors a stable OpenAPI spec | Rare, only if the third party ships an SDK |

## 13. Related and incompatible patterns

**Service Component Test.** A consumer-side contract test is often layered
underneath a service component test (this repository's entry
`service-component-test.md`), which tests a whole service in isolation
with its real dependencies stubbed out. A service component test may use a
Pact mock provider as one of its stubs, combining both patterns.

**Transactional Outbox and Idempotent Consumer.** For asynchronous,
message-based interactions, contract tests are typically written against
the message shape published via a Transactional Outbox and consumed by an
Idempotent Consumer (both entries in this repository). The contract
verifies the message shape; the outbox and idempotent-consumer patterns
handle delivery reliability, a separate concern the contract test does
not cover.

**API Gateway.** When a gateway sits between the consumer and the real
provider, contract tests can be written either against the gateway's
contract with the provider or against the consumer's contract with the
gateway, and teams need to be explicit about which boundary is under test,
because conflating the two hides where a real break would occur.

**Distributed Tracing.** Distributed tracing (this repository's entry) is
the production-time complement to contract testing's pre-deploy nature.
Contract tests prevent known-shape breaks before deploy; tracing helps
diagnose the unknown-shape or timing-related failures that contract tests
cannot catch, once they happen live.

**Incompatible with nothing structurally**, but it is functionally
redundant with, and should not be treated as a substitute for, hand-written
full-flow integration tests on the small number of interactions where
business-logic correctness across the boundary genuinely needs to be
proven, not merely shape compliance.

## 14. Refactoring path in and out

Introducing the pattern into an existing consumer with hand-mocked tests
starts with the single highest-risk integration, typically the one that
has broken production most recently. Replace the hand-written mock in that
one test file with a Pact-generated mock, defining the interaction as
precisely what the code under test actually sends and reads. Publish the
resulting contract, but do not yet wire a can-i-deploy gate. First get the
provider team to add a verification test against that one contract,
running it in their CI as an informational, non-blocking step. Once both
sides trust the signal (typically after a few weeks of the verification
step correctly staying green or correctly catching real drift), promote
the verification step to blocking, and only then wire can-i-deploy into
the deploy pipelines on both sides. Repeat per integration, prioritizing
by incident history rather than converting the whole surface area at once.

Removing the pattern when it stops earning its place is rare, but it
happens when two services are folded back into one (a monolith
consolidation, or when a team simply merges), or when the provider is
replaced by a stable, versioned, externally owned SDK the team no longer
controls at the wire-protocol level. When removing, do not simply delete
the contract test file. First confirm the interaction is genuinely covered
by whatever replaces it (a shared type system, a merged codebase's own
compiler, or a vendor SDK's own compatibility guarantees), then retire the
contract from the broker explicitly (most brokers support marking a
pacticipant version as no longer deployed) so can-i-deploy stops
considering it, rather than letting it silently rot as an unmaintained,
permanently stale entry.

## 15. Testing and verification

Testing the pattern itself, not merely using it to test something else,
means verifying three properties independently.

First, that the consumer's mock-based tests genuinely exercise the real
client code path, not a stub of it. A common mistake is writing the
contract test against a hand-rolled HTTP call inside the test file itself,
rather than against the actual production client class, which means a bug
in the real client is never caught even though the contract test passes.
Verification. The test should import and call the exact same client
function or class the production code path uses, with only the base URL
swapped to point at the mock.

Second, that the provider's verification step genuinely exercises the
real provider, including its real routing, real middleware, and ideally a
real, migrated database with realistic test data, not an in-memory fake
that has itself drifted from production behavior. Verification. Run
provider verification tests against the same build artifact (the same
container image or deployable) that would actually ship, not against
source run in a special test mode that behaves differently.

Third, that matching rules are neither too loose (accepting any string
where only three enum values are ever valid, silently masking a real
regression) nor too tight (asserting an exact value the provider is free
to change without breaking any real consumer behavior, causing false
positives that erode trust in the suite). Verification. Periodically
mutation test the contract itself, deliberately breaking the provider in
a way a real consumer would care about, and confirming the verification
suite catches it, and separately confirm a cosmetic, non-breaking provider
change (reordering unrelated response fields, adding a new optional
field) does not fail verification.

Test doubles used inside this pattern. The Pact mock provider is itself a
programmable test double, an HTTP stub server configured per interaction.
On the provider side, provider states function as a form of test data
builder or object mother, setting up preconditions before each verified
interaction runs.

## 16. Observability signals

A healthy consumer-side contract testing setup shows, on a CI dashboard,
consistently green consumer contract-generation jobs on every commit to
main, a steadily current set of published contracts per consumer version
in the broker with no consumer version older than the team's normal
deploy cadence still marked as the latest for its environment, provider
verification jobs that run and complete on every provider commit rather
than only nightly, with a stable pass rate, and can-i-deploy checks that
resolve in seconds, not minutes, since a slow broker query becomes a
bottleneck every team routes their deploy pipeline through.

Signals worth logging and alerting on specifically. A spike in
verification failures immediately following a provider deploy, which is
the exact signal the pattern exists to surface and should be visible, not
buried, in the provider team's own CI notifications. Contracts that have
not been republished in longer than the consumer's own typical release
cadence, a proxy for a contract that may be stale and no longer
protecting anyone. And can-i-deploy denials, which represent a caught
regression and are worth tracking as a positive metric, an estimate of
production incidents the gate plausibly prevented, not merely as pipeline
friction to be minimized.

A failing instance looks like verification jobs that are disabled, marked
allow-failure, or simply not run for weeks at a time, contracts published
once during initial setup and never updated as the consumer's actual
usage evolved, or a broker with authentication or availability issues
that has caused teams to route around can-i-deploy with a manual override
that has become the unremarked default path.

## 17. Security and privacy implications

Pact files, and contract test fixtures generally, commonly embed example
request and response bodies, which means example data (names, emails,
account identifiers, tokens) can end up committed to a shared broker or a
version-controlled fixture file if authored carelessly by copying real
production payloads rather than synthetic examples. Treat contract
fixtures the same as any other test data with respect to data-handling
policy. Use synthetic or clearly fake example values, never a raw copy of
a real production response, even when that response was easiest to grab
from a browser network tab while writing the test.

A contract broker is itself an internal service with access to what
amounts to a structural map of every service-to-service interaction in the
organization, request shapes, header names, and often authentication
header patterns, even if example token values are, or should be, redacted
or replaced with placeholders. It should be access-controlled the same as
any other internal infrastructure that exposes architectural metadata, and
authentication tokens used by CI pipelines to publish and query contracts
should be scoped and rotated the same as any other CI secret, since a
leaked broker credential could let an attacker publish a false contract or
read the full interaction map of the organization's services.

The pattern itself has no bearing on runtime authentication or
authorization between the real services. Matching rules can assert that an
Authorization header is present and has some shape, but the pattern
deliberately does not, and should not be extended to, validate actual
token contents or secrets during contract verification, since doing so
would require real credentials inside test fixtures.

## Code examples

All three examples below are original, minimal, and dependency free. None
uses the real Pact library, since bringing in Pact's own runtime would
obscure the mechanic this pattern actually describes. each shows the same
three moves. an interaction is defined as data, a mock provider is built
from that data, and the consumer's real client code runs against the mock
while the interaction is captured in a shape a provider-side verification
test could later replay. Java and Kotlin are the languages where a real
Pact JVM consumer test would most commonly be written in production, and
are omitted here only because a from-scratch JVM HTTP mock server needs
more scaffolding than is useful for a from-first-principles illustration,
not because the pattern does not apply there.

### TypeScript

Compiled with `tsc` under `--strict`, targeting Node's built-in `http` and
global `fetch`. Ran successfully with `node`.

```typescript
// Minimal, dependency-free illustration of consumer-side contract testing
// in TypeScript. Not the Pact library. Shows the same mechanic as the
// Python example: an interaction becomes a mock, the real client runs
// against the mock, and the interaction is captured as a contract.

import * as http from "node:http";

interface Interaction {
  description: string;
  method: string;
  path: string;
  responseStatus: number;
  responseBody: Record<string, unknown>;
  requiredFields: string[];
}

class MockProvider {
  private server: http.Server;
  private interactions = new Map<string, Interaction>();
  private port = 0;

  constructor() {
    this.server = http.createServer((req, res) => {
      const key = `${req.method} ${req.url}`;
      const interaction = this.interactions.get(key);
      if (!interaction) {
        res.writeHead(404);
        res.end();
        return;
      }
      res.writeHead(interaction.responseStatus, { "Content-Type": "application/json" });
      res.end(JSON.stringify(interaction.responseBody));
    });
  }

  addInteraction(i: Interaction): void {
    this.interactions.set(`${i.method} ${i.path}`, i);
  }

  start(): Promise<string> {
    return new Promise((resolve) => {
      this.server.listen(0, "127.0.0.1", () => {
        const address = this.server.address();
        if (address && typeof address === "object") {
          this.port = address.port;
        }
        resolve(`http://127.0.0.1:${this.port}`);
      });
    });
  }

  stop(): Promise<void> {
    return new Promise((resolve) => this.server.close(() => resolve()));
  }
}

async function getOrder(baseUrl: string, orderId: number): Promise<Record<string, unknown>> {
  const res = await fetch(`${baseUrl}/orders/${orderId}`);
  if (!res.ok) {
    throw new Error(`unexpected status ${res.status}`);
  }
  return (await res.json()) as Record<string, unknown>;
}

function assert(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

async function main(): Promise<void> {
  const provider = new MockProvider();
  const interaction: Interaction = {
    description: "an order with id 42 exists",
    method: "GET",
    path: "/orders/42",
    responseStatus: 200,
    responseBody: { id: 42, status: "SHIPPED" },
    requiredFields: ["id", "status"],
  };
  provider.addInteraction(interaction);
  const baseUrl = await provider.start();

  try {
    const order = await getOrder(baseUrl, 42);
    for (const field of interaction.requiredFields) {
      assert(field in order, `missing field ${field}`);
    }
    assert(order.status === "SHIPPED", "status did not match");
    assert(typeof order.id === "number", "id was not a number");

    const contract = {
      consumer: "order-web",
      provider: "order-service",
      interactions: [
        {
          description: interaction.description,
          request: { method: interaction.method, path: interaction.path },
          response: { status: interaction.responseStatus, body: interaction.responseBody },
        },
      ],
    };
    const rendered = JSON.stringify(contract);
    assert(rendered.includes("order-service"), "contract missing provider name");
    assert(rendered.includes("SHIPPED"), "contract missing captured response body");

    console.log("all consumer contract assertions passed");
  } finally {
    await provider.stop();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
```

### Python

Standard library only, `http.server` for the mock and `unittest` for the
consumer test. Ran successfully with `python3 -m unittest`.

```python
"""Minimal, dependency-free illustration of consumer-side contract testing.

This is not the Pact library. It shows the core mechanic: a consumer
defines an interaction, a mock server is built from it, the real client
code runs against the mock, and the interaction is captured as a
contract that a provider-side test could replay later.
"""
from __future__ import annotations

import http.server
import json
import socket
import threading
import unittest
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Interaction:
    description: str
    method: str
    path: str
    response_status: int
    response_body: dict[str, Any]
    required_fields: list[str] = field(default_factory=list)


class MockProviderHandler(http.server.BaseHTTPRequestHandler):
    interactions: dict[tuple[str, str], Interaction] = {}

    def log_message(self, *_args: Any) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        key = ("GET", self.path)
        interaction = self.interactions.get(key)
        if interaction is None:
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps(interaction.response_body).encode()
        self.send_response(interaction.response_status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


class MockProvider:
    def __init__(self) -> None:
        self._server = http.server.HTTPServer(("127.0.0.1", 0), MockProviderHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    def add_interaction(self, interaction: Interaction) -> None:
        MockProviderHandler.interactions[(interaction.method, interaction.path)] = interaction

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()


def get_order(base_url: str, order_id: int) -> dict[str, Any]:
    import urllib.request

    with urllib.request.urlopen(f"{base_url}/orders/{order_id}") as resp:
        return json.loads(resp.read())


class OrderClientContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = MockProvider()
        self.interaction = Interaction(
            description="an order with id 42 exists",
            method="GET",
            path="/orders/42",
            response_status=200,
            response_body={"id": 42, "status": "SHIPPED"},
            required_fields=["id", "status"],
        )
        self.provider.add_interaction(self.interaction)
        self.provider.start()

    def tearDown(self) -> None:
        self.provider.stop()

    def test_client_can_fetch_and_parse_an_order(self) -> None:
        order = get_order(self.provider.base_url, 42)
        for f in self.interaction.required_fields:
            self.assertIn(f, order)
        self.assertEqual(order["status"], "SHIPPED")
        self.assertIsInstance(order["id"], int)

    def test_contract_can_be_serialized_for_the_provider_team(self) -> None:
        contract = {
            "consumer": "order-web",
            "provider": "order-service",
            "interactions": [
                {
                    "description": self.interaction.description,
                    "request": {"method": self.interaction.method, "path": self.interaction.path},
                    "response": {
                        "status": self.interaction.response_status,
                        "body": self.interaction.response_body,
                    },
                }
            ],
        }
        rendered = json.dumps(contract)
        self.assertIn("order-service", rendered)
        self.assertIn("SHIPPED", rendered)


if __name__ == "__main__":
    unittest.main()
```

### Go

Standard library only, `net/http/httptest` for the mock. Ran successfully
with `go run`.

```go
// Minimal, dependency-free illustration of consumer-side contract testing
// in Go. Not the Pact library. Same mechanic as the Python and TypeScript
// versions: an interaction becomes a mock, the real client code runs
// against the mock, and the interaction is captured as a contract.
package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
)

type Interaction struct {
	Description     string
	Method          string
	Path            string
	ResponseStatus  int
	ResponseBody    map[string]interface{}
	RequiredFields  []string
}

func newMockProvider(interaction Interaction) *httptest.Server {
	mux := http.NewServeMux()
	mux.HandleFunc(interaction.Path, func(w http.ResponseWriter, r *http.Request) {
		if r.Method != interaction.Method {
			w.WriteHeader(http.StatusNotFound)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(interaction.ResponseStatus)
		_ = json.NewEncoder(w).Encode(interaction.ResponseBody)
	})
	return httptest.NewServer(mux)
}

func getOrder(baseURL string, orderID int) (map[string]interface{}, error) {
	resp, err := http.Get(fmt.Sprintf("%s/orders/%d", baseURL, orderID))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status %d", resp.StatusCode)
	}
	var order map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&order); err != nil {
		return nil, err
	}
	return order, nil
}

func must(cond bool, msg string) {
	if !cond {
		panic(msg)
	}
}

func main() {
	interaction := Interaction{
		Description:    "an order with id 42 exists",
		Method:         "GET",
		Path:           "/orders/42",
		ResponseStatus: http.StatusOK,
		ResponseBody:   map[string]interface{}{"id": 42, "status": "SHIPPED"},
		RequiredFields: []string{"id", "status"},
	}

	server := newMockProvider(interaction)
	defer server.Close()

	order, err := getOrder(server.URL, 42)
	must(err == nil, "client call against the mock provider failed")
	for _, f := range interaction.RequiredFields {
		_, ok := order[f]
		must(ok, "missing field "+f)
	}
	must(order["status"] == "SHIPPED", "status did not match")

	contract := map[string]interface{}{
		"consumer": "order-web",
		"provider": "order-service",
		"interactions": []map[string]interface{}{
			{
				"description": interaction.Description,
				"request": map[string]string{
					"method": interaction.Method,
					"path":   interaction.Path,
				},
				"response": map[string]interface{}{
					"status": interaction.ResponseStatus,
					"body":   interaction.ResponseBody,
				},
			},
		},
	}
	rendered, err := json.Marshal(contract)
	must(err == nil, "failed to marshal contract")
	must(len(rendered) > 0, "contract should not be empty")

	fmt.Println("all consumer contract assertions passed")
}
```

## 18. References

1. Ian Robinson. "Consumer-Driven Contracts. A Service Evolution Pattern."
   martinfowler.com, 12 June 2006.
   https://martinfowler.com/articles/consumerDrivenContracts.html
   Verified 2026-08-02.
2. Chris Richardson. "Pattern. Consumer-side contract test." microservices.io,
   Testing patterns.
   https://microservices.io/patterns/testing/consumer-side-contract-test.html
   Verified 2026-08-02.
3. Pact Foundation. "What is Pact." docs.pact.io.
   https://docs.pact.io/
   Verified 2026-08-02.
4. Pact Foundation. "The Pact Broker." docs.pact.io.
   https://docs.pact.io/pact_broker
   Verified 2026-08-02.
5. PactFlow. "Case Studies." pactflow.io.
   https://pactflow.io/case-studies/
   Verified 2026-08-02.
6. Sam Newman. Building Microservices, 2nd edition. O'Reilly Media, 2021.
   Chapter 1, "What Is a Microservice."
