---
name: Serverless Deployment
slug: serverless-deployment
family: 10-microservices
category: Deployment
aliases: [Function as a Service, FaaS Deployment, Lambda-Style Deployment]
first_described: "Roberts, Serverless Architectures, martinfowler.com, 2018"
maturity: established
related: [idempotent-consumer, api-gateway, service-instance-per-host, database-per-service, transactional-outbox]
incompatible_with: [service-instance-per-host]
verified: 2026-08-02
---

# Serverless Deployment

## 1. Name, aliases, and lineage

The name in day-to-day use is Serverless Deployment, and the narrower technical
term underneath it is Function as a Service, FaaS. Neither term was minted by a
single paper the way Circuit Breaker traces to a Release It essay. The word
serverless appears in industry writing from around 2015, attached first to AWS
Lambda, which AWS announced at re Invent in November 2014. The most widely
cited attempt to pin the term down precisely is Mike Roberts, "Serverless
Architectures," martinfowler.com, first published 2016 and revised 2018
(https://martinfowler.com/articles/serverless.html, verified 2026-08-02).
Roberts splits serverless into two overlapping ideas, Backend as a Service,
BaaS, meaning third party managed services such as an auth provider or a
managed database that remove the need to run a server process at all, and
Function as a Service, FaaS, meaning application logic that runs in
stateless, event triggered compute units the vendor provisions, scales, and
tears down. His own words, quoted directly from the article, describe FaaS
code as running in "stateless compute containers that are event-triggered,
ephemeral (may only last for one invocation), and fully managed by a third
party."

This entry is about the deployment pattern, not the vendor product. The pattern
is package a single unit of behaviour, hand it to a platform that owns the
process lifecycle, and let that platform decide when to start an instance, how
many instances to run concurrently, and when to kill an idle one. The name
Lambda-Style Deployment is common in conversation because AWS Lambda was first
to mainstream adoption and the shape of its programming model, a handler
function plus an event object, became the shape every other vendor copied.
Cloudflare Workers, Azure Functions, Google Cloud Functions, and Vercel
Functions all present the same handler-plus-event shape even though their
underlying execution substrate differs sharply, which is covered in dimension
8.

The maturity here is marked established rather than canonical. The pattern is
in daily production use across every major cloud, but the concrete mechanics,
billing models, cold start mitigation, and even the vocabulary vendors use for
the same underlying idea, are still shifting year over year. Azure retired its
original Consumption plan model in favour of Flex Consumption as the
recommended path for new serverless function apps (Microsoft Learn, "Azure
Functions scale and hosting options," verified 2026-08-02), and Cloudflare's
isolate model is different enough from a container that some writers argue it
should not be called serverless at all. A pattern whose vocabulary is still
settling is established, not canonical.

## 2. Problem and context

A team owns a piece of business logic that is genuinely small and genuinely
bursty. An image gets uploaded and needs a thumbnail generated. A webhook
arrives from a payment provider and needs to update an order record. A
scheduled job needs to run once a night to close out a batch. None of these
things need to run continuously, none of them need a warm process sitting idle
between events, and the load on each of them can jump from zero to thousands
of concurrent invocations in the space of a minute during a flash sale or a
marketing push.

The classic answer, run a small service on its own host or container per
Service Instance per Host, forces the team to own capacity planning for a
workload whose shape is genuinely unpredictable. Provision for the peak
and most of the fleet sits idle most of the day. Provision for the average and
the peak causes queued requests, timeouts, and paged engineers. The team also
now owns patching the base image, rotating the runtime, configuring the
autoscaler, and setting up health checks, none of which touches the actual
business problem of resizing an image or updating an order.

The context that makes Serverless Deployment the right answer has three
parts, and all three need to be true at once for the pattern to earn its
place.

- The unit of work is genuinely stateless between invocations, or can be made
  so by pushing state into an external store. A function that needs an
  in-memory cache warmed across thousands of requests fights the platform's
  ability to kill and recreate instances at will.
- The workload is event shaped. An HTTP request, a queue message, a storage
  object landing in a bucket, a schedule tick. FaaS platforms are built around
  a trigger abstraction, and a workload with no natural trigger, a long
  running batch computation with internal checkpoints, does not fit.
- The team is willing to trade fine grained control over the runtime, the
  exact CPU generation, the network stack, warm pool sizing, for near zero
  idle cost and near zero operational ownership of the compute layer.

Where any of the three is false the pattern still runs, but it runs badly. A
stateful workload forced into FaaS reinvents state externally at a latency
and cost penalty. A non event shaped workload forced into FaaS fights the
platform's timeout limits. A team that needs deep runtime control fights the
platform's abstraction at every turn.

## 3. Forces

**Cost versus latency at idle.** Pay per invocation with no idle charge is the
headline benefit, and it is real for bursty, low average, high peak
workloads. The cost of that model is the cold start, the latency penalty paid
the first time a new execution environment has to be created. AWS states cold
starts occur in under one percent of invocations and usually add under 100
milliseconds to over one second (AWS documentation, "Understanding the Lambda
execution environment lifecycle," verified 2026-08-02), but the distribution
is not uniform. A function with a large dependency tree, a JVM runtime, or a
database connection to establish during static initialisation pays much
longer cold starts than a small interpreted function with no external
dependency.

**Operability versus control.** The platform owns patching, scaling,
placement, and process supervision. That is the operational win. The cost is
that the team gives up choice of CPU generation, cannot tune kernel
parameters, cannot keep a process warm indefinitely without paying for
provisioned concurrency, and is bound by the platform's timeout, memory, and
package size limits. AWS Lambda's standard execution model caps a function
at fifteen minutes and enforces a ten second initialisation window before the
platform gives up and retries the init phase at invocation time (AWS
documentation, same source, verified 2026-08-02). A workload that genuinely
needs twenty minutes of uninterrupted compute does not fit without
restructuring into smaller steps or moving to a different deployment pattern
entirely.

**Consistency versus concurrency.** Multiple concurrent invocations of the
same function run in different, isolated execution environments by default.
There is no shared in-process memory between them unless the platform
explicitly offers a shared layer, and even then it is opt in and unreliable
across scale-to-zero events. This forces every piece of shared state,
counters, locks, caches, into an external, network hop away store, which adds
latency and a consistency model the team must reason about explicitly instead
of getting for free from a single process's memory.

**Coupling to the platform versus portability.** Roberts is direct about this
trade-off in the source article, verified above. Switching FaaS vendors means
reworking the deployment tooling, the trigger configuration, and often parts
of the code itself, because the event object shape, the environment variable
conventions, and the extension APIs differ by vendor. The pattern favours
depth of integration with one platform's event sources over portability
across platforms.

**Cost model transparency versus predictability at sustained load.** Per
invocation billing is cheap at low, spiky volume and can become more
expensive than a provisioned server at sustained high volume, because the
per-millisecond-per-invocation rate carries a margin the provider needs to
cover the idle capacity it is holding in reserve for other tenants. The
pattern favours the spiky, low average case and sacrifices cost predictability
and cost efficiency at sustained saturation.

## 4. Applicability and non-applicability

Reach for Serverless Deployment when the following hold.

- The workload is event driven with a clean, well defined trigger, an HTTP
  request through an API Gateway, a message on a queue, an object landing in
  blob storage, a scheduled tick, a database change stream.
- Traffic is bursty or unpredictable, with long idle periods between spikes,
  so paying only for actual invocation time beats paying for reserved,
  continuously running capacity.
- The unit of work completes well within the platform's execution time
  limit, minutes, not hours, and does not depend on long lived in-memory
  state surviving between invocations.
- The team wants to minimise operational ownership of the compute layer,
  patching, capacity planning, autoscaling policy, for this specific piece of
  logic, and is willing to accept the platform's constraints in exchange.
- Glue logic between managed services is needed, resizing an image after an
  upload, enriching a record after a webhook, fanning a queue message out to
  several downstream calls.

Do NOT reach for it in these cases, and the reason matters more than the rule.

- The workload needs to hold state in memory across many requests for
  performance, a large in-memory cache, an open long lived connection pool
  sized for steady state, a WebSocket session that must persist for hours.
  The instance can be recycled at any time and the platform does not
  guarantee affinity.
- The workload is CPU or memory intensive and sustained, video transcoding at
  scale, training a model, running continuously at high utilisation for
  hours. The per-invocation pricing model and the resource limits, AWS
  Lambda tops out at 10,240 MB of memory (AWS documentation, Lambda quotas
  page, verified 2026-08-02), make a container or a dedicated instance
  cheaper and simpler at that scale.
- Sub-ten-millisecond, tail-latency-critical request paths where even the
  rare cold start is unacceptable, unless the team is willing to pay for
  provisioned or always-ready concurrency, which reintroduces a fixed
  reserved cost and partially defeats the pattern's cost model.
- The team needs fine control over the network stack, custom kernel modules,
  GPU scheduling with exotic drivers, or an exact CPU microarchitecture for
  numerically sensitive code. FaaS platforms abstract the machine away on
  purpose.
- Vendor lock-in is a hard organisational constraint and there is no budget
  to build an abstraction layer over the trigger and deployment surface. The
  event shapes, IAM models, and deployment tooling differ enough between AWS
  Lambda, Azure Functions, and Cloudflare Workers that a naive multi-cloud
  FaaS strategy usually costs more than it saves.
- The function's own dependencies make cold start unacceptable and the
  workload cannot tolerate the cost of provisioned concurrency. A JVM based
  function with a large classpath doing latency sensitive synchronous work is
  the recurring example vendors themselves call out in optimisation guides.

## 5. Structure

- **Function.** The unit of deployment. A single handler with one well
  defined entry point, packaged with its dependencies, given a memory and
  timeout limit by the operator, and otherwise opaque to the platform. It
  owns no long running process of its own.
- **Trigger.** The event source bound to the function. An HTTP route through
  an API Gateway, a queue, a storage bucket notification, a schedule, a
  stream. The trigger defines the event shape the function receives and,
  usually, the retry and delivery semantics, at-least-once, at-most-once, or
  exactly-once-processing achieved through idempotency, not exactly-once
  delivery.
- **Execution environment.** The platform-managed sandbox, a microVM, a
  container, or a V8 isolate depending on vendor, that actually runs the
  function's code for one or more invocations. This is the thing that is
  created cold, frozen between invocations, thawed for reuse, and eventually
  torn down. The function author does not create or destroy this directly.
- **Runtime.** The language-specific process inside the execution
  environment that bridges the platform's invocation protocol to the
  function's handler. AWS Lambda's Runtime API is the documented example
  (AWS documentation, Lambda execution environment lifecycle, verified
  2026-08-02).
- **External state store.** Whatever holds state the function needs beyond a
  single invocation, a database, an object store, a cache, because the
  execution environment's memory is not a reliable place to keep it.
- **Orchestrator or scheduler.** The platform component, invisible to the
  function author, that decides how many execution environments to run
  concurrently, when to reuse a warm one, and when to freeze or kill one.
  This is the component the pattern hands control to in exchange for not
  operating it.
- **Deployment package and configuration.** The artifact, code plus
  dependencies plus a manifest describing memory, timeout, trigger bindings,
  and IAM or role permissions, that the operator ships to the platform.
  Infrastructure as code tools such as the AWS Serverless Application Model
  or the Serverless Framework usually own this artifact's lifecycle.

## 6. ASCII structure diagram

```
+---------------------------------------------------------------+
| Trigger source, an HTTP route, queue, blob event, or schedule |
+---------------------------------------------------------------+
     |
     v
+--------------------------------------------------+
| Orchestrator, decides: reuse a warm env, or cold-start|
+--------------------------------------------------+
     | routes to one of two possible envs
     v
+--------------------------------+
| Execution env #1, warm, reused |
| Runtime -> Function handler    |
+--------------------------------+
+------------------------------------+
| Execution env #2, cold-started now |
| Runtime -> Function handler        |
+------------------------------------+
     | either env
     v
+-------------------------------------------------+
| External state store                            |
| a database, object store, cache, or message bus |
+-------------------------------------------------+
```

## 7. Dynamics

The event flow below follows a single request through cold start, then a
second request through warm reuse, matching the phases AWS documents for
Lambda, Init, Invoke, and the freeze between invocations (AWS documentation,
Lambda execution environment lifecycle, verified 2026-08-02). Other vendors
use different names for the same three phases.

```
First invocation, no warm environment available (a cold start)

  Trigger      Orchestrator        Execution env          Runtime          Function
    |               |                     |                   |                |
    |--event------->|                     |                   |                |
    |               |--create new env---->|                   |                |
    |               |                     |--bootstrap------->|                |
    |               |                     |                   |--static init-->|
    |               |                     |                   |  (module load, |
    |               |                     |                   |   DB client,   |
    |               |                     |                   |   config read) |
    |               |                     |                   |<---ready-------|
    |               |                     |                   |--invoke event->|
    |               |                     |                   |                |--handle-->
    |               |                     |                   |<--result-------|
    |               |<--------------------|<------------------|                |
    |<--response-----|                     |                   |                |
    |               |                     |--freeze (keep warm for reuse)------>|

Second invocation, arrives while the environment above is still warm

  Trigger      Orchestrator        Execution env (warm, reused)      Function
    |               |                     |                             |
    |--event------->|                     |                             |
    |               |--reuse warm env---->|                             |
    |               |                     |--invoke event (no init)--->|
    |               |                     |                             |--handle-->
    |               |                     |<--result--------------------|
    |               |<--------------------|                             |
    |<--response-----|                     |                             |
    |               |                     |--freeze again-------------->|

  If no invocation arrives before the platform's idle timeout, the
  orchestrator terminates the environment and any subsequent invocation
  cold-starts a new one, repeating the first sequence.
```

The important observation the diagram is meant to surface is that static
initialisation, module imports, client construction, configuration reads,
runs once per environment, not once per invocation. AWS's own optimisation
guidance is explicit that this static init phase is the largest single
contributor to cold start latency and recommends moving expensive setup
outside the handler so it is paid once per environment and amortised across
every warm invocation that environment serves (AWS documentation, same
source, "Optimizing static initialization," verified 2026-08-02).

## 8. Implementation variants

- **Container-per-invocation, microVM isolation.** AWS Lambda's default
  execution model. Each execution environment is a Firecracker microVM. Cold
  starts are more expensive than the isolate model below because a real
  virtual machine boots, but the isolation boundary is stronger and general
  purpose runtimes, arbitrary containers via the Lambda container image
  packaging option, are fully supported.
- **V8 isolate multiplexing.** Cloudflare Workers' model. Rather than one
  container per function, a single V8 process hosts many isolates
  simultaneously, each with its own sandboxed global scope but sharing the
  underlying JavaScript engine process. Cloudflare states an isolate "can
  start around a hundred times faster than a Node process on a container or
  virtual machine" and that isolates "consume an order of magnitude less
  memory" at startup (Cloudflare developer documentation, "How Workers
  works," verified 2026-08-02). The trade is a narrower language surface,
  effectively JavaScript, WebAssembly, and languages that compile to either,
  and a smaller sandbox than a full container gives.
- **Snapshot-and-restore.** AWS Lambda SnapStart takes a memory and disk
  snapshot of a fully initialised execution environment at publish time and
  restores from that snapshot instead of running static initialisation from
  scratch on every cold start (AWS documentation, Lambda execution
  environment lifecycle, Restore phase, verified 2026-08-02). This converts a
  cold start's static-init cost into a one-time cost paid at deploy time
  rather than at every fresh environment creation, at the cost of extra
  complexity around any state that must not be reused unchanged across
  restores, credentials and random number generator state being the classic
  examples vendors warn about.
- **Provisioned or always-ready concurrency.** A fixed number of execution
  environments kept permanently warm, sidestepping cold start for the
  provisioned portion of traffic at the cost of paying for that capacity
  whether or not it is used. AWS Lambda's provisioned concurrency and Azure
  Functions' always ready instances on the Flex Consumption and Premium
  plans are the direct examples (Microsoft Learn, "Azure Functions scale and
  hosting options," verified 2026-08-02). This variant is a deliberate
  partial retreat from the pure pay-per-use model toward a hybrid that trades
  some of the cost benefit back for latency predictability.
- **Language-idiomatic handler shapes.** The pattern is expressed differently
  depending on how the host language handles closures and modules. In
  JavaScript and TypeScript, a module-level constant initialised outside the
  exported handler function is the idiomatic way to pay setup cost once per
  environment. In Python, a module-level variable assigned at import time
  plays the same role. In Go, because each cold start recompiles nothing, a
  package-level variable initialised in an init function or at declaration
  time is reused across invocations served by the same process, and Go's
  comparatively fast binary startup is one reason several vendors document
  Go as having among the shortest cold starts of the officially supported
  runtimes.
- **Durable, checkpointed functions.** A newer variant, distinct from
  classic short-lived FaaS, that adds state persistence and checkpointing so
  a logical function can span far longer than the platform's raw execution
  limit by resuming from a saved point rather than running continuously.
  AWS's own current Lambda documentation describes exactly this shape under
  the name Durable Functions, contrasted directly against the standard
  fifteen-minute execution model (AWS documentation, Lambda execution
  environment lifecycle, verified 2026-08-02). This variant blurs the line
  between Serverless Deployment and a workflow orchestration pattern and
  should be read as FaaS extended with an explicit state machine, not as a
  different pattern.

## 9. Known production uses

- **iRobot's cloud fleet management for Roomba vacuums.** iRobot's published
  AWS case study describes the connected Roomba backend built on AWS Lambda
  processing telemetry and device events from millions of connected robots,
  used specifically because device traffic is bursty and unpredictable by
  time of day (AWS customer case study, iRobot, published at
  aws.amazon.com/solutions/case-studies, referenced via AWS's published
  serverless customer case study index, verified 2026-08-02).
- **Coca-Cola's vending machine backend.** Coca-Cola's engineering account of
  its vending machine interaction platform describes migrating to a
  serverless architecture on AWS Lambda and API Gateway specifically to
  handle sporadic, geographically distributed traffic from vending
  machines without maintaining always-on servers (referenced in AWS's own
  published Lambda customer stories page, aws.amazon.com/lambda, verified
  2026-08-02).
- **Netflix's encoding pipeline components.** Netflix's technology blog has
  documented using AWS Lambda for parts of its media processing pipeline,
  specifically bursty, event-driven, short-duration tasks triggered by new
  content arriving, distinct from Netflix's own primary microservices fleet
  which runs on EC2 (Netflix Technology Blog, distributed encoding pipeline
  coverage, netflixtechblog.com, verified 2026-08-02).
- **Cloudflare's own edge products.** Cloudflare Workers is not only a
  product Cloudflare sells, it is the execution substrate for several of
  Cloudflare's own edge features, as described in Cloudflare's own
  architecture documentation for how Workers is built and used internally
  (Cloudflare developer documentation, "How Workers works," verified
  2026-08-02).

## 10. Consequences

Positive.

- No idle compute cost for genuinely bursty workloads, because billing is
  tied to actual invocation time rather than reserved capacity.
- The team stops owning patching, base image maintenance, and autoscaler
  tuning for the compute layer of this specific workload, the platform owns
  it.
- Natural, near-linear horizontal scaling to the platform's concurrency
  limit with no manual capacity planning, useful for genuinely spiky load
  such as a flash sale or a viral event.
- Deployment granularity shrinks to a single function, which lowers the
  blast radius of a bad deploy compared to redeploying a whole service, and
  makes independent versioning of small pieces of logic straightforward.
- Forces state out of the process and into an explicit external store, which,
  done deliberately, produces a cleaner separation between compute and state
  that pays off when the same state needs to be read by more than one
  function or trigger.

Negative.

- Cold start latency is a real, user visible cost for the first request an
  idle environment serves, and it is worse for runtimes and dependency trees
  that take longer to initialise, a cost the team pays in the least
  convenient place, the tail of the request latency distribution.
- Debugging is harder. There is no long running process to attach a
  debugger to in the traditional sense, and distributed tracing across many
  short lived, independently scaled function invocations requires
  intentional correlation identifiers threaded through every event.
- Vendor lock-in is structural, not accidental. The trigger configuration,
  IAM or role model, environment variable conventions, and extension APIs
  are vendor specific enough that a rewrite is usually required to move
  platforms, a trade-off Roberts calls out directly in the source article
  cited in dimension 1.
- Cost at sustained high volume can exceed a provisioned server, because the
  per-invocation price includes a margin for the idle capacity the platform
  holds in reserve on the tenant's behalf. The pattern is optimised for the
  spiky case, not the saturated case.
- Local development and testing fidelity is imperfect. Emulators for
  cold-start behaviour, concurrency limits, and IAM permission boundaries
  rarely match production exactly, so integration bugs specific to the
  platform's execution model surface late, sometimes only in production.
- At-least-once delivery is the default guarantee for most asynchronous
  triggers, which pushes the burden of correctness onto the function author
  in the form of required idempotency, covered further in dimension 13's
  relationship to Idempotent Consumer.

## 11. Failure modes and misuse

**Symptom.** The first request after a period of low traffic takes 800
milliseconds to two seconds longer than every subsequent request, and this
repeats the same way after every idle window.
**Cause.** A cold start whose static initialisation phase is doing expensive
work, pulling a full SDK, opening a database connection, parsing a large
configuration file, that the platform must redo for every freshly created
execution environment.
**Fix.** Move only the minimum required imports and client construction into
the module-level scope so it runs once per environment, defer anything not
needed on the hot path with lazy initialisation, and consider provisioned
concurrency or a snapshot-restore mechanism such as SnapStart if the
remaining cold start is still unacceptable for the traffic pattern.

**Symptom.** A payment or order-processing function occasionally records a
transaction twice for what the client insists was a single action.
**Cause.** The trigger's at-least-once delivery guarantee retried the
invocation after a transient failure, a timeout, a throttling error, a
platform-side retry, and the function's logic was not written to be safe
against re-execution with the same input, so the retry re-applied the
side effect.
**Fix.** Apply the Idempotent Consumer pattern explicitly, an idempotency key
derived from the event payload checked against a durable store before the
side effect runs, exactly as AWS's own Powertools idempotency utility
implements for Lambda functions triggered by SQS (AWS Compute Blog,
"Handling Lambda functions idempotency with AWS Lambda Powertools," verified
2026-08-02).

**Symptom.** A function that worked in every test suddenly starts throwing
permission-denied errors against a resource it has always used, once
traffic scales up.
**Cause.** The function's IAM role or managed identity was granted broad,
undifferentiated permissions during initial development, and a later
tightening pass, or a security review, revealed the function was silently
depending on an access path nobody explicitly reasoned about, the classic
over-privileged function role failure mode that carries more weight in a
serverless system than in a traditional one because every function
usually gets its own role, multiplying the number of privilege boundaries
a team must audit (OWASP Serverless Top 10 Project overview, owasp.org,
verified 2026-08-02, frames application level security, including access
control, as remaining the function author's responsibility even though the
platform manages the infrastructure layer).
**Fix.** Scope each function's execution role to the minimum set of
resources and actions it actually needs, review roles as part of every
deploy rather than only during incident response, and treat a broad
wildcard permission on a function role as a code smell equivalent to a
hardcoded credential.

**Symptom.** A batch of events processed through a queue trigger silently
loses a fraction of records under sustained high throughput, with no error
logged.
**Cause.** The function's concurrency limit was reached, and the platform
throttled or the source queue's visibility timeout expired before the
function finished processing a batch, causing messages to be redelivered
past a dead-letter threshold or, in a poorly configured pipeline, dropped
without the team noticing because no alert was wired to the throttling
metric.
**Fix.** Set an explicit reserved or maximum concurrency appropriate to the
downstream systems the function calls, configure a dead-letter queue or
destination for failed invocations, and alert on the platform's throttling
and error-rate metrics, not only on the function's own application logs.

**Symptom.** A function used to orchestrate several downstream steps grows
past its execution timeout under load and starts failing mid-sequence,
leaving some downstream steps applied and others not.
**Cause.** The team used Serverless Deployment for a workload that is
actually a multi-step workflow with its own state machine needs, forcing a
long sequential process into a single function invocation bound by the
platform's timeout limit, and treating a partial failure as recoverable
without designing for it.
**Fix.** Decompose the workflow into a proper orchestration pattern, a Saga
or a managed workflow service such as AWS Step Functions, where each step is
its own function invocation with its own retry and compensation logic,
rather than one long function trying to do all of it inline.

## 12. Trade-off matrix

| Force | Serverless Deployment (FaaS) | Service Instance per Host | Container orchestration (Kubernetes-style) |
|---|---|---|---|
| Idle cost | Near zero, pay per invocation | Full cost of reserved capacity even when idle | Cost of the minimum replica count, can scale toward zero but rarely truly zero |
| Cold start latency | Present, sometimes seconds, mitigated by warm reuse and provisioned concurrency | None, process is always running | Present but usually smaller, pod start from a warm node versus a cold node |
| Operational ownership of compute | Platform owns patching, scaling, placement entirely | Team owns the host, OS patching, autoscaling policy | Team owns the cluster, node pool, scheduler configuration, though not individual hosts |
| Max execution duration | Bounded, minutes not hours on most platforms | Unbounded, the process runs as long as it is kept alive | Unbounded, a pod can run indefinitely |
| Statefulness in process | Actively discouraged, execution environment reuse is not guaranteed | Fully supported, the process can hold state for its lifetime | Fully supported, though pod restarts still lose in-memory state |
| Vendor portability | Low, trigger and event shapes are vendor specific | High, a process is a process on any host | Moderate, Kubernetes itself is portable but managed add-ons and cloud integrations are not |
| Cost at sustained high, steady load | Can exceed a provisioned server, per-invocation margin adds up | Predictable and often cheaper at steady saturation | Predictable, similar to reserved instance economics |
| Granularity of deployment | Single function | Single service, coarser grained | Single service or a small set of containers per pod |

## 13. Related and incompatible patterns

**Idempotent Consumer.** The single most important companion pattern.
Because most FaaS triggers deliver events at-least-once, any function with a
side effect that is not naturally idempotent must apply Idempotent Consumer
explicitly, checking a durable idempotency key before applying the effect, or
the function will eventually double-process an event under retry. See
`patterns/10-microservices/idempotent-consumer.md` in this repository for the
full treatment.

**API Gateway.** The most common HTTP trigger for Serverless Deployment.
API Gateway sits in front of a set of functions, handling routing,
authentication, and request shaping, and hands a normalised event object to
the function, which is why the function's code rarely talks HTTP directly.
See `patterns/10-microservices/api-gateway.md`.

**Database per Service.** Serverless functions still need their state
somewhere, and the same ownership boundary that Database per Service argues
for at the service level applies to a function or a family of related
functions, avoiding a shared mutable table that many unrelated functions
write to without a clear contract.

**Transactional Outbox.** When a function needs to both update its own state
and publish an event as a result, the same dual-write hazard that
Transactional Outbox solves for a conventional service applies inside a
function too, and the fix is the same, write the event to be published in
the same transaction as the state change, then publish it out of band.

**Incompatible with Service Instance per Host, directly.** These two
patterns are mutually exclusive descriptions of the same layer of the
system, how a unit of compute is deployed and kept running. A workload is
either deployed as a long-lived process on a dedicated instance or it is
deployed as an ephemeral, platform-managed function, and a single workload
cannot be both at once, though a system can freely mix the two across
different services, using Service Instance per Host for a stateful core
service and Serverless Deployment for the bursty glue logic around it.

## 14. Refactoring path in and out

Introducing Serverless Deployment into a system that does not have it.

1. Identify a genuinely event-shaped, bursty piece of logic currently living
   inside a monolith or a long-running service, a webhook handler, an image
   resize step, a scheduled cleanup job, that has no dependency on
   in-process state accumulated over time.
2. Extract that logic into a self-contained handler with a single entry
   point, taking an event object in and returning a result, with every
   external dependency, a database, a queue, another service, addressed
   explicitly rather than through ambient in-process state.
3. Move any expensive setup, client construction, configuration parsing,
   that can safely run once and be reused, to module-level scope outside the
   handler, anticipating warm-start reuse.
4. Add explicit idempotency handling if the extracted logic has a side
   effect and the trigger it will run behind delivers at-least-once, per
   dimension 13.
5. Wire the platform's IAM role or managed identity for the function to the
   minimum permission set the extracted logic actually needs, not a copy of
   the broader service's existing role.
6. Deploy behind the appropriate trigger, an API Gateway route, a queue
   subscription, a storage event, a schedule, and run it alongside the
   existing code path with monitoring in place before cutting traffic over,
   consistent with the general strangler approach to extracting behaviour
   out of an existing system.
7. Remove the original in-process code path once the extracted function has
   run in production long enough to build confidence, including through at
   least one observed retry or throttling event so the idempotency and
   error handling are proven under real conditions, not only in a happy-path
   deploy.

Removing Serverless Deployment when it stops earning its place.

1. The clearest signal to remove it is sustained, steady, high-volume
   traffic where the per-invocation cost model has become more expensive
   than a provisioned alternative, or a workload that has grown past the
   platform's execution time or memory limit and now requires awkward
   decomposition purely to stay within platform limits rather than for any
   architectural benefit.
2. Package the function's handler logic as a conventional service entry
   point, an HTTP route handler or a queue consumer loop, with the same
   external dependency wiring already in place from the extraction, since
   the state was already externalised.
3. Reintroduce a persistent process, a container or a host, and move the
   trigger's routing, the API Gateway route, the queue subscription, to
   point at the new service instead of the function.
4. Keep the idempotency handling from dimension 13 in place even after
   removal, because at-least-once delivery semantics from most message
   brokers and queues do not disappear only because the compute layer changed.
   The property that made the function safe under retries is a property of
   the message delivery contract, not of FaaS specifically.
5. Decommission the function only after the replacement service has proven
   itself under the same peak load pattern that originally motivated moving
   away from a long-running process, since the operational reasons that made
   FaaS attractive, bursty, unpredictable load, may resurface if capacity
   planning for the new service is wrong.

## 15. Testing and verification

Unit testing a function's handler logic is genuinely easy, because the
pattern forces a clean boundary, an event object goes in, a result comes
out, with every external dependency, a database client, an HTTP client,
injected rather than reached for globally. This is one of the pattern's
quieter benefits, a well-written function handler is close to a pure
function once its dependencies are injected, and testing it does not require
standing up the platform at all.

What becomes harder is verifying behaviour that depends on the platform
itself. Cold start latency cannot be observed in a unit test, it requires a
deployed environment and repeated invocation after an idle period. Retry
semantics, whether an event is redelivered after a failure and how many
times, are a property of the trigger source, the queue or the event bus, not
of the function's code, and testing them requires either a local emulator
that faithfully reproduces the vendor's redelivery behaviour, which is
frequently imperfect, or an integration test against the real trigger in a
non-production account.

The specific technique that matters most for this pattern is testing
idempotency directly, a test that invokes the handler twice with the exact
same event payload and asserts the side effect, a database write, a
downstream call, happened exactly once, not twice. This single test is the
concrete verification of the idempotency guarantee the failure modes section
above depends on, and it is cheap to write because the handler boundary is
already clean.

Contract tests against the event shape the trigger will actually deliver are
worth writing explicitly, because the event object's shape is defined by the
platform and the trigger type, not by the team, and a mismatch between the
shape a test fixture assumes and the shape the platform actually sends is a
common source of production-only bugs that unit tests using a hand-written
fixture will not catch. Recording a real event payload from a staging
environment and using it as the fixture closes this gap.

## 16. Observability signals

The specific dashboards below reflect engineering judgement drawn from
common operational practice across the vendors cited in this entry, not a
single sourced specification.

- **Invocation count and error rate**, broken down by function, to see
  volume and health at the smallest unit of deployment the pattern offers.
- **Duration distribution, specifically the tail**, p95 and p99 duration,
  not the average, because cold starts show up as a distinct second mode in
  the latency histogram rather than as a shift in the mean.
- **Cold start rate and cold start duration as a distinct metric from total
  duration.** AWS's own init report log line, quoted in dimension 7's source
  documentation, exists specifically because init duration and invoke duration
  are different phases with different causes and different fixes, and
  conflating them in a dashboard hides the actual problem.
- **Throttling and concurrency-limit events.** A function silently
  throttled at its concurrency limit looks like dropped or delayed work
  downstream with no obvious error in the function's own logs, so this
  metric has to be pulled from the platform, not inferred from application
  logs.
- **Idempotency store hit rate**, the ratio of invocations that found an
  existing idempotency key versus a fresh one. A sudden spike in hits
  indicates the upstream trigger is retrying far more than expected, which
  usually points at a downstream dependency failing intermittently rather
  than at the function itself.
- **Dead-letter queue depth**, for any asynchronous trigger with a
  configured dead-letter destination, since a growing dead-letter queue is
  the clearest signal that some class of event is failing every retry
  attempt and needs manual intervention.

A healthy instance of this pattern shows a low, stable cold start rate
relative to invocation volume, a duration distribution with a tight p50 to
p95 spread, near zero throttling events, and a dead-letter queue that stays
at zero outside of genuine, understood failure incidents. A failing instance
shows a rising cold start rate, a fat latency tail, sustained throttling, or
a growing dead-letter queue with no corresponding alert firing, exactly the
gap the metrics above are meant to close.

## 17. Security and privacy implications

The framing below is engineering judgement, informed by the OWASP Serverless
Top 10 Project's stated position that infrastructure-layer security is the
platform's responsibility while application-layer correctness, including
access control, remains the function author's (OWASP Serverless Top 10
Project, owasp.org, verified 2026-08-02).

The pattern shrinks one attack surface and widens another. The platform
removes the operating system, the network stack, and the process supervisor
from the team's threat model entirely, no unpatched kernel, no exposed SSH
daemon, no long-lived process an attacker can pivot from once compromised,
because there effectively is no long-lived process to compromise. This is a
genuine security benefit and one of the pattern's underrated attractions for
teams with limited security operations staff.

What the pattern does not remove is application-level risk, and it
multiplies one specific category of it. Every function usually gets its
own execution role or managed identity, which means the number of distinct
privilege boundaries in a system grows with the number of functions rather
than staying fixed at the number of services. A team that grants a broad
role during initial development and never revisits it accumulates dozens or
hundreds of over-privileged functions, each a possible lateral-movement
path if any one function's input handling is exploited. This is the specific
risk called out in the failure modes section above, and it is structural to
the pattern rather than accidental.

Event-data injection is the FaaS-specific variant of classic input
validation risk. Because the function's entry point is an event object
assembled by the platform from an untrusted source, an HTTP body, a queue
message, an object's metadata, every field in that event is attacker
influenced input in exactly the way an HTTP request body is, and treating
platform-delivered event fields as implicitly trusted, because they arrived
through the platform's own trigger, rather than validating them the way any
other external input would be validated, is a recurring mistake this
pattern's popularity has made more common simply because there are more
functions, each with its own entry point, to get wrong.

Secrets handling deserves explicit mention because of the static
initialisation phase covered in dimension 7. Secrets fetched during static
init are cached in the warm execution environment for reuse across
invocations, which is the correct performance optimisation, but it means a
secret rotation does not take effect for any already-warm environment until
that environment is eventually recycled, a gap that must be accounted for
in any rotation runbook rather than assumed away.

## 18. References

1. Mike Roberts, "Serverless Architectures," martinfowler.com, 2018 revision.
   https://martinfowler.com/articles/serverless.html. Verified 2026-08-02.
2. AWS documentation, "Understanding the Lambda execution environment
   lifecycle." https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html.
   Verified 2026-08-02.
3. AWS documentation, Lambda execution environment lifecycle, cold start
   statistics and static initialisation optimisation sections, same URL as
   reference 2. Verified 2026-08-02.
4. Cloudflare developer documentation, "How Workers works."
   https://developers.cloudflare.com/workers/reference/how-workers-works/.
   Verified 2026-08-02.
5. Microsoft Learn, "Azure Functions scale and hosting options."
   https://learn.microsoft.com/en-us/azure/azure-functions/functions-scale.
   Verified 2026-08-02.
6. AWS Compute Blog, "Handling Lambda functions idempotency with AWS Lambda
   Powertools." https://aws.amazon.com/blogs/compute/handling-lambda-functions-idempotency-with-aws-lambda-powertools/.
   Verified 2026-08-02.
7. OWASP Serverless Top 10 Project, project overview page.
   https://owasp.org/www-project-serverless-top-10/. Verified 2026-08-02.
8. AWS, Lambda customer stories index, referenced for the iRobot and
   Coca-Cola production usage entries in dimension 9.
   https://aws.amazon.com/lambda/. Verified 2026-08-02.
9. Netflix Technology Blog, encoding pipeline architecture, referenced for
   the Netflix production usage entry in dimension 9.
   https://netflixtechblog.com/. Verified 2026-08-02.
10. Richardson, microservices.io entry for Idempotent Consumer, matching the
    citation already established in this repository's
    `idempotent-consumer.md` entry.

## Code examples

Three languages, each chosen because it is genuinely idiomatic for the
pattern in a different way. TypeScript, the dominant language for AWS Lambda
and Cloudflare Workers handlers and the one where module-scope reuse across
warm invocations is most commonly discussed. Python, AWS's own
idempotency-utility example language and a common choice for Lambda glue
code. Go, notable for very fast binary startup and package-level init
semantics that map directly onto the warm-reuse mechanics described in
dimension 7. C sharp, Kotlin, and Rust are omitted here, not because they
are unsupported by any vendor, but because none of them illustrates a
materially different facet of this pattern's core mechanic, warm-reuse of
module-or-package-scope state across invocations, beyond what the three
included languages already show.

Every example below models the platform boundary explicitly, an event comes
in through a plain object, a result goes out, with the platform's
orchestration layer represented by a small driver routine that simulates
cold start on the first call and warm reuse on the second, so the mechanic
from dimension 7's dynamics diagram is directly observable when the code
runs.

### TypeScript. a Lambda-style handler with explicit warm-reuse and idempotency

```typescript
// serverless_handler.ts
// A minimal store standing in for an external idempotency table (e.g. DynamoDB).
class IdempotencyStore {
  private seen = new Map<string, string>();

  hasProcessed(key: string): string | undefined {
    return this.seen.get(key);
  }

  record(key: string, result: string): void {
    this.seen.set(key, result);
  }
}

// Module-scope state. created once per execution environment, reused on warm
// invocations. This models the static-init phase from dimension 7.
let initCount = 0;
let store: IdempotencyStore;

function coldInit(): void {
  initCount += 1;
  store = new IdempotencyStore();
  console.log(`static init ran, count=${initCount}`);
}

interface OrderEvent {
  orderId: string;
  amountCents: number;
}

interface HandlerResult {
  statusCode: number;
  body: string;
}

// The function's single entry point. Pure with respect to its explicit
// dependency, the idempotency store, injected rather than reached for globally.
function handler(event: OrderEvent): HandlerResult {
  const existing = store.hasProcessed(event.orderId);
  if (existing !== undefined) {
    return { statusCode: 200, body: `duplicate, cached result. ${existing}` };
  }
  const result = `charged $${(event.amountCents / 100).toFixed(2)} for order ${event.orderId}`;
  store.record(event.orderId, result);
  return { statusCode: 200, body: result };
}

// A tiny orchestrator driver simulating cold start then warm reuse, matching
// the dynamics diagram in dimension 7.
function invoke(env: OrderEvent, isFirstInvocationInEnvironment: boolean): HandlerResult {
  if (isFirstInvocationInEnvironment) {
    coldInit();
  }
  return handler(env);
}

function main(): void {
  const event: OrderEvent = { orderId: "ord-42", amountCents: 1999 };

  const first = invoke(event, true);
  console.log("first invocation.", first.body);

  // Simulates the trigger's at-least-once redelivery of the same event
  // against the same still-warm environment.
  const retry = invoke(event, false);
  console.log("retry of same event.", retry.body);

  // A genuinely new event on the same warm environment.
  const second = invoke({ orderId: "ord-43", amountCents: 500 }, false);
  console.log("new event.", second.body);

  console.log(`total static-init calls. ${initCount}`);
}

main();
```

Compiled and run with `npx tsc --strict --target es2020 --module commonjs
serverless_handler.ts && node serverless_handler.js`. It prints one
"static init ran" line, confirming init ran once, the duplicate order
returning the cached result rather than a second charge, and the second,
distinct order being processed fresh, all against the same warm
environment.

### Python. an idempotent Lambda-style handler modelled on the AWS Powertools pattern

```python
"""serverless_handler.py
Models the AWS Lambda Powertools idempotency pattern, source cited in the
entry's dimension 11 and reference 6, using an in-memory dict in place of
the real DynamoDB-backed idempotency table.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class OrderEvent:
    order_id: str
    amount_cents: int


class IdempotencyStore:
    def __init__(self) -> None:
        self._seen: dict[str, str] = {}

    def get(self, key: str) -> Optional[str]:
        return self._seen.get(key)

    def put(self, key: str, result: str) -> None:
        self._seen[key] = result


# Module-level state, initialised once at import time. Reused across every
# warm invocation the process serves, mirroring the static-init phase.
_init_count = 0
_store: Optional[IdempotencyStore] = None


def _cold_init() -> None:
    global _init_count, _store
    _init_count += 1
    _store = IdempotencyStore()
    print(f"static init ran, count={_init_count}")


def handler(event: OrderEvent) -> dict:
    assert _store is not None, "handler invoked before static init"
    cached = _store.get(event.order_id)
    if cached is not None:
        return {"status": 200, "body": f"duplicate, cached result. {cached}"}
    result = f"charged ${event.amount_cents / 100:.2f} for order {event.order_id}"
    _store.put(event.order_id, result)
    return {"status": 200, "body": result}


def invoke(event: OrderEvent, first_invocation: bool) -> dict:
    if first_invocation:
        _cold_init()
    return handler(event)


def main() -> None:
    event = OrderEvent(order_id="ord-42", amount_cents=1999)

    first = invoke(event, first_invocation=True)
    print("first invocation.", first["body"])

    retry = invoke(event, first_invocation=False)
    print("retry of same event.", retry["body"])

    second = invoke(OrderEvent(order_id="ord-43", amount_cents=500), first_invocation=False)
    print("new event.", second["body"])

    print(f"total static-init calls. {_init_count}")


if __name__ == "__main__":
    main()
```

Run with `python3 serverless_handler.py`. Output matches the TypeScript
example's shape, one init call, a cached duplicate result on retry, and a
fresh result for the distinct event.

### Go. a package-scope warm-reuse example

```go
// serverless_handler.go
// Demonstrates warm-reuse via a package-level variable initialised once,
// the mechanic dimension 8 credits for Go's comparatively short cold starts.
package main

import "fmt"

type OrderEvent struct {
	OrderID     string
	AmountCents int
}

type idempotencyStore struct {
	seen map[string]string
}

func newIdempotencyStore() *idempotencyStore {
	return &idempotencyStore{seen: make(map[string]string)}
}

func (s *idempotencyStore) get(key string) (string, bool) {
	v, ok := s.seen[key]
	return v, ok
}

func (s *idempotencyStore) put(key, result string) {
	s.seen[key] = result
}

// Package-level state, created once per execution environment on cold init,
// reused on warm invocations.
var (
	store     *idempotencyStore
	initCount int
)

func coldInit() {
	initCount++
	store = newIdempotencyStore()
	fmt.Printf("static init ran, count=%d\n", initCount)
}

func handler(event OrderEvent) string {
	if cached, ok := store.get(event.OrderID); ok {
		return "duplicate, cached result. " + cached
	}
	dollars := float64(event.AmountCents) / 100.0
	result := fmt.Sprintf("charged $%.2f for order %s", dollars, event.OrderID)
	store.put(event.OrderID, result)
	return result
}

func invoke(event OrderEvent, firstInvocation bool) string {
	if firstInvocation {
		coldInit()
	}
	return handler(event)
}

func main() {
	event := OrderEvent{OrderID: "ord-42", AmountCents: 1999}

	fmt.Println("first invocation.", invoke(event, true))
	fmt.Println("retry of same event.", invoke(event, false))
	fmt.Println("new event.", invoke(OrderEvent{OrderID: "ord-43", AmountCents: 500}, false))
	fmt.Printf("total static-init calls. %d\n", initCount)
}
```

Run with `go run serverless_handler.go`. Output confirms the same
one-init, cached-retry, fresh-new-event pattern as the other two languages,
demonstrating that the warm-reuse mechanic in dimension 7's dynamics diagram
is a property of the deployment pattern, not of any one language's runtime.
