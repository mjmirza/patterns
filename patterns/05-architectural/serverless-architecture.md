---
name: Serverless Architecture
slug: serverless-architecture
family: 05-architectural
category: Architectural
aliases: [Function as a Service Architecture, FaaS Architecture, Serverless Compute]
first_described: "Roberts 2018 (term definition); commercial origin AWS Lambda, launched 2014"
maturity: established
related: [event-driven-architecture, microservices, hexagonal-architecture, pipes-and-filters, cqrs]
incompatible_with: [monolithic-architecture]
verified: 2026-08-02
---

# Serverless Architecture

## 1. Name, aliases, and lineage

The canonical name is Serverless Architecture. The term is a misnomer that stuck.
Servers still run the code, the difference is that the team writing the code
never provisions, patches, or scales one. The most cited definition of the term
comes from Mike Roberts, published as "Serverless Architectures" on
martinfowler.com, an article he first wrote in 2016 and revised through 2018.
Roberts defines serverless as application designs that combine third-party
Backend as a Service (BaaS) offerings with custom code that runs in managed,
short-lived containers on Functions as a Service (FaaS) platforms
([Roberts, "Serverless Architectures", martinfowler.com](https://martinfowler.com/articles/serverless.html),
verified 2026-08-02).

Two aliases are common and both point at only half of what the pattern
describes. **Function as a Service Architecture** or **FaaS Architecture**
names the compute half, the individual, independently deployed function that
runs in response to a trigger. **Backend as a Service Architecture** names the
managed-dependency half, a hosted database, an auth provider, a message queue,
consumed as a service rather than operated by the team. Roberts's article
treats FaaS and BaaS as the two ingredients of the same architectural style,
not as competing definitions, and that framing is the one this entry follows.

The commercial origin of FaaS is AWS Lambda, launched at the re Invent conference in November
2014. AWS's own product documentation still opens with the plain description,
Lambda is "a serverless compute service" that lets a team "run code without
provisioning or managing servers"
([AWS, "What is AWS Lambda?"](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html),
verified 2026-08-02). Google Cloud Functions and Azure Functions followed
within two years, and by 2018 every major public cloud had a FaaS product,
which is roughly when the architectural pattern, as distinct from the product
category, was formalized in writing.

A naming trap worth flagging early. "Serverless" is sometimes used loosely to
mean "any managed cloud service", stretching to cover managed Kubernetes or
managed databases that still require capacity planning. This entry restricts
the term to its FaaS-plus-BaaS meaning, the unit of deployment is a stateless
function or a managed service, and the unit of billing is consumption, not a
reserved instance.

## 2. Problem and context

A team owns a backend that must handle a workload with two properties that are
hard to satisfy at once with a conventional server fleet, the load is spiky or
unpredictable, and much of the time nobody is calling the service at all.

The situation reads like this in an operations review. A team runs three
EC2 instances, or a small Kubernetes deployment, sized for the ninety-fifth
percentile of daily traffic. Nine hours a day the fleet sits near idle,
because the workload is a webhook handler, a nightly batch job, an image
resize triggered by an upload, or an internal tool five people use twice a
week. The team pays for capacity around the clock to cover load that arrives
in short, uneven bursts, and every one of those instances still needs patching,
an AMI rebuild pipeline, and an on-call rotation for a process that spends most
of its life doing nothing.

The second half of the context is organizational, not technical. The team is
small relative to the number of discrete, independent tasks the backend must
do, resize an image, verify a webhook signature, send a transactional email,
run a nightly reconciliation. Each task is naturally an isolated unit of work
with no shared runtime state, and standing up a dedicated, always-on service
for each one is disproportionate to the actual compute involved.

Serverless architecture is the response, the unit of deployment shrinks to a
single function bound to a trigger event, and the unit of billing shrinks to
the actual invocation, usually metered in milliseconds of execution and
number of requests. The platform, not the team, decides when to create an
execution environment, how many to run in parallel, and when to tear one down.

The context that makes this the right answer has three parts, each one
necessary. First, the workload is genuinely event-driven or bursty rather than
a steady stream that would keep a server fleet near capacity anyway, in which
case the per-invocation billing model does not beat a reserved instance.
Second, each unit of work can complete inside the platform's execution time
limit, fifteen minutes for AWS Lambda functions as of this writing
([AWS, "What is AWS Lambda?"](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html),
verified 2026-08-02), and does not depend on long-lived in-process state such
as an open WebSocket held for hours. Third, the team is willing to trade some
control over the runtime, the exact CPU, network placement, and startup path,
for the platform absorbing patching, capacity, and horizontal scaling.

## 3. Forces

The pattern balances the following competing pressures. This dimension is
partly judgement, weighing which pressure matters most for a given workload
shape, and it is labeled as such where the weighing is not a fact anyone could
independently check.

- **Operational burden.** Strongly favoured. No server to patch, no fleet to
  size, no AMI pipeline. The platform vendor absorbs the operating system and
  the runtime patching. This is the single largest reason the pattern spread.
- **Cost at low or spiky utilization.** Favoured. Billing by invocation and
  execution time means an idle period costs close to nothing, which reverses
  the economics of a reserved fleet sized for a peak that arrives rarely.
- **Cost at sustained high utilization.** Sacrificed, and this is judgement
  drawn from how the billing model is structured rather than a cited figure.
  A function invoked continuously at high volume, for long durations, tends to
  cost more per unit of compute than a right-sized reserved instance or a
  container running the same code, because the per-invocation and per-GB-second
  pricing carries a margin the platform is not obligated to pass along at
  scale. Teams running Lambda at sustained volume commonly move the hot path to
  a container or a reserved-capacity service once the invocation count
  justifies the migration effort.
- **Latency for the first request.** Sacrificed. An execution environment that
  is not already warm must be created before the function can run, which is
  the cold start, discussed in detail in dimension 11. AWS states cold starts
  occur in under one percent of invocations under steady, moderate load, with
  durations from under 100 milliseconds to over one second depending on
  runtime and package size
  ([AWS Compute Blog, "Operating Lambda, Performance optimization"](https://aws.amazon.com/blogs/compute/operating-lambda-performance-optimization-part-1/),
  verified 2026-08-02), but the one percent figure is a steady-state average,
  not a guarantee, and traffic spikes or deployments raise it.
- **Vendor lock-in.** Sacrificed. Roberts's article is explicit that
  migrating a Lambda-based system to Google Cloud Functions means rewriting
  operational tooling and, in practice, redesigning around a different set of
  triggers and integrated services, not merely swapping a runtime
  ([Roberts, "Serverless Architectures"](https://martinfowler.com/articles/serverless.html),
  verified 2026-08-02). The BaaS half of the pattern deepens this further,
  because a managed queue, a managed database with a vendor-specific query
  model, and a managed auth provider are each their own migration cost.
- **Testability.** Sacrificed, per Roberts. Unit testing an individual function
  is straightforward, but integration testing against real BaaS dependencies is
  hard, because those services resist local stubbing and the cloud environment
  used for integration testing diverges from the local development environment
  ([Roberts, "Serverless Architectures"](https://martinfowler.com/articles/serverless.html),
  verified 2026-08-02).
- **Elasticity.** Strongly favoured. The platform creates as many concurrent
  execution environments as concurrent invocations demand, with no capacity
  plan required in advance. This is the property that lets serverless absorb a
  thirty-times traffic spike with no pre-provisioning, a pattern seen in
  production (dimension 9).
- **Observability continuity.** Sacrificed. A request that fans out across a
  dozen short-lived functions, a queue, and two managed services produces a
  trace that spans processes with no shared memory and often no shared clock
  source at sub-millisecond resolution, which is harder to reconstruct than a
  single process's call stack.
- **Local development fidelity.** Sacrificed. A local emulator for a FaaS
  platform is an approximation of the cloud execution environment, never an
  exact match, so "works locally" carries less assurance than it does for a
  conventionally deployed service.

## 4. Applicability and non-applicability

Reach for serverless architecture when the following hold.

- The workload is event-driven, an HTTP request, a file landing in storage, a
  message on a queue, a scheduled tick, a database change stream.
- Traffic is bursty, unpredictable, or has long idle periods, so paying for
  reserved always-on capacity would waste money most of the time.
- Each unit of work is short, bounded well inside the platform's maximum
  execution duration, and does not depend on multi-request in-memory state.
- The team wants to add capacity to a new integration point, a webhook, a
  cron job, an image pipeline, without standing up and operating a new
  service.
- The organization already accepts a managed-cloud operating model and values
  removing patch and capacity management over retaining full runtime control.
- Rapid, small, independently deployable units of change are wanted, and the
  team can tolerate per-function deployment and versioning rather than one
  atomic service deployment.

Do NOT reach for serverless architecture in these cases, and the reason
matters more than the rule.

- **The workload is a steady, high-volume, long-running process.** A stream
  processor consuming a constant high message rate for hours at a time, or a
  service handling continuous, predictable production traffic, tends to cost
  more on a per-invocation FaaS billing model than on a right-sized container
  or reserved instance running the same code, once utilization is high and
  sustained. Reach for containers on a managed orchestrator instead.
- **The unit of work genuinely needs long-lived, in-process state.** A
  real-time multiplayer game server holding room state in memory, a database
  connection pool meant to be shared across thousands of requests per second
  with sub-millisecond reuse, or a long-running WebSocket session held open for
  hours does not fit a model built around short-lived, stateless execution
  environments. BaaS-managed WebSocket gateways exist and route to short-lived
  functions per message, but the persistent connection itself is not the FaaS
  function, conflating the two produces the state-loss bugs in dimension 11.
- **Latency must be predictable in the single-digit millisecond range on every
  request, including the first one after a deploy or a scale-out event.** Cold
  starts, even at AWS's stated sub-one-percent steady-state rate, are not zero,
  and a workload with a hard tail-latency SLA needs either Provisioned
  Concurrency (dimension 8) paid for as a reserved cost, defeating some of the
  cost argument, or a conventionally warm service.
- **The team needs full control over the runtime, the operating system, or
  specialized hardware.** GPU-bound machine learning inference at high volume, code
  requiring a kernel module, or a workload tied to a specific CPU
  microarchitecture is a poor fit for a platform that abstracts the machine
  away entirely.
- **Vendor neutrality is a hard organizational requirement.** A regulated
  environment or a contractual obligation to remain portable across clouds
  makes the FaaS-plus-BaaS coupling described in dimension 3 a liability, not a
  convenience. A container running on any Kubernetes cluster is more portable
  than a Lambda function wired to six other AWS-managed services.
- **The domain logic is one large, cohesive unit that would only be split
  along function boundaries for the sake of fitting the pattern.** Splitting a
  transactional workflow that must complete atomically across a dozen small
  functions coordinated by a queue turns a single-process problem into a
  distributed-systems problem, trading a stack trace for a trace collector.

## 5. Structure

Serverless architecture has five participants, named by the role each plays,
not by a product name, because the roles map onto different concrete services
depending on the cloud provider.

- **Trigger.** The event source that causes a function to run, an API
  gateway routing an HTTP request, an object-storage bucket notifying on a new
  file, a message queue delivering a batch, a scheduler firing on a cron
  expression, a database change stream, or a direct SDK invocation. The
  trigger decides invocation shape, synchronous request-response, or
  asynchronous fire-and-forget with retry semantics owned by the platform.
- **Function.** The unit of custom, stateless business logic. It receives an
  event payload and a context object, does its work, and returns a result or
  produces a side effect. It holds no reliable state between invocations
  beyond what the platform happens to reuse opportunistically in a warm
  execution environment (dimension 7).
- **Execution environment.** The platform-managed sandbox a function runs
  inside. Created on demand, torn down after a period of inactivity, and never
  guaranteed to be reused for the next invocation. AWS Lambda functions run
  inside Firecracker microVMs
  ([AWS, "What is AWS Lambda?"](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html),
  verified 2026-08-02), Cloudflare Workers run inside V8 isolates within a
  shared process rather than a per-request virtual machine
  ([Cloudflare Workers docs, "How Workers works"](https://developers.cloudflare.com/workers/reference/how-workers-works/),
  verified 2026-08-02). The isolation mechanism differs by platform, and it is
  the single biggest influence on cold start cost, discussed in dimension 11.
- **Managed backend service (BaaS).** A stateful dependency the function
  reads from or writes to but does not itself run, a managed database, an
  object store, a managed queue, a managed authentication provider. The
  function stays stateless precisely because durable state lives here instead.
- **Orchestrator or event bus.** The optional participant that chains
  functions together into a workflow, either by publishing an event one
  function's output triggers another function's input, or through a dedicated
  state-machine service that sequences steps and owns the workflow's own
  durable state so no single function has to.

Relationships. The Trigger invokes the Function, and only the Trigger, a
client never calls a Function directly except through whatever gateway is
acting as the Trigger for that path. The Function depends on zero or more
BaaS services for anything durable, and never assumes another invocation of
itself will see state left in memory. The Orchestrator, where present, depends
on Functions as its steps and treats each one as a black box that receives
input and returns output or fails.

## 6. ASCII structure diagram

```
+---------------------------------------+
| Trigger                               |
| API Gateway, Queue, Bucket, Scheduler |
+---------------------------------------+
           | invokes
           v
+----------------------------------------+
| Execution Environment                  |
| created on demand, torn down when idle |
|                                        |
|   Function (stateless logic)           |
+----------------------------------------+
           | reads / writes
           v
+----------------------+
| Managed Queue (BaaS) |
+----------------------+
+-------------------------+
| Managed Database (BaaS) |
+-------------------------+
+------------------------+
| Managed Storage (BaaS) |
+------------------------+

Orchestrator, a state machine or event bus, sequences
several Functions, each one independently triggered, none
holding the workflow's state.
```

## 7. Dynamics

The dynamics differ sharply depending on whether the execution environment is
warm or must be created from nothing, and the sequence below shows both paths
for the same synchronous, gateway-triggered invocation.

```
Client        Trigger (Gateway)     Platform          Execution Env      Function      BaaS
  |                  |                  |                    |              |           |
  |-- HTTP request ->|                  |                    |              |           |
  |                  |-- route event -->|                    |              |           |
  |                  |                  |                    |              |           |
  |                  |         [ COLD PATH: no warm env exists ]            |           |
  |                  |                  |-- create sandbox ->|              |           |
  |                  |                  |   (download code,  |              |           |
  |                  |                  |    start runtime,  |              |           |
  |                  |                  |    run init code)  |              |           |
  |                  |                  |<-- env ready ------|              |           |
  |                  |                  |                    |-- invoke() ->|           |
  |                  |                  |                    |              |-- I/O --->|
  |                  |                  |                    |              |<-- data ---|
  |                  |                  |                    |<-- result ---|           |
  |                  |<-- response -----|<-------------------|              |           |
  |<-- HTTP 200 -----|                  |                    |              |           |
  |                  |                  |                    |              |           |
  |                  |         [ WARM PATH: env reused for the next call ]  |           |
  |-- HTTP request ->|                  |                    |              |           |
  |                  |-- route event -->|-- invoke() ------->|-- invoke() ->|           |
  |                  |                  |   (env already up, init already ran)|         |
  |                  |                  |                    |              |-- I/O --->|
  |                  |                  |                    |              |<-- data ---|
  |                  |                  |                    |<-- result ---|           |
  |                  |<-- response -----|<-------------------|              |           |
  |<-- HTTP 200 -----|                  |                    |              |           |
```

Three properties worth naming explicitly. First, the platform, not the
function's code, decides whether a given invocation lands on a warm or a cold
environment, and code cannot force a warm path except by influencing how
likely one is to be available (dimension 8). Second, module-level or
global-scope initialization, opening a database connection, constructing an
HTTP client, runs once per execution environment and is reused by every
warm invocation on that environment, which is exactly the mechanism the code
examples in this entry demonstrate and measure. Third, two concurrent
invocations never share an execution environment, the platform creates a
second environment rather than queuing the second request behind the first,
which is what makes the model horizontally elastic and is also why in-memory
state cannot be relied on for coordination between concurrent calls.

## 8. Implementation variants

**Bare FaaS function behind an API gateway.** The simplest form, one function
per route or per event type, deployed independently, triggered by a managed
gateway that handles routing, throttling, and authentication before the
function ever runs. This is the shape most tutorials show and the one that
scales cleanly to dozens of small, independent endpoints.

**Monolithic function, sometimes called a "Lambdalith".** A single function
containing an entire application's routing logic internally, deployed as one
unit behind one gateway route that forwards every request to it. This trades
away the independent-deployment benefit of many small functions in exchange
for a single deployment artifact, a single cold start to warm rather than
many, and one dependency graph rather than dozens duplicated across
functions. It is a deliberate middle ground between serverless and a
conventional monolith, and is common when a team wants the operational model
of serverless without the proliferation of tiny deployable units.

**Provisioned or reserved concurrency.** The platform keeps a specified number
of execution environments warm and ready ahead of demand, at a reserved cost,
specifically to eliminate cold-start latency for the paths that keep them
warm. AWS documents this as returning "double-digit millisecond" response
times because initialization already ran
([AWS Compute Blog, "Operating Lambda, Performance optimization"](https://aws.amazon.com/blogs/compute/operating-lambda-performance-optimization-part-1/),
verified 2026-08-02). This variant reintroduces a minimum reserved cost, which
is judgement worth stating plainly, it is the point at which serverless
billing starts to resemble the always-on model it was adopted to avoid, scoped
down to only the paths that need it.

**Snapshot-restore cold start elimination.** Rather than reserving warm
capacity ahead of time, the platform pre-initializes an environment once,
freezes a snapshot of its memory and disk state, and restores from that
snapshot on future cold starts instead of re-running initialization from
scratch. AWS Lambda SnapStart for Java functions is the documented example,
AWS reports a benchmark where p99.9 latency fell from 5,114 milliseconds
without SnapStart to 488 milliseconds with it, describing the feature as "up
to 10x faster function startup" at no additional cost
([AWS Compute Blog, "Reducing Java cold starts on AWS Lambda functions with SnapStart"](https://aws.amazon.com/blogs/compute/reducing-java-cold-starts-on-aws-lambda-functions-with-snapstart/),
verified 2026-08-02). This variant addresses cold starts without paying for
idle reserved capacity, at the cost of platform and runtime-specific
eligibility.

**Isolate-based execution instead of per-invocation virtual machines.**
Cloudflare Workers runs many isolated scripts inside one already-running
process rather than starting a fresh container or virtual machine per
function. Cloudflare's own documentation states an isolate "can start around a
hundred times faster than a Node process on a container or virtual machine"
and consumes "an order of magnitude less memory" at startup
([Cloudflare Workers docs, "How Workers works"](https://developers.cloudflare.com/workers/reference/how-workers-works/),
verified 2026-08-02). This variant changes the isolation primitive itself
rather than adding a warming mechanism on top of a VM-per-invocation model,
and it trades some of the strong VM-level isolation guarantees of Firecracker
for near-elimination of cold start cost.

**Durable, long-lived function sessions.** Some platforms now offer a compute
primitive positioned between a short FaaS invocation and a fully operated
server, an isolated environment that persists state across a session lasting
hours rather than milliseconds, suspending and resuming on demand. AWS
documents this as Lambda MicroVMs, distinct from Lambda Functions, explicitly
for workloads needing a dedicated, stateful environment per user or job rather
than a stateless, per-request one
([AWS, "What is AWS Lambda?"](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html),
verified 2026-08-02). This is not classical FaaS, and naming the distinction
matters, it is the platform vendor acknowledging that the applicability
boundary in dimension 4, no long-lived state, excludes a real class of
workload, and building a separate primitive for it rather than stretching
FaaS to cover it.

**Orchestrated workflow via a managed state machine.** Rather than chaining
functions through an ad hoc event bus, a dedicated orchestration service
sequences function invocations, retries a failed step, and owns the
workflow's durable state itself, so no individual function has to track where
the overall process stands. This is the serverless-native answer to the
long-running-workflow limitation in dimension 4, at the cost of the workflow
definition becoming a first-class artifact the team must design and version
alongside the functions it calls.

## 9. Known production uses

**Thomson Reuters.** A serverless data-processing pipeline built on AWS
processes "up to 4,000 events per second" and was brought from design to
production in five months
([AWS, Lambda customer case studies index](https://aws.amazon.com/lambda/resources/customer-case-studies/),
verified 2026-08-02).

**iRobot.** Runs its connected-device platform, coordinating IoT telemetry
from millions of home robots, on AWS Lambda and related managed services with
a platform team of fewer than ten people
([AWS, Lambda customer case studies index](https://aws.amazon.com/lambda/resources/customer-case-studies/),
verified 2026-08-02).

**Financial Industry Regulatory Authority (FINRA).** Uses AWS Lambda to
analyze roughly 75 billion market events every day as part of its fraud and
insider-trading detection pipeline
([AWS, Lambda customer case studies index](https://aws.amazon.com/lambda/resources/customer-case-studies/),
verified 2026-08-02). This is the clearest example in the public record of
serverless applied to a high-volume, latency-tolerant batch analytics
workload rather than a low-latency request path.

**Square Enix.** Moved an image-processing pipeline to a serverless
architecture and reports the processing time for a single image dropping from
several hours to close to 10 seconds, while the system absorbed traffic
spikes of up to 30 times normal load with no manual capacity planning
([AWS, Lambda customer case studies index](https://aws.amazon.com/lambda/resources/customer-case-studies/),
verified 2026-08-02). This is a concrete demonstration of the elasticity force
from dimension 3 turning into a measured outcome, not only a theoretical
property.

**Financial Engines.** Operates a serverless system handling request rates of
up to 60,000 per minute with the vendor reporting zero downtime attributable
to the architecture
([AWS, Lambda customer case studies index](https://aws.amazon.com/lambda/resources/customer-case-studies/),
verified 2026-08-02).

**Bustle.** Runs its entire production website on a serverless architecture,
serving high-volume traffic with no conventionally provisioned application
server in the request path
([AWS, Lambda customer case studies index](https://aws.amazon.com/lambda/resources/customer-case-studies/),
verified 2026-08-02).

**T-Mobile.** Adopted a stated "serverless first" internal policy and runs
critical, revenue-bearing applications on the pattern rather than treating it as a
side project for low-stakes internal tools
([AWS, Lambda customer case studies index](https://aws.amazon.com/lambda/resources/customer-case-studies/),
verified 2026-08-02). A named "serverless first" policy at a large
telecommunications carrier is notable in this catalog as evidence the pattern
graduated from an experimental adjunct to a default architectural choice for
at least one large regulated organization.

A caution about the source class for this dimension. Every case study cited
above comes from a single vendor's own case-study index, which is a real,
citable, checkable source, but it is also a marketing artifact selected by
that vendor to show its product favourably. None of the figures above have an
independent, non-vendor confirmation in the sources checked for this entry.
Treat the numbers as the vendor's own reported outcomes, not as independently
audited figures, and weigh that when using them to justify an architectural
decision.

## 10. Consequences

Positive.

- Idle time costs close to nothing, because billing follows invocation and
  execution time rather than a reserved, always-running instance.
- The team never patches an operating system, builds an AMI, or plans server
  capacity for the compute layer, the platform absorbs that work entirely.
- Individual functions scale independently and automatically to match
  concurrent demand, with no capacity plan required in advance, which is the
  property behind the Square Enix thirty-times-spike outcome above.
- Small, independent units of deployment let a team add a new integration
  point, a webhook handler, a scheduled job, without touching or redeploying
  an existing service.
- Firecracker-based isolation gives each Lambda execution environment
  VM-level separation from every other, which is a strong security boundary
  compared to sharing a process or a container runtime across tenants
  ([AWS, "What is AWS Lambda?"](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html),
  verified 2026-08-02).

Negative.

- The first invocation into a fresh execution environment pays a cold-start
  penalty that ranges from under 100 milliseconds to over one second depending
  on runtime and package size
  ([AWS Compute Blog, "Operating Lambda, Performance optimization"](https://aws.amazon.com/blogs/compute/operating-lambda-performance-optimization-part-1/),
  verified 2026-08-02), which a latency-sensitive path must design around
  rather than ignore.
- At sustained high volume, per-invocation billing tends to cost more than a
  right-sized reserved instance or container running the same workload, which
  reverses the cost argument the pattern is usually adopted for.
- Migrating away from a chosen platform means rewriting operational tooling
  and often redesigning around a different set of triggers and managed
  services, not merely recompiling code for a new target
  ([Roberts, "Serverless Architectures"](https://martinfowler.com/articles/serverless.html),
  verified 2026-08-02).
- Integration testing against real BaaS dependencies is genuinely harder than
  testing a conventional service against a local database, because those
  dependencies resist local stubbing
  ([Roberts, "Serverless Architectures"](https://martinfowler.com/articles/serverless.html),
  verified 2026-08-02).
- A single request that fans out across several functions and managed
  services produces a distributed trace instead of a call stack, which raises
  the bar for debugging a production incident.
- Statefulness must move out of the function entirely, which forces every
  cross-invocation coordination need, a rate limiter, a session, an
  in-progress workflow, into an explicit BaaS dependency that must be
  designed, paid for, and operated in its own right.

## 11. Failure modes and misuse

**The state-in-memory assumption.** Symptom. A counter, a cache, or a
"logged in" flag stored in a global variable behaves correctly in local
testing and during a burst of traffic on one warm environment, then silently
resets or diverges under concurrent load, because a second concurrent request
landed on a second, freshly created execution environment with none of that
in-memory state. Cause. Treating module-level state as shared state rather
than as a same-environment cache that is coincidentally reused. Fix. Anything
that must be consistent across invocations belongs in a BaaS dependency, not
in a global variable, module-level state is only safe to use as an
opportunistic performance optimization for something idempotent to
reconstruct, exactly the connection-pool pattern shown in the code examples.

**The cold-start-blind latency SLA.** Symptom. A service meets its p50 latency
target comfortably in dashboards, then fails an SLA audit or a customer
complaint traces back to a specific request that took over a second, and the
team cannot reproduce it on demand. Cause. A latency budget was set from
average or warm-path measurements, ignoring that AWS itself reports cold
starts, while rare in steady traffic, occur during deployments, configuration
changes, and scale-out events
([AWS Compute Blog, "Operating Lambda, Performance optimization"](https://aws.amazon.com/blogs/compute/operating-lambda-performance-optimization-part-1/),
verified 2026-08-02), all of which cluster in time rather than spreading
evenly. Fix. Measure and publish p99 or p99.9 latency, not only p50, and apply
Provisioned Concurrency or a snapshot-restore mechanism to any path with a
hard tail-latency requirement.

**The naive warmer.** Symptom. A scheduled job pings a function every few
minutes to "keep it warm", the team believes cold starts are solved, and a
real traffic spike still produces a burst of slow first-requests. Cause. AWS
documents explicitly that pinging a function does not prevent cold starts
during a genuine scaling event, because load balancing across multiple
execution environments and availability zones means a ping keeps at most one
environment warm while the platform may need to create several more to serve
concurrent traffic
([AWS Compute Blog, "Operating Lambda, Performance optimization"](https://aws.amazon.com/blogs/compute/operating-lambda-performance-optimization-part-1/),
verified 2026-08-02). Fix. Use Provisioned Concurrency for genuine scale
guarantees, treat a warming ping as, at best, a minor mitigation for a
consistently low-traffic path, never as a substitute.

**Chatty function-to-function orchestration.** Symptom. A single logical
operation is implemented as five functions calling each other synchronously
in sequence, each one paying its own invocation overhead and its own
possible cold start, and the total latency from first call to last result is far worse than the sum of
each function's individual execution time would suggest. Cause. Decomposing a
workflow along function boundaries that were chosen for code organization
rather than for genuine independent scaling or deployment needs, then wiring
them together with synchronous calls instead of an orchestrator. Fix. Either
combine the steps into fewer functions (the Lambdalith variant from
dimension 8) or move sequencing into a dedicated workflow orchestrator that
manages the steps' state itself rather than relying on function-to-function
calls.

**The oversized dependency bundle.** Symptom. Cold start duration for a
particular function is consistently several times worse than a comparable
function in the same runtime, and profiling shows most of the time is spent
before the handler code ever runs. Cause. A large dependency tree, an entire
cloud SDK imported when only one client is used, or a bundler that ships
unused code, all of which the platform must load and initialize before
invoking the handler, on every cold start. Fix. Trim the dependency surface to
what the function actually calls, use a bundler that tree-shakes unused code,
and move genuinely optional, rarely used code paths into a separate function
rather than a conditional branch inside one large one.

**The unbounded fan-out.** Symptom. A single upstream event, one file upload,
one queue message, triggers a downstream storm of function invocations that
overwhelms a shared, non-elastic dependency, most often a conventional
relational database whose connection limit is fixed regardless of how many
concurrent Lambda execution environments are trying to open a connection.
Cause. The elasticity that makes FaaS attractive applies to the compute layer
only, a BaaS dependency, or worse, a conventional database sitting behind the
functions, has its own capacity limit that does not scale with invocation
concurrency. Fix. Put a managed queue or connection pooler between the
functions and the shared resource, cap concurrency explicitly on the trigger
side, and treat the constrained dependency's capacity as the actual scaling
limit of the system, not the function layer's advertised elasticity.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Serverless (FaaS + BaaS) | Containers on managed orchestrator | Traditional VM fleet (reserved) | Platform as a Service (PaaS, always-on) |
|---|---|---|---|---|
| Cost at low or spiky utilization | Strong. Pay per invocation, near-zero at idle | Moderate. Still pays for minimum replica count | Poor. Reserved capacity billed continuously | Moderate. Often has a paid minimum tier |
| Cost at sustained high utilization | Poor relative to reserved compute at the same throughput | Strong. Right-sized replicas amortize well | Strong. Reserved pricing is cheapest at steady high load | Moderate to strong, depends on tier |
| First-request latency | Weak without mitigation. Cold start risk | Strong once replicas are running | Strong, always warm | Strong, always warm |
| Operational burden (patching, capacity) | Lowest. Platform owns almost everything | Moderate. Team owns image builds and orchestrator config | Highest. Team owns OS, patching, capacity | Low to moderate |
| Elastic scale-out speed | Fastest. Sub-second per environment | Moderate. Bounded by replica start time and pod scheduling | Slowest. Bounded by instance boot and provisioning | Fast, platform-managed |
| Vendor lock-in | Highest, especially with heavy BaaS use | Lower. Containers are broadly portable | Lowest. VMs run anywhere | Moderate, platform-specific build and deploy conventions |
| Local development fidelity | Weakest. Emulators approximate the cloud environment | Strong. The same container runs locally | Strong. Same OS locally and in production | Moderate, depends on platform tooling |
| Long-running or stateful workloads | Poor fit for classical FaaS, needs a distinct primitive | Strong fit | Strong fit | Strong fit |
| Team topology | Good for many small, independently owned functions | Good for services owned by a platform-savvy team | Good where infrastructure ownership is centralized | Good for teams wanting to skip infrastructure entirely |

Reading of the table. Serverless wins decisively where load is spiky and the
operational cost of running any server at all outweighs the per-invocation
billing premium. Containers on a managed orchestrator win once utilization is
high enough and steady enough that right-sized, always-warm replicas beat
per-invocation pricing, while keeping most of the elasticity and far more of
the portability. A reserved VM fleet wins on raw cost per unit of compute at
sustained high, predictable load, at the price of owning every layer below the
application. A PaaS sits between serverless and containers, trading some
elasticity and cost-at-idle for always-warm latency and simpler local
development.

## 13. Related and incompatible patterns

- **Event-Driven Architecture.** The natural parent. Serverless architecture
  is frequently the implementation vehicle for an event-driven system, where
  each function is a handler subscribed to one kind of event, and the
  Trigger-plus-Function pairing described in dimension 5 is a specific,
  managed instance of the publish-and-react shape that event-driven
  architecture describes more generally.
- **Microservices.** Composes closely but is not the same pattern. A
  microservice is defined by its bounded context and independent deployment
  boundary, and it can be implemented as a conventionally deployed service, a
  container, or a set of serverless functions. Serverless is one deployment
  strategy a microservice can adopt, not a synonym for the microservices
  pattern itself, and a single microservice is commonly implemented as several
  cooperating functions rather than one.
- **CQRS (Command Query Responsibility Segregation).** Frequently paired.
  The write side is a small number of functions triggered by commands, writing
  to a BaaS store, while the read side is served by a separately scaled path,
  sometimes a different set of functions entirely, reading from a
  denormalized projection updated asynchronously by an event the write side
  emits. The independent-scaling property of serverless functions fits the
  independent-scaling need CQRS separates out.
- **Hexagonal Architecture (Ports and Adapters).** Composes well inside a
  single function. The function's handler is an inbound adapter translating a
  platform-specific event shape into a domain call, and each BaaS client is an
  outbound adapter. Structuring a function's internals this way keeps the
  domain logic testable in isolation from the event shape and the specific
  managed service, which mitigates part of the testability weakness from
  dimension 3.
- **Pipes and Filters.** A close structural cousin for data-processing
  workloads. A chain of functions, each one triggered by the previous one's
  output landing in a queue or a storage bucket, is Pipes and Filters
  implemented with managed, elastic, per-stage compute instead of long-lived
  processes connected by in-memory pipes.
- **Saga Pattern.** The usual answer to the long-running, multi-step workflow
  limitation named in dimension 4. Where a business process spans several
  functions and must be either fully completed or compensated on failure, a
  Saga, often implemented on top of an orchestrator, coordinates the sequence
  and its compensating actions, since no single function can hold that state
  itself.
- **Monolithic Architecture.** Actively incompatible in spirit, though not
  always in practice. A monolith's central premise is a single deployable
  unit sharing one process and often one in-memory state, serverless's central
  premise is many independently deployable, stateless units. The Lambdalith
  variant from dimension 8 is the honest middle ground, a single deployment
  artifact that still runs as short-lived, stateless invocations, and it is
  worth naming precisely because teams sometimes reach for it while believing
  they have escaped monolith consequences they have not actually escaped.
- **Circuit Breaker.** Composes as a defensive addition rather than a
  structural relative. A function calling an unreliable external dependency
  still benefits from circuit-breaking logic inside the function or in front
  of the BaaS client, because a flood of concurrently scaled-out execution
  environments all retrying a failing dependency at once can worsen an
  outage rather than absorb it, which is the fan-out failure mode from
  dimension 11 applied to an external service instead of a database.

## 14. Refactoring path in and out

Introducing the pattern into a system that does not have it. Ordered steps.

1. Identify one clearly bounded, event-driven unit of work already isolated
   in the existing codebase, a webhook handler, a scheduled job, an
   asynchronous task queue consumer. Confirm it completes well within the
   target platform's maximum execution duration and holds no state that must
   survive past a single invocation.
2. Extract that unit's logic into a pure function of an input event and its
   dependencies, with the dependencies passed in or constructed from
   configuration rather than assumed to be already-running local resources.
   This is the same seam-finding step used in the Strangler Fig pattern,
   applied to compute rather than to a whole service.
3. Deploy that one function behind its trigger, in parallel with the
   existing code path still running the same logic, and route a small
   percentage of real traffic or events to the new path.
4. Instrument both paths identically and compare correctness and latency
   before shifting more traffic, paying particular attention to the cold-start
   tail rather than only the average, per the SLA failure mode in
   dimension 11.
5. Once the new path is proven, retire the old code path and repeat with the
   next candidate unit of work, resisting the urge to migrate the whole system
   at once, since the migration itself introduces the distributed-tracing and
   testing difficulty named in dimension 3.
6. Move any state the extracted function needs across invocations into an
   explicit BaaS dependency at this step, never before, so the migration
   forces the state question to be answered rather than papered over with a
   module-level variable that happens to work during the parallel-run phase.

Removing the pattern when it stops earning its place. Signals that it should
go include a function whose invocation volume has grown so high and so steady
that its bill under per-invocation pricing now exceeds what a right-sized
container would cost, or a set of functions that have accumulated so much
synchronous function-to-function chatter that the system has become a
distributed monolith in all but name.

1. Measure actual invocation volume and duration against the target
   platform's container-based pricing for equivalent compute, to confirm the
   migration is justified by cost or latency rather than by preference alone.
2. Consolidate the chattiest, most tightly coupled functions into a single
   deployable service, preserving the same input and output contracts each
   function already had, so downstream and upstream callers see no change.
3. Containerize that consolidated service and deploy it behind the same
   trigger, either directly, where the platform supports routing an event
   source to a container, or through a small compatibility function that
   forwards the event.
4. Move the extracted BaaS dependencies to be owned and connection-pooled by
   the new long-running service, which removes the per-invocation connection
   overhead the serverless functions had to pay repeatedly.
5. Decommission the individual functions once the consolidated service has
   run in production long enough to confirm parity, and remove the
   compatibility forwarding layer if one was used.

## 15. Testing and verification

Easier because of the pattern.

- A single function with a narrow, well-defined input event and output shape
  is simple to unit test in isolation, construct the event, call the handler
  directly as a plain function call, and assert on the return value, exactly
  as the code examples in this entry do with no framework or emulator
  involved.
- Small units of code are easy to reason about individually, which makes pure
  business logic inside a function straightforward to cover with fast,
  in-process tests.

Harder because of the pattern.

- Roberts's article names this directly, while unit testing is easy,
  integration testing against real BaaS dependencies is hard, because those
  managed services resist local stubbing and cloud test environments differ
  from local development environments
  ([Roberts, "Serverless Architectures"](https://martinfowler.com/articles/serverless.html),
  verified 2026-08-02).
- Cold-start behaviour, concurrency limits, and cross-function timing are
  properties of the deployed platform, not of the function's code, and cannot
  be exercised meaningfully by a unit test at all, they require a deployed
  environment and load-testing tools.
- Local emulators for a given FaaS platform are an approximation, and a test
  suite that passes entirely against an emulator can still fail against the
  real trigger's actual event shape or the real service's actual latency and
  error characteristics.

Techniques that apply.

- **Handler-as-a-plain-function testing.** Structure the handler so it is
  callable directly with a constructed event object and no platform runtime
  in the loop, which is the same technique demonstrated in the code examples
  below, call handler with the event and assert on the return value, with no
  network call and no deployed infrastructure required.
- **Hexagonal internals with fakes at the port boundary.** Following the
  Hexagonal Architecture composition from dimension 13, give the function's
  outbound adapters, the database client, the queue publisher, an interface
  the domain logic depends on, and substitute a fake or in-memory
  implementation in tests, reserving real BaaS calls for a smaller set of
  genuine integration tests.
- **Contract tests against the trigger's event shape.** Because the trigger's
  event schema is defined by the platform, not by the team, a test that
  asserts the handler correctly parses a real, platform-documented sample
  event catches drift when the platform changes an event's shape across a
  version, which a purely hand-constructed test event would not.
- **A small, deliberately maintained set of deployed integration tests.**
  Given that local stubbing of BaaS dependencies is weak, accept a smaller
  number of tests that run against a real, isolated staging deployment of the
  actual managed services, rather than trying to fully substitute for them
  locally, and keep that set small and fast enough to run on every deploy.
- **Cold-start and concurrency load testing as a separate practice.** Treat
  tail-latency and concurrency-limit behaviour as a deployed-environment
  concern verified with load-testing tools against a real or staging
  deployment, not as something a unit test suite is expected to catch.

## 16. Observability signals

Because a single logical request can fan out across many short-lived
processes with no shared memory, observability has to be designed in from the
trigger layer, not bolted on afterward.

What to record.

- A correlation identifier generated at the trigger and propagated through
  every downstream function invocation, queue message, and BaaS call, so a
  single logical request can be reconstructed across process boundaries after
  the fact.
- Per-invocation duration, split into cold-start initialization time and
  handler execution time where the platform exposes the distinction, so a
  latency regression can be attributed to one or the other rather than
  investigated as one undifferentiated number.
- A cold-start counter or flag on every invocation, so the actual observed
  cold-start rate can be compared against the platform's stated steady-state
  average and against the failure mode in dimension 11 where deployments and
  scale-out events cluster cold starts in time.
- Concurrent execution count over time, since this is the signal that most
  directly explains both cost and the fan-out failure mode against a shared,
  non-elastic dependency.
- Error rate and error type per function, distinguishing a function's own
  logic errors from platform-level throttling or timeout errors, since the
  two point at entirely different fixes.
- BaaS-side metrics for anything a function depends on, database connection
  count, queue depth, and queue age, all of which reveal backpressure that
  the function-level metrics alone would not show.

A healthy instance on a dashboard. The cold-start rate sits near the
platform's stated steady-state figure and only spikes briefly around known
deployment events, then returns to baseline. Concurrent execution count
tracks incoming trigger volume closely, with no sustained plateau at a
concurrency limit. Error rate is flat and low, and when it moves, it moves
together with a known upstream dependency's own error rate rather than in
isolation. Correlation-tagged traces reconstruct cleanly end to end with no
gaps.

A failing instance. Cold-start rate stays high well past a deployment
window, which points at either an oversized dependency bundle (dimension 11)
or a workload pattern the platform is not keeping warm between invocations. A
concurrent-execution plateau that tracks a flat line rather than the actual
trigger volume means the account or function has hit a concurrency limit and
requests are queuing or being throttled behind it, invisible to a naive
success-rate dashboard until the queue itself is instrumented. A BaaS
dependency's connection count climbing in lockstep with function concurrency,
with no limit, is the fan-out failure mode in progress and will eventually
exhaust that dependency's own limit regardless of how healthy the function
layer's own metrics look.

## 17. Security and privacy implications

The security posture of serverless architecture is a subject with real
weight, not a settled matter of no concern, and several implications follow
directly from the structure in dimension 5.

**A shifted, not eliminated, attack surface.** The platform vendor is
responsible for patching the operating system and the underlying isolation
mechanism, which removes a large, well-understood class of infrastructure
vulnerability from the team's responsibility entirely. AWS documents its
Lambda execution environments as isolated by Firecracker virtualization,
providing VM-level separation between workloads
([AWS, "What is AWS Lambda?"](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html),
verified 2026-08-02). What remains squarely the team's responsibility is
application-layer code, dependency supply chain, and the permissions granted
to each function.

**Function-level permission scope.** Because each function is an independent
deployable unit, each one usually carries its own execution role and
permission set, which is a genuine security improvement over a monolithic
service holding one broad set of credentials for every operation it might
ever perform. The corresponding failure mode, not covered elsewhere in this
entry because it is a security-specific misuse rather than an architectural
one, is granting every function the same broad, copy-pasted permission
template rather than the minimum each one actually needs, which erases the
advantage the fine-grained deployment unit was supposed to provide.

**Dependency supply chain per function.** Every function ships its own
dependency bundle, which multiplies the number of places a vulnerable or
compromised third-party package can enter the system compared to a single
monolithic deployment with one dependency tree to audit. The oversized
dependency bundle failure mode in dimension 11 has a security dimension as
well as a performance one, a smaller, deliberately curated dependency surface
is both faster to cold-start and smaller to audit.

**Event payload as an untrusted input surface.** A function's entire input is
a platform-delivered event object, constructed from an HTTP request body, a
storage notification, or a queue message, each of which may originate from an
external, untrusted source. Because the handler is the first application
code to see that payload, it is the correct place to validate and sanitize
input, exactly as any other request-handling code would, and the ease of
writing a new trigger-bound function should not be mistaken for an exemption
from that discipline.

On privacy, the pattern raises one implication that is architectural rather
than incidental. Data frequently crosses process and, depending on how BaaS
dependencies are chosen, potentially service boundaries between a trigger, a
function, and one or more managed backend services, each of which may have
its own data-residency and retention behaviour. Where a workload handles
regulated or personal data, each BaaS dependency in the chain needs its own
data-handling review, not only the function's own code, because the function
is frequently the thinnest, least persistent part of the whole path the data
travels through.

## References

1. Mike Roberts. "Serverless Architectures". martinfowler.com.
   https://martinfowler.com/articles/serverless.html
   Verified 2026-08-02. Source for the FaaS-plus-BaaS definition, the cold
   start, vendor lock-in, and testability trade-offs.
2. Amazon Web Services. "What is AWS Lambda?" AWS Lambda Developer Guide.
   https://docs.aws.amazon.com/lambda/latest/dg/welcome.html
   Verified 2026-08-02. Source for the Lambda definition, the
   Lambda Functions versus Lambda MicroVMs distinction, Firecracker
   virtualization, and the 15-minute execution duration limit.
3. Amazon Web Services. "Operating Lambda, Performance optimization, Part 1".
   AWS Compute Blog.
   https://aws.amazon.com/blogs/compute/operating-lambda-performance-optimization-part-1/
   Verified 2026-08-02. Source for the sub-one-percent steady-state cold-start
   rate, cold-start duration range, Provisioned Concurrency behaviour, and the
   function-warmer limitation.
4. Amazon Web Services. "Reducing Java cold starts on AWS Lambda functions
   with SnapStart". AWS Compute Blog.
   https://aws.amazon.com/blogs/compute/reducing-java-cold-starts-on-aws-lambda-functions-with-snapstart/
   Verified 2026-08-02. Source for the SnapStart mechanism and the p99.9
   latency benchmark figures.
5. Cloudflare. "How Workers works". Cloudflare Workers documentation.
   https://developers.cloudflare.com/workers/reference/how-workers-works/
   Verified 2026-08-02. Source for the V8 isolate execution model and its
   stated startup speed and memory advantage over a per-invocation container
   or virtual machine.
6. Amazon Web Services. "AWS Lambda customer case studies". AWS Lambda
   resources index.
   https://aws.amazon.com/lambda/resources/customer-case-studies/
   Verified 2026-08-02. Source for the Thomson Reuters, iRobot, FINRA, Square
   Enix, Financial Engines, Bustle, and T-Mobile production-use figures in
   dimension 9.
7. Microsoft. "Azure Functions". Azure product documentation.
   https://azure.microsoft.com/en-us/products/functions
   Verified 2026-08-02. Source for the consumption-plan, pay-per-use billing
   description used as background for the cost forces in dimension 3.

## Code examples

Three languages where the pattern is genuinely idiomatic across different
platforms, each one demonstrating the same architectural property, module or
package-level initialization runs once per execution environment and is
reused across warm invocations, which is the mechanism behind both the
performance benefit of a warm path and the state-loss risk named in
dimension 11 if that reused state is mistaken for durable, shared state. Each
sample below constructs a sample event, invokes the handler directly as a
plain function call, exactly the handler-as-a-plain-function testing
technique from dimension 15, and asserts the initialization counter stays at
one across two invocations, proving reuse without requiring a deployed
platform or an emulator.

### TypeScript

Written against the shape an AWS API Gateway or a Cloudflare Worker delivers,
an event object in, a response object out, with no platform SDK required to
demonstrate the architectural property itself.

```typescript
interface OrderEvent {
  orderId: string;
  amountCents: number;
  taxCents: number;
}

interface Response {
  statusCode: number;
  body: string;
}

// Module-level state survives across warm invocations of the same
// execution environment, but never across two concurrent environments.
let initCount = 0;

function connectionPool(): { poolSize: number } {
  initCount += 1;
  return { poolSize: 5 };
}

const pool = connectionPool();

export function handler(event: OrderEvent): Response {
  if (!event.orderId) {
    return { statusCode: 400, body: JSON.stringify({ error: "orderId required" }) };
  }
  const total = event.amountCents + event.taxCents;
  return {
    statusCode: 200,
    body: JSON.stringify({ orderId: event.orderId, totalCents: total, initCount, poolSize: pool.poolSize }),
  };
}

const r1 = handler({ orderId: "A1", amountCents: 1000, taxCents: 80 });
const r2 = handler({ orderId: "A2", amountCents: 500, taxCents: 40 });
console.log(r1);
console.log(r2);
if (JSON.parse(r1.body).initCount !== 1 || JSON.parse(r2.body).initCount !== 1) {
  throw new Error("expected a single cold-start init reused across warm invocations");
}
console.log("OK");
```

Compiled with tsc, target es2020, module commonjs, and run with node.
Output confirms initCount stays at 1 across both invocations, which is the
same behaviour a warm Lambda or Worker execution environment exhibits in
production.

### Python

Written against the AWS Lambda handler signature, handler taking an event
and a context, which is the most widely deployed FaaS handler shape in
production.

```python
import json
import time

# Simulates a cold-started dependency (a DB client, an HTTP client pool).
# Created once at module load (cold start), reused across warm invocations.
_INIT_COUNT = {"value": 0}


def _get_client():
    _INIT_COUNT["value"] += 1
    return {"connected_at": time.time(), "pool_size": 5}


_client = _get_client()


def handler(event, context=None):
    order_id = event.get("order_id")
    if not order_id:
        return {"statusCode": 400, "body": json.dumps({"error": "order_id required"})}
    total = event.get("amount_cents", 0) + event.get("tax_cents", 0)
    return {
        "statusCode": 200,
        "body": json.dumps({"order_id": order_id, "total_cents": total, "init_count": _INIT_COUNT["value"]}),
    }


if __name__ == "__main__":
    r1 = handler({"order_id": "A1", "amount_cents": 1000, "tax_cents": 80})
    r2 = handler({"order_id": "A2", "amount_cents": 500, "tax_cents": 40})
    print(r1)
    print(r2)
    assert json.loads(r1["body"])["init_count"] == 1
    assert json.loads(r2["body"])["init_count"] == 1
    print("OK: single cold-start init reused across two warm invocations")
```

Run directly with python3. The _INIT_COUNT dictionary is module-level
state, the exact pattern AWS documents production Lambda functions using for
database connections and HTTP clients, so they are created once per
execution environment rather than once per invocation.

### Go

Written to compile and run standalone, without the aws-lambda-go module,
because the architectural property demonstrated here, package-level
initialization reused across invocations on one execution environment, holds
regardless of which SDK ultimately wraps the handler for deployment.

```go
package main

import (
	"encoding/json"
	"fmt"
)

// OrderEvent mirrors the JSON payload a trigger (API Gateway, SQS) delivers.
type OrderEvent struct {
	OrderID     string `json:"order_id"`
	AmountCents int    `json:"amount_cents"`
	TaxCents    int    `json:"tax_cents"`
}

type Response struct {
	StatusCode int    `json:"status_code"`
	Body       string `json:"body"`
}

// initCount and poolSize are package-level: created once per execution
// environment (cold start), reused by every invocation that lands
// on the same warm environment.
var initCount int

func connectionPool() int {
	initCount++
	return 5
}

var poolSize = connectionPool()

func handler(event OrderEvent) Response {
	if event.OrderID == "" {
		return Response{StatusCode: 400, Body: `{"error":"order_id required"}`}
	}
	total := event.AmountCents + event.TaxCents
	body, _ := json.Marshal(map[string]any{
		"order_id":    event.OrderID,
		"total_cents": total,
		"init_count":  initCount,
		"pool_size":   poolSize,
	})
	return Response{StatusCode: 200, Body: string(body)}
}

func main() {
	r1 := handler(OrderEvent{OrderID: "A1", AmountCents: 1000, TaxCents: 80})
	r2 := handler(OrderEvent{OrderID: "A2", AmountCents: 500, TaxCents: 40})
	fmt.Println(r1)
	fmt.Println(r2)
	if initCount != 1 {
		panic("expected a single cold-start init reused across warm invocations")
	}
	fmt.Println("OK")
}
```

Run with go run main.go. In a real deployment, main would instead call
lambda.Start passing handler, from the aws-lambda-go module, but the
architecturally relevant part, the package-level poolSize initialized
exactly once, is identical either way, and the standalone form here compiled
and ran without requiring network access to fetch that dependency.
