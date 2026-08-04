---
name: Consumer-Driven Contract Test
slug: consumer-driven-contract-test
family: 10-microservices
category: Testing
aliases: [CDC Test, Contract Test, Pact Test]
first_described: "Ian Robinson, ThoughtWorks, 2006"
maturity: established
related: [service-component-test, api-gateway, remote-procedure-invocation, messaging, transactional-outbox]
incompatible_with: []
verified: 2026-08-02
---

## 1. Name, aliases, and lineage

The canonical name is Consumer-Driven Contract Test, commonly shortened to CDC
test or just contract test. The word Pact appears constantly in this space
because Pact is the most widely used open source implementation, not because Pact is
the name of the pattern itself. Some teams call the artifact a pact and the
practice contract testing, which is imprecise but near universal in casual
conversation.

The underlying idea, that a service consumer should be able to state its
expectations of a provider and have those expectations verified automatically,
was named and described by Ian Robinson in a 2006 article on martinfowler.com
titled Consumer-Driven Contracts, A Service Evolution Pattern. Robinson framed
it as an inversion of the usual provider-first contract, where a provider
publishes a WSDL or an API document and consumers build against it hoping
nothing they depend on changes. Robinson's proposal was to let contracts
emerge from the demands of consumers rather than from the imagination of
providers, so that a provider knows exactly which parts of its surface are
actually load bearing (Ian Robinson, Consumer-Driven Contracts, A Service
Evolution Pattern, martinfowler.com, 12 June 2006, verified 2026-08-02,
https://martinfowler.com/articles/consumerDrivenContracts.html).

The testing technique built on top of that idea, where each consumer
expectation is captured as an executable, machine-checkable contract and a
provider replays every consumer's contract in its own build, was implemented
starting in 2013 by a team at realestate.com.au (REA Group) working on a Ruby
microservices migration, with Ronald Holshausen and Beth Skurrie as the key
early authors and maintainers. Skurrie later built the Pact Broker and
co-founded PactFlow, the commercial contract testing platform (Pact
Foundation, History, docs.pact.io, verified 2026-08-02,
https://docs.pact.io/history). This entry is about the testing technique, the
CDC test, not only about the naming pattern from 2006. In practice the two are
inseparable, the pattern gives the reason, the test gives the mechanism.

## 2. Problem and context

A consumer service calls a provider service over HTTP, gRPC, or an
asynchronous message. Both sides deploy independently, on their own schedule,
often owned by different teams. The consumer's integration tests either hit a
real, deployed instance of the provider, which is slow, flaky under load, and
requires shared test environments that different teams collide over, or they
hit a hand-written mock that the consumer team maintains from memory of what
the provider does, which drifts from reality the first time the provider
changes a field name or a status code and nobody tells the consumer team.

The provider team faces the mirror problem. They want to refactor, remove
dead fields, tighten validation, or change an internal representation, but
they cannot know which of their fields are actually read by which consumers.
A conservative provider team freezes the API forever out of fear. An
aggressive provider team breaks a consumer in production because a full,
end-to-end integration environment that exercises every real consumer against
every real provider on every commit does not exist, or exists but is too slow
and too flaky to run on every pull request.

The context in which this problem is acute is a microservice architecture
with many independently deployed services and many consumer-to-provider
relationships, where the combinatorial cost of full end-to-end integration
testing across every pair grows faster than any team can operate. Martin
Fowler and Sam Newman both describe this specific failure mode, brittle,
slow, hard-to-diagnose end-to-end test suites, as one of the primary
motivations for adopting contract tests instead (Sam Newman, Building
Microservices, 2nd edition, O'Reilly, 2021, chapter 9, Testing, pages 316 to
328, on the cost of the testing pyramid's top layer across many services).

## 3. Forces

Fidelity versus speed. A real end-to-end test against a live provider has
the highest fidelity, it genuinely proves the two services interoperate, but
it is slow to run and slow to set up, and it fails for reasons unrelated to
the interaction under test, network flakiness, unrelated provider bugs,
environment drift. A contract test trades away some of that fidelity, the
provider verification step runs the contract against the provider in
isolation, not against the actual live consumer, in exchange for running in
seconds inside each side's own CI pipeline.

Coupling direction. Contract tests deliberately couple the provider's
release pipeline to the consumer's stated expectations. This is a form of
coupling introduced on purpose, to convert a silent, discovered-in-production
coupling into an explicit, tested one. The force here is between the
provider's desire for autonomy to change freely and the consumer's need for
stability, and the pattern resolves it by making the coupling visible and
automatically checked rather than by removing the coupling, which cannot be
removed because the services genuinely depend on each other.

Team topology and ownership. The pattern assumes the consumer team can
write and maintain their own contract, and that the provider team is willing
to run a verification step in their own pipeline that can fail their build
because of a change the provider team did not author. This works well when
consumer and provider teams trust each other and share a broker or a
repository. It works badly when the provider is a third party who will never
run your test suite, in which case there is no verification loop to close and
the pattern degrades to documentation.

Consistency of what is tested versus completeness of what could break.
Because the contract only captures interactions the consumer actually
exercises, an untested consumer behavior against an unexpected provider
change is not caught. The pattern deliberately favors testing the load
bearing surface over testing everything, which sacrifices completeness for
focus and for the ability to run fast.

Operability cost of a broker. Running Pact, or an equivalent, well
typically means running or paying for a broker, a service that stores
contracts and their verification results and answers the question can this
consumer version safely be deployed given what providers have verified
already. This is one more piece of infrastructure to operate, monitor, and
keep available, and its own outage can block deployments if the pipeline is
configured to hard fail when the broker is unreachable.

## 4. Applicability and non-applicability

Reach for a consumer-driven contract test when:

- Two or more services communicate directly, synchronously over HTTP or gRPC,
  or asynchronously over a message broker, and are deployed independently by
  different teams or on different schedules.
- The number of consumer to provider relationships is large enough that a
  full end-to-end integration suite covering every pair has become too slow
  or too flaky to run on every change, the classic testing pyramid pressure
  described in Toby Clemson's canonical write up on martinfowler.com (Toby
  Clemson, Testing Strategies in a Microservice Architecture,
  martinfowler.com, 18 November 2014, verified 2026-08-02,
  https://martinfowler.com/articles/microservice-testing/).
- The provider team is willing and able to run a verification step against
  published consumer contracts as part of their own build, meaning they can
  add a dependency on a contract broker or a shared repository.
- You want confidence about independent deployability, the ability to ship a
  provider change without first coordinating a synchronized deployment with
  every consumer, which is one of the core promises of microservice
  architecture (Sam Newman, Building Microservices, 2nd edition, O'Reilly,
  2021, chapter 1, pages 6 to 9, on independent deployability as a defining
  property).
- The interaction surface is stable enough in shape, even if the data
  changes, that request and response schemas make sense to pin down as
  concrete examples.

Do not reach for it when:

- There is only one consumer and one provider, both owned by the same team,
  deployed together, and always tested end to end anyway. The coordination
  cost of a broker buys nothing a shared integration test suite in the same
  repository does not already give you for free.
- The provider is a third party outside your organization who will never run
  your verification step, for example a public payment gateway or a SaaS
  vendor's API. A CDC test against such a provider degrades into a one sided
  regression test of your own client code, which is still useful but is not
  the consumer-driven pattern, it is closer to dimension 8's provider stub
  variant without the feedback loop.
- The interaction is driven by complex business logic that spans many
  calls and depends on server side state built up over a long conversation,
  where a single request and response pair cannot represent the real
  contract. Full component or end-to-end tests are more honest here, see
  dimension 13 for how this pattern relates to service-component-test.
- You need to verify non-functional properties, load, latency under
  concurrency, or failure injection behavior. A contract test proves the
  shape of an interaction is honored, it says nothing about how the provider
  behaves under load, and using it as a stand in for performance testing is a
  misuse covered in dimension 11.
- The team lacks any process to keep contracts, and their verification
  status, visible to both sides. A contract nobody looks at before deploying
  is worse than no contract, because it creates a false sense of safety, this
  is discussed further in dimension 11.

## 5. Structure

Consumer. The service that calls another service. Owns the consumer side
test, which drives the real client code the consumer will ship against a
mock, or stub, provider generated from stated expectations. Running this test
also produces the contract file as a side effect.

Consumer test. The executable test, written in the consumer's codebase,
that exercises the consumer's own client code against a locally started stub.
It is not testing the provider, it is testing that the consumer's client
correctly forms the request and correctly parses the response the consumer
expects.

Contract, also called the pact. A serialized, typically JSON, artifact
describing one or more interactions, each interaction stating an expected
request, method, path, headers, body, and the response the provider promised
to return for that request. The contract is generated by the consumer test
run, not hand authored, which is what makes it consumer driven rather than
provider dictated.

Provider. The service that receives the call. Owns the provider
verification step, which replays every interaction from every consumer's
contract against a real, running instance of the provider, typically with
test data or state setup hooks, and asserts the actual response matches what
the contract promised.

Provider states, sometimes called provider state handlers. Hooks the
provider team implements so the provider can be placed into the state a given
interaction assumes before replay, for example order 42 exists and is
shipped. Without these, most interactions beyond the trivial cannot be
verified because the provider has no data to respond with.

Broker, or a shared repository standing in for one. A service that stores
published contracts and published verification results, and can answer, for a
given consumer version, which provider versions it is compatible with, and
for a given provider version, is it safe to deploy given the consumer
versions currently running. Pact's implementation of this role is the Pact
Broker or the hosted PactFlow product (Pact Foundation, Pact Broker,
docs.pact.io, verified 2026-08-02, https://docs.pact.io/pact_broker).

Can I deploy check, sometimes called the deployment gate. A query run
before a deploy that asks the broker whether the version about to be deployed
has a verified, compatible relationship with every version of every service
it talks to that is currently deployed in the target environment. This is
what actually gives teams the confidence to deploy independently, the
contract test alone only proves compatibility at test time, the gate proves
it is still true at deploy time.

## 6. ASCII structure diagram

```
+------------------+          publishes           +-----------------+
|  Consumer repo    | -----------------------------> |     Broker     |
|                    |         (pact JSON)           | (or shared repo)|
|  consumer client   |                                |                 |
|  consumer test  ---+--> generates contract          | stores pacts    |
|                    |                                | stores verify   |
+--------------------+                                |   results       |
                                                        |                |
+--------------------+          fetches               | answers "can I |
|  Provider repo     | <----------------------------- |   deploy?"     |
|                    |         (pact JSON)             +-----------------+
|  provider verify --+--> replays interactions
|  provider states   |    against real provider
+--------------------+    publishes verification
                          result back to broker
```

## 7. Dynamics

```
Consumer CI                 Broker                   Provider CI
    |                          |                          |
    | run consumer test        |                          |
    | (drives client vs stub)  |                          |
    |------------------------->|                          |
    | contract JSON published  |                          |
    |------------------------->|                          |
    |                          |                          |
    |                          |   provider CI polls or   |
    |                          |   is webhook-triggered   |
    |                          |<-------------------------|
    |                          |   fetch pending contracts|
    |                          |-------------------------->|
    |                          |                          | run provider states,
    |                          |                          | replay each
    |                          |                          | interaction against
    |                          |                          | the real provider
    |                          |                          |
    |                          |   publish verification   |
    |                          |   result (pass or fail)  |
    |                          |<-------------------------|
    |                          |                          |
    | before deploy:           |                          | before deploy:
    | can-i-deploy(consumer)   |                          | can-i-deploy(provider)
    |------------------------->|                          |------------------------->|
    | yes/no + compatible      |                          | yes/no + compatible
    | provider versions        |                          | consumer versions
    |<-------------------------|                          |<-------------------------|
```

The critical property this diagram makes visible is that the consumer and
provider verification steps never run against each other directly. They both
talk only to the broker, at different times, possibly on different days. The
broker is the asynchronous handoff point, which is exactly what allows the
two teams to work and deploy on independent schedules while still getting a
synchronous style guarantee before a real deploy happens.

## 8. Implementation variants

Consumer-driven with a broker, the canonical Pact shape. Consumer writes
a test against a mock provider, the Pact library intercepts the calls and
serializes them into a pact file, the file is published to a broker, the
provider fetches pending contracts and verifies them with a Pact provider
verifier, results flow back to the broker, and a can-i-deploy check gates
both sides' pipelines. This is the shape documented across the Pact
ecosystem (Pact Foundation, How Pact Works, docs.pact.io, verified
2026-08-02, https://docs.pact.io/getting_started/how_pact_works).

Provider-driven contracts stored with the producer, Spring Cloud
Contract's default shape. Instead of the consumer generating the contract
from a test run, the contract is authored, often in a Groovy or YAML DSL, and
stored in the producer's own repository. The producer's build then generates
both a verification test against its real implementation and a WireMock stub
jar that consumers pull down and run against locally. This inverts who
authors the file relative to the canonical Pact flow, but the same
consumer-driven spirit survives if consumer teams are the ones raising pull
requests against the producer's contract file, which the Spring Cloud
Contract documentation explicitly recommends as a workflow (Spring Cloud
Contract Reference Documentation, section on consumer driven contracts with
contracts on the producer side, docs.spring.io, verified 2026-08-02,
https://docs.spring.io/spring-cloud-contract/reference/).

Contracts in an external, shared repository. Both consumer and provider
reference contract definitions stored in a repository neither of them owns
outright, which decouples the contract's lifecycle from either service's
deployment lifecycle. This variant trades simplicity for the operational
overhead of a third repository and an access model that decides who may
propose a contract change (Spring Cloud Contract Reference Documentation,
consumer driven contracts with contracts in an external repository,
docs.spring.io, verified 2026-08-02,
https://docs.spring.io/spring-cloud-contract/reference/).

Bi-directional contract testing, schema based rather than interaction
based. Instead of exchanging concrete request and response examples, the
consumer states which parts of a published OpenAPI or AsyncAPI schema it
actually uses, and the provider's real schema is checked for compatibility
against that subset. PactFlow introduced this as a lighter weight variant for
teams that already maintain OpenAPI specifications and do not want to hand
write interaction examples (PactFlow, Bi-Directional Contract Testing,
pactflow.io, verified 2026-08-02,
https://pactflow.io/bi-directional-contract-testing/). This variant sacrifices
some precision, a schema saying a field is a string says nothing about which
specific string values matter, in exchange for lower authoring cost and
reuse of specifications teams already maintain for other reasons.

Message-based contract testing. For asynchronous, message broker based
interactions, the contract shifts from request and response pairs to
message shape and the conditions under which a provider emits it. Pact
supports this through its message pact API, where the consumer states it can
handle a message of a given shape and the provider verifies it can produce a
message satisfying that shape, independent of the broker technology used
underneath (Pact Foundation, Asynchronous APIs, docs.pact.io, verified
2026-08-02, https://docs.pact.io/getting_started/how_pact_works#asynchronous-apis).

## 9. Known production uses

DoorDash adopted Pact to enforce compatibility between its mobile client
applications and a mobile backend-for-frontend service, applying consumer
driven contract testing specifically to reduce the coordination overhead of
keeping mobile apps and their backend in lockstep across independent release
trains (DoorDash Engineering, Contract Testing with Pact, DoorDash Engineering
Blog, verified 2026-08-02,
https://careersatdoordash.com/blog/contract-testing-with-pact/).

Atlassian used Pact contract tests alongside an OpenAPI specification so that
teams received immediate feedback in CI when a change was about to break an
API implementation, and so that consumer teams could build and rely on mocks
generated from the same specifications and Pact definitions without those
mocks diverging from the real implementation at integration time (Pact
Foundation, Case Study, Atlassian, docs.pact.io, verified 2026-08-02,
https://docs.pact.io/users/case_studies/case_study_atlassian).

REA Group, realestate.com.au, is the pattern's origin, not merely an adopter.
The Pact library itself was written there starting in 2013 during a migration
to a Ruby based microservices architecture, precisely to solve the same
brittle, slow, cross-team integration testing problem this entry describes in
dimension 2, and REA Group ran the resulting tool in production for its own
services from that point forward (Pact Foundation, History, docs.pact.io,
verified 2026-08-02, https://docs.pact.io/history).

Spring Cloud Contract, a Pivotal and later VMware and Broadcom maintained
project under the Spring umbrella, is itself evidence of production use at
scale, it exists because enough Spring based organizations needed consumer
driven contract testing integrated into the Spring Boot and Spring Cloud
ecosystem that Pivotal built and has continuously maintained a dedicated
framework for it since 2017, current stable release 5.0.3 as of this writing
(Spring Cloud Contract Reference Documentation, docs.spring.io, verified
2026-08-02, https://docs.spring.io/spring-cloud-contract/reference/).

## 10. Consequences

Positive:

- Providers gain a precise, machine-checked list of which parts of their API
  are actually depended upon, which converts the fear driven question can I
  change this field into a fact driven answer from a test result.
- Consumer and provider teams can deploy on independent schedules with a
  concrete, automated safety net instead of a synchronized release calendar,
  restoring the independent deployability that is one of the central promises
  of a microservice architecture.
- Contract tests run in milliseconds to a few seconds because they replace a
  live network call to a real, deployed dependency with a local stub or a
  local replay, which keeps CI fast even as the number of services grows.
- The contract file itself becomes living, versioned documentation of the
  actual interaction, generated from real test runs rather than hand
  maintained and prone to drifting from what the code does.
- Breaking changes are caught before a deploy, not after, because the
  can-i-deploy gate consults verification results computed ahead of time
  rather than discovering the incompatibility in production traffic.

Negative:

- A broker, or an equivalent shared repository plus process, becomes new
  infrastructure to run, monitor, and keep available, and teams that skip
  this step and only run contract tests locally lose the cross-team
  visibility that is most of the pattern's value.
- The contract only covers interactions the consumer actually exercised in
  its test, so a provider change that breaks an untested consumer code path,
  for example error handling for a status code the consumer test never
  triggered, is not caught, which is a real gap discussed further in
  dimension 11.
- Provider teams take on ongoing work implementing and maintaining provider
  state handlers so their service can be placed into the states each
  interaction assumes, which is nontrivial when interactions depend on
  complex, multi step setup.
- Consumer teams gain the power to fail a provider's build with an
  expectation the provider team never reviewed, which requires social process
  and code review discipline on contract changes, not just tooling, or it
  becomes a source of friction between teams.
- Because the pattern optimizes for interface compatibility, it gives no
  signal at all about performance, availability, or correctness of business
  logic beyond the shape of the response, teams sometimes over trust a green
  contract suite as proof the system works end to end, which it is not.

## 11. Failure modes and misuse

Symptom. A provider deploys a change that passes every contract test and
still breaks a consumer in production.
Cause. The broken code path was never exercised by any consumer's
contract, for example a specific error response, a rarely used query
parameter combination, or a field the consumer reads but never asserted on in
its test.
Fix. Extend consumer contracts to cover the paths that actually matter in
production, including negative and error cases, and periodically audit
contracts against real traffic logs to find gaps, a practice sometimes called
contract coverage review.

Symptom. The provider team routinely merges pull requests that change
contract expectations authored by the consumer team, without the consumer
team's review or knowledge.
Cause. Contracts are treated as just another test fixture that lives in
whichever repository is convenient, rather than as a cross-team agreement
requiring the consumer's sign off before it changes.
Fix. Route any change to an existing interaction through the consumer
team, either by requiring their approval on the pull request that touches the
contract file, or by having the provider team open the change as a proposed
interaction the consumer must accept and re-verify.

Symptom. CI is green, the broker's can-i-deploy check is skipped or its
failure is ignored, and an incompatible pair of versions is deployed anyway.
Cause. The deployment pipeline treats the can-i-deploy check as advisory
rather than as a hard gate, often because it was added after the deployment
pipeline already existed and nobody wired the failure to actually block the
deploy step.
Fix. Wire the can-i-deploy, or an equivalent compatibility query, as a
blocking step in the deployment pipeline itself, not merely as a status check
teams can click through.

Symptom. Teams describe their contract test suite as an integration test
suite and stop maintaining any other integration or end-to-end coverage.
Cause. A category error, treating dimension 10's positive consequences,
fast and precise interface compatibility checking, as if they also covered
dimension 17's business logic and cross-service data consistency concerns,
which contract tests were never designed to catch.
Fix. Keep a small number of genuine end-to-end or component tests for the
handful of critical business flows that span multiple services, contract
tests replace the bulk of the brittle integration layer, they do not replace
every form of integration confidence, a point Toby Clemson makes explicitly
about where contract tests sit in the pyramid relative to end-to-end tests
(Toby Clemson, Testing Strategies in a Microservice Architecture,
martinfowler.com, 18 November 2014, verified 2026-08-02,
https://martinfowler.com/articles/microservice-testing/).

Symptom. Provider verification is flaky, sometimes passing and sometimes
failing for the same contract with no code change.
Cause. Provider state setup is not properly isolated between interaction
replays, for example shared test database rows leak state across runs, or
depends on wall clock time or another form of nondeterminism.
Fix. Make provider state handlers fully own and tear down their own test
data per interaction, and remove any dependency on ambient time or ordering
between interactions.

## 12. Trade-off matrix

| Force | Consumer-Driven Contract Test | Full End-to-End Integration Test | Service Component Test with a static mock |
|---|---|---|---|
| Fidelity to real provider behavior | High for tested paths, none for untested paths | Highest, exercises the real deployed pair | None, mock behavior is whatever the author guessed |
| Speed and CI cost | Fast, runs in seconds against a local stub or replay | Slow, needs real environments and real network calls | Fast, but gives false confidence |
| Cross-team change detection | Automatic, breaking changes fail the provider's build | Automatic but noisy, failures are hard to attribute to a cause | None, drift goes unnoticed until production |
| Coordination overhead | Moderate, needs a broker and a review process on contract changes | Low day to day, high to set up and keep environments stable | Very low, but the low cost is the false confidence problem |
| Coverage of business logic across services | Low, only proves interface shape | High, exercises real logic end to end | Low, mock never encodes real logic |
| Best fit | Many services, independently deployed, willing provider team | Few critical cross-cutting flows, worth the operational cost | Never as a substitute for either of the above, only as a cheap early smoke test |

## 13. Related and incompatible patterns

Service Component Test. A component test exercises one service in
isolation with its real dependencies replaced by test doubles, and a
consumer-driven contract test is frequently used to generate or validate
those test doubles so they stay honest about what the real dependency
actually does, rather than being hand-maintained mocks that silently drift.
The two compose directly, the contract feeds the stub, the stub feeds the
component test.

API Gateway. When a gateway sits between many external consumers and
internal services, contract tests are typically written between the gateway
and each internal service it routes to, and separately between external
clients and the gateway's own public surface, treating the gateway as both a
provider, to its upstream clients, and a consumer, to the services behind it.

Remote Procedure Invocation and Messaging. Both are the interaction
styles a contract test verifies. The HTTP or gRPC request and response shape
for RPI, and the message shape plus the conditions of production for
asynchronous messaging. The pattern is agnostic to which style is used, but
the tooling and the shape of what gets captured differs meaningfully between
the two, see dimension 8's message-based variant.

Transactional Outbox. A provider that publishes domain events through an
outbox is itself a message producer, and a consumer of those events can write
a message pact against it the same way a synchronous consumer would against
an HTTP endpoint, treating the emitted event schema as the contract surface.

Incompatible with nothing structurally, but it is not a substitute for,
and should never be presented as replacing, a full end-to-end test of the
critical handful of cross-service business flows an organization genuinely
cannot afford to get wrong, see dimension 11's misuse pattern about treating
contract tests as sufficient integration coverage on their own.

## 14. Refactoring path in and out

Introducing the pattern into a codebase that has none, step by step.

1. Pick one consumer-to-provider relationship that has recently caused a
   production incident or a painful, manually coordinated deploy, this gives
   the pilot immediate, visible payoff rather than an abstract exercise.
2. In the consumer's codebase, write a test against the real client code the
   consumer already uses, backed by a Pact, or equivalent, mock provider,
   asserting on the one or two interactions that actually matter for the
   incident or the coordination pain identified in step 1.
3. Run that test, inspect the generated contract file, and commit it, or
   publish it to a broker if one is already available, this is the point
   where the practice becomes visible outside the consumer team.
4. On the provider side, add a verification step to the provider's own build
   that fetches the contract and replays it, implementing whatever minimal
   provider state setup the one or two interactions require.
5. Once the loop works for one pair, wire a can-i-deploy check into both
   sides' deployment pipelines as a blocking step, not yet for every service,
   just for this pair, to prove the end-to-end safety net actually works
   before generalizing it.
6. Expand outward, relationship by relationship, prioritizing pairs with a
   history of breakage or with independent deployment cadences, rather than
   attempting a big-bang rollout across every service in the organization at once.

Removing the pattern when it stops earning its place, for example two
services are merged, or a consumer is deprecated.

1. Confirm in the broker, or the shared contract repository, that no active
   consumer version still depends on the interactions in question, using the
   broker's own relationship queries rather than trusting memory or a wiki
   page.
2. Delete the consumer test and its generated contract from the consumer's
   codebase, and delete the corresponding provider verification step and any
   provider state handlers that exist solely to serve that contract.
3. Remove the now-unused contract from the broker so stale, orphaned pacts do
   not accumulate and confuse future can-i-deploy queries, most broker
   implementations expose a way to explicitly retire or delete a pacticipant
   relationship.

## 15. Testing and verification

Testing and verification is largely what this pattern is, so this dimension
covers how to test the contract testing setup itself, which is a real,
separate concern from the interactions the contracts describe.

What becomes easy because of this pattern is testing the consumer's client
code against a stable, versioned expectation of the provider, without ever
standing up the provider, which means the consumer's test suite can be fully
hermetic and can run offline, in parallel, and without flakiness introduced
by a shared test environment.

What becomes harder is reasoning about end-to-end correctness across a chain
of more than two services, because each contract only proves a single hop is
compatible, a chain of three services each individually compatible with its
immediate neighbor can still fail to satisfy a business invariant that spans
all three, which is exactly the gap component and end-to-end tests exist to
close, as covered in dimension 13.

The test double that matters most here is the provider verifier itself
running against a genuinely real, running instance of the provider, not a
second layer of mocking. A common mistake is verifying the provider's
contract against a mocked-out version of the provider's own internals, which
defeats the purpose entirely, because it no longer proves the real code
honors the contract, only that a second hand-maintained approximation does.

For the broker relationship itself, the can-i-deploy query, treat it as
something to test in a staging or sandbox instance of the broker before
relying on it in a real deployment pipeline, deliberately publishing an
incompatible pair of versions and confirming the query correctly reports
them as unsafe to deploy together, the same way any safety mechanism deserves
a test that proves it actually fails closed.

## 16. Observability signals

Log and expose, per consumer to provider relationship.

- The number of interactions in the current contract, and its trend over
  time, a sudden drop can indicate a consumer accidentally deleted coverage
  rather than intentionally simplified its expectations.
- The timestamp and result of the last provider verification run for each
  consumer version, stale verification results, for example a contract
  published two weeks ago that the provider has never verified, is a signal
  the cross-team feedback loop has broken down.
- The can-i-deploy decision and its reasoning at every deploy attempt,
  including which specific consumer or provider version made a deploy unsafe,
  this turns a blocked deploy from a confusing red X into an actionable,
  named incompatibility.
- Contract verification duration, a provider verification step that has crept
  from seconds to minutes usually means provider state setup has grown
  unwieldy and needs attention before it becomes a CI bottleneck teams route
  around.

A healthy dashboard shows every active consumer to provider pair with a
recent, passing verification result and a green can-i-deploy status for the
versions currently running in production. A failing instance shows either a
red verification result that has not been acted on, or, more dangerously, no
recent verification at all, meaning the loop has silently stopped running
rather than actively failed, which is easy to miss without an explicit
staleness alert.

## 17. Security and privacy implications

Contract files, and the broker that stores them, contain concrete example
request and response payloads, which means field names, plausible data
shapes, and sometimes literal example values from a real domain, order
identifiers, customer identifiers, internal status enumerations. If contract
authors are not deliberate about using synthetic, clearly fake example data,
a contract can leak the shape of internal data models, and occasionally
actual sensitive values copied in from a debugging session, to anyone with
read access to the broker.

Because the broker becomes a shared, cross-team dependency that many
pipelines authenticate against to publish and fetch contracts, its access
tokens are a meaningful piece of attack surface, a leaked broker token can
allow an attacker to read every team's interface contracts, which is a
detailed map of internal service topology and data shapes, or to publish a
malicious verification result that could influence a can-i-deploy decision if
the broker's trust model is not carefully scoped per pacticipant.

This entry does not identify any implication specific to the pattern beyond
the general concerns above, which apply to shared internal tooling broadly.
There is no known privacy regulation implication distinct from whatever
applies to the underlying data the interactions themselves carry.

## 18. References

1. Ian Robinson, Consumer-Driven Contracts, A Service Evolution Pattern,
   martinfowler.com, 12 June 2006, verified 2026-08-02,
   https://martinfowler.com/articles/consumerDrivenContracts.html
2. Pact Foundation, History, docs.pact.io, verified 2026-08-02,
   https://docs.pact.io/history
3. Pact Foundation, How Pact Works, docs.pact.io, verified 2026-08-02,
   https://docs.pact.io/getting_started/how_pact_works
4. Pact Foundation, Pact Broker, docs.pact.io, verified 2026-08-02,
   https://docs.pact.io/pact_broker
5. Pact Foundation, Case Study, Atlassian, docs.pact.io, verified 2026-08-02,
   https://docs.pact.io/users/case_studies/case_study_atlassian
6. DoorDash Engineering, Contract Testing with Pact, DoorDash Engineering
   Blog, verified 2026-08-02,
   https://careersatdoordash.com/blog/contract-testing-with-pact/
7. PactFlow, Bi-Directional Contract Testing, pactflow.io, verified
   2026-08-02, https://pactflow.io/bi-directional-contract-testing/
8. Spring Cloud Contract Reference Documentation, docs.spring.io, verified
   2026-08-02, https://docs.spring.io/spring-cloud-contract/reference/
9. Sam Newman, Building Microservices, 2nd edition, O'Reilly, 2021, chapter
   1, pages 6 to 9, and chapter 9, pages 316 to 328.
10. Toby Clemson, Testing Strategies in a Microservice Architecture,
    martinfowler.com, 18 November 2014, verified 2026-08-02,
    https://martinfowler.com/articles/microservice-testing/

## Code examples

Three languages, each a self-contained, dependency-free consumer-driven
contract test. Each starts a local stub HTTP server shaped by a hand written
contract, drives real consumer client code against it, asserts the response
matches expectations, then serializes the contract, mirroring what a real
Pact-style consumer test does without requiring an external library or
network access to run in this environment. Provider verification is the same
shape in reverse, replay the same interaction against a real provider
instance, which is omitted here because it requires a running provider
process, the structure is described fully in dimensions 6 and 7.

C#, Kotlin, and Rust are omitted here. Rust's toolchain was present but the
pattern's idiomatic expression is materially identical to the Go example
above, a typed struct plus an httptest-style local server, so a third
imperative, statically typed example added no new teaching value against the
6000 to 9000 word budget. C# and Kotlin were not available to compile in this
environment and are not claimed to have been run.

### TypeScript

```typescript
import * as http from "http";
import { AddressInfo } from "net";

interface Interaction {
  description: string;
  request: { method: string; path: string };
  response: { status: number; body: Record<string, unknown> };
}

interface Contract {
  consumer: string;
  provider: string;
  interactions: Interaction[];
}

interface OrderStatus {
  orderId: string;
  status: string;
}

class OrderServiceClient {
  constructor(private readonly baseUrl: string) {}

  fetchOrderStatus(orderId: string): Promise<OrderStatus> {
    return new Promise((resolve, reject) => {
      http.get(`${this.baseUrl}/orders/${orderId}/status`, (res) => {
        let raw = "";
        res.on("data", (chunk) => (raw += chunk));
        res.on("end", () => {
          try {
            resolve(JSON.parse(raw) as OrderStatus);
          } catch (err) {
            reject(err);
          }
        });
      }).on("error", reject);
    });
  }
}

function startStub(interaction: Interaction): Promise<{ server: http.Server; port: number }> {
  const server = http.createServer((req, res) => {
    if (req.url !== interaction.request.path) {
      res.writeHead(404);
      res.end();
      return;
    }
    res.writeHead(interaction.response.status, { "Content-Type": "application/json" });
    res.end(JSON.stringify(interaction.response.body));
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address() as AddressInfo;
      resolve({ server, port });
    });
  });
}

async function runConsumerContractTest(): Promise<void> {
  const interaction: Interaction = {
    description: "a request for the status of order 42",
    request: { method: "GET", path: "/orders/42/status" },
    response: { status: 200, body: { orderId: "42", status: "SHIPPED" } },
  };

  const { server, port } = await startStub(interaction);
  const client = new OrderServiceClient(`http://127.0.0.1:${port}`);
  const result = await client.fetchOrderStatus("42");
  server.close();

  if (result.orderId !== "42" || result.status !== "SHIPPED") {
    throw new Error(`unexpected result: ${JSON.stringify(result)}`);
  }

  const contract: Contract = {
    consumer: "web-storefront",
    provider: "order-service",
    interactions: [interaction],
  };
  const pactJson = JSON.stringify(contract, null, 2);
  if (!pactJson.includes("order-service")) {
    throw new Error("contract missing provider name");
  }

  console.log("consumer contract test passed");
}

runConsumerContractTest().catch((err) => {
  console.error(err);
  process.exit(1);
});
```

Compiled with tsc, target es2020, module commonjs, against types node,
and run with node. Output confirmed consumer contract test passed.

### Python

```python
"""Consumer-driven contract test. Stdlib only, no external deps."""
import http.server
import json
import socketserver
import threading
import time
import unittest
import urllib.request
from dataclasses import dataclass, field


@dataclass
class Interaction:
    description: str
    request: dict
    response: dict


@dataclass
class Contract:
    consumer: str
    provider: str
    interactions: list = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(
            {
                "consumer": {"name": self.consumer},
                "provider": {"name": self.provider},
                "interactions": [i.__dict__ for i in self.interactions],
            },
            indent=2,
        )


class OrderServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def fetch_order_status(self, order_id: str) -> dict:
        req = urllib.request.Request(f"{self.base_url}/orders/{order_id}/status")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return json.loads(resp.read().decode("utf-8"))


def _make_stub_handler(interaction: Interaction):
    class StubHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            expected_path = interaction.request["path"]
            if self.path != expected_path:
                self.send_response(404)
                self.end_headers()
                return
            body = json.dumps(interaction.response["body"]).encode("utf-8")
            self.send_response(interaction.response["status"])
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            return

    return StubHandler


class ConsumerContractTest(unittest.TestCase):
    def test_fetch_order_status_matches_contract(self):
        interaction = Interaction(
            description="a request for the status of order 42",
            request={"method": "GET", "path": "/orders/42/status"},
            response={
                "status": 200,
                "body": {"orderId": "42", "status": "SHIPPED"},
            },
        )

        handler = _make_stub_handler(interaction)
        with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
            port = httpd.server_address[1]
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            time.sleep(0.05)

            client = OrderServiceClient(f"http://127.0.0.1:{port}")
            result = client.fetch_order_status("42")

            httpd.shutdown()

        self.assertEqual(result["orderId"], "42")
        self.assertEqual(result["status"], "SHIPPED")

        contract = Contract(
            consumer="web-storefront", provider="order-service", interactions=[interaction]
        )
        pact_json = contract.to_json()
        self.assertIn('"consumer"', pact_json)
        self.assertIn('"order-service"', pact_json)


if __name__ == "__main__":
    unittest.main()
```

Run with python3 -m unittest. Output confirmed one test, ok.

### Go

```go
package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

type Interaction struct {
	Description string       `json:"description"`
	Request     RequestPart  `json:"request"`
	Response    ResponsePart `json:"response"`
}

type RequestPart struct {
	Method string `json:"method"`
	Path   string `json:"path"`
}

type ResponsePart struct {
	Status int                    `json:"status"`
	Body   map[string]interface{} `json:"body"`
}

type Contract struct {
	Consumer     string        `json:"consumer"`
	Provider     string        `json:"provider"`
	Interactions []Interaction `json:"interactions"`
}

type OrderStatus struct {
	OrderID string `json:"orderId"`
	Status  string `json:"status"`
}

func fetchOrderStatus(baseURL, orderID string) (*OrderStatus, error) {
	resp, err := http.Get(baseURL + "/orders/" + orderID + "/status")
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	var out OrderStatus
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, err
	}
	return &out, nil
}

func TestConsumerContract_OrderStatus(t *testing.T) {
	interaction := Interaction{
		Description: "a request for the status of order 42",
		Request:     RequestPart{Method: "GET", Path: "/orders/42/status"},
		Response: ResponsePart{
			Status: 200,
			Body:   map[string]interface{}{"orderId": "42", "status": "SHIPPED"},
		},
	}

	stub := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != interaction.Request.Path {
			w.WriteHeader(http.StatusNotFound)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(interaction.Response.Status)
		json.NewEncoder(w).Encode(interaction.Response.Body)
	}))
	defer stub.Close()

	result, err := fetchOrderStatus(stub.URL, "42")
	if err != nil {
		t.Fatalf("consumer client call failed: %v", err)
	}
	if result.OrderID != "42" || result.Status != "SHIPPED" {
		t.Fatalf("unexpected result: %+v", result)
	}

	contract := Contract{
		Consumer:     "web-storefront",
		Provider:     "order-service",
		Interactions: []Interaction{interaction},
	}
	out, err := json.MarshalIndent(contract, "", "  ")
	if err != nil {
		t.Fatalf("failed to marshal contract: %v", err)
	}
	if len(out) == 0 {
		t.Fatal("empty contract output")
	}
}
```

Run with go test ./.... Output confirmed PASS.
