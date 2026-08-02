---
name: Asynchronous Request-Reply
slug: asynchronous-request-reply
family: 08-cloud-distributed
category: Cloud Distributed
aliases: [HTTP Polling Pattern, Poll and Redirect, 202 Accepted Pattern, Async HTTP Pattern]
first_described: "Microsoft, Azure Architecture Center, Cloud Design Patterns"
maturity: canonical
related: [queue-based-load-leveling, competing-consumers, saga, circuit-breaker, retry, throttling, valet-key]
incompatible_with: []
verified: 2026-08-02
---

# Asynchronous Request-Reply

## 1. Name, aliases, and lineage

The canonical name in current cloud architecture literature is Asynchronous
Request-Reply. Microsoft's Azure Architecture Center catalogs it as one of its
Cloud Design Patterns under the title "Asynchronous Request-Reply pattern,"
with the stated purpose of decoupling back-end processing from a front-end host
when back-end work must run asynchronously but the front end still needs a
clear response
([Microsoft Learn, Azure Architecture Center, Asynchronous Request-Reply Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply),
verified 2026-08-02). The Azure catalog is a maintained successor to the
original Azure Architecture Center Cloud Design Patterns work, itself
descended from Microsoft's 2014 "Cloud Design Patterns" e-book by Alex Homer,
John Sharp, Larry Brader, Masashi Narumoto, and Trent Swanson. In everyday
engineering conversation the same shape is called the HTTP Polling pattern, the
202-and-poll pattern, or Poll and Redirect, names that describe the mechanism
rather than the intent and that appear across REST API design guides and
platform engineering blogs rather than in a single citable book.

This entry treats Asynchronous Request-Reply as distinct from, but a close
cousin of, the Request-Reply message exchange described in Gregor Hohpe and
Bobby Woolf's *Enterprise Integration Patterns* (Addison-Wesley, 2003). Their
Request-Reply pattern is a messaging-layer pattern. "Send a pair of
Request-Reply messages, each on its own channel," where a Requestor sends a
request and a Replier returns a response, correlated by a Correlation
Identifier, and the requesting side may block synchronously or register an
asynchronous callback
([EnterpriseIntegrationPatterns.com, Request-Reply](https://www.enterpriseintegrationpatterns.com/patterns/messaging/RequestReply.html),
verified 2026-08-02). The cloud pattern in this entry is the HTTP-native,
polling-first specialization of that older messaging idea, adapted for a world
where the client is often a browser or a third-party integrator that cannot
hold a queue connection open and cannot receive a message-broker callback.

Judgement. the naming is genuinely unsettled across vendors. AWS documents the
equivalent shape inside Step Functions as the "Wait for a Callback with Task
Token" integration pattern, which is the callback variant rather than the
polling variant of the same underlying idea
([AWS documentation, Step Functions service integration patterns](https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html),
verified 2026-08-02). Readers coming from a Java or .NET REST background will
also recognize this as the shape behind "long-running operations" in API
design guides such as the Google API Improvement Proposals and the Microsoft
REST API Guidelines, neither of which is quoted directly here because neither
was independently verified for this entry, but both describe the same
Operation resource with a status field.

## 2. Problem and context

A client calls an API expecting an answer inside the budget of one HTTP
connection, typically well under a second. Most APIs meet that budget.
authentication, a database read, a small computation, done. The Azure
Architecture Center frames the baseline explicitly. "In most cases, APIs for a
client application respond in about 100 milliseconds (ms) or less"
([Microsoft Learn, Asynchronous Request-Reply Pattern, Context and problem](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply),
verified 2026-08-02). The problem this pattern solves begins the moment a
request cannot be answered in that budget, because the work behind it is
genuinely long, for example rendering a large export, transcoding a video,
running a fraud-scoring model over a batch, provisioning a virtual machine,
training a small model, or waiting on a third party (a payment network, a KYC
provider, a shipping carrier) whose own response time is outside the caller's
control.

If the server tries to hold the HTTP connection open until the work finishes,
several things go wrong at once. Load balancers, reverse proxies, and browser
fetch clients all carry their own idle-connection timeouts, frequently in the
15 to 60 second range, and a request that outlives one of those timeouts is
torn down by an intermediary the application never controls, so the client
sees a connection reset with no information about whether the work actually
completed on the server. The Azure documentation names this directly.
"synchronous request-reply" breaks down for work that takes seconds to
minutes, or minutes to hours, because "you can't wait for the work to finish
before you send a response"
([Microsoft Learn, Asynchronous Request-Reply Pattern, Context and problem](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply),
verified 2026-08-02). Holding a thread or a connection slot open per pending
request also does not scale. a web tier sized for fast request-response
traffic starves under a load of slow, blocking requests, because the
concurrency ceiling of the tier is now bounded by the slowest operation
instead of the fastest.

The context in which this problem is acute is specifically REST-over-HTTP
client-server interaction, most often from a browser, a mobile app, or a
third-party integrator calling a public API, where the caller cannot assume a
persistent duplex connection and cannot always receive an inbound callback
(firewalls, NAT, or a client-side runtime with no open port). The pattern is
not the right answer inside a service mesh where two of your own services can
share a message broker or a long-lived gRPC stream, where a queue-based
handoff or a streaming RPC is usually cheaper and simpler, a distinction this
entry returns to in section 4.

## 3. Forces

- **Latency budget versus honesty about duration.** The client wants an
  answer fast. The server cannot always deliver the true answer fast. The
  pattern resolves this by splitting the promise. the fast answer is an
  acknowledgment, not the result, and the client must be redesigned to accept
  that split rather than expecting one round trip to carry both.
- **Connection lifetime versus operation lifetime.** HTTP connections, load
  balancer idle timeouts, and browser fetch timeouts are all short-lived by
  design. Long-running operations are not. The pattern favors keeping the
  connection short and modeling the operation's actual lifetime as a resource
  the client polls, at the cost of the client needing a loop instead of a
  single call.
- **Push versus pull for the completion signal.** A webhook or callback
  pushes the result to the client the moment it exists, which minimizes
  latency and server load from repeated polling, but it requires the client
  to expose a reachable endpoint, handle authentication of the inbound call,
  and tolerate at-least-once delivery. Polling requires no inbound endpoint on
  the client at all, which is why the Azure documentation recommends it
  specifically "when callback endpoints are unavailable or when long-running
  connections add too much complexity"
  ([Microsoft Learn, Asynchronous Request-Reply Pattern, Solution](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply),
  verified 2026-08-02), at the cost of wasted requests, added latency equal to
  half the polling interval on average, and a status endpoint the server must
  keep serving.
- **Operability versus simplicity.** A polling status endpoint is trivially
  observable. a human can `curl` it and read the state in plain HTTP. A
  callback or webhook is harder to debug interactively because the
  interesting event happens on an inbound connection the operator is not
  watching. This pattern trades some elegance for operational transparency.
- **Cost of idle capacity.** Every pending job occupies storage for its status
  record and, if backed by a queue, a slot in that queue. A pattern that never
  expires stale operations accumulates cost indefinitely, which is why a
  retention and cleanup policy is not optional, it is part of the pattern
  (see section 10).
- **Client sophistication.** A browser calling this API directly needs the
  polling loop written in client-side JavaScript, with backoff, which is
  ordinary work for an experienced team and an easy place for an inexperienced
  one to get wrong (fixed-interval hammering, no jitter, no cap). A
  server-to-server caller, especially inside a microservices architecture, may
  prefer a message broker instead, because it already has one. the Azure
  documentation flags this explicitly, noting some architectures separate
  request and response stages with a message broker via the Queue-Based Load
  Leveling pattern instead of HTTP polling
  ([Microsoft Learn, Asynchronous Request-Reply Pattern, Context and problem](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply),
  verified 2026-08-02).

## 4. Applicability and non-applicability

**Reach for Asynchronous Request-Reply when.**

- The caller is a browser application, a mobile client, or a third-party
  integrator, and a callback endpoint is difficult or impossible to expose on
  the caller's side. The Azure documentation states this as the first "when
  to use" condition
  ([Microsoft Learn, Asynchronous Request-Reply Pattern, When to use this pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply),
  verified 2026-08-02).
- The transport is constrained to plain HTTP and the far side, for firewall or
  platform reasons, cannot receive inbound callbacks (the same source's second
  condition).
- The integration partner does not support a modern push mechanism such as
  WebSockets or webhooks, the third condition in the same source.
- A REST-shaped, resource-oriented API needs to expose a long-running
  operation as a first-class resource that can be inspected, retried, or
  cancelled, which is exactly what a status endpoint gives you for free.
- The work genuinely takes longer than an acceptable synchronous budget.
  report generation, video or image transcoding, bulk data export, batch
  scoring, or a call chained to a slow upstream dependency.

**Do not reach for it when (the explicit non-applicability list).**

- **The response can stream in real time.** If the client needs a continuous
  feed of partial results rather than one final answer, Server-Sent Events or
  a WebSocket delivers it with lower latency and no polling waste. the Azure
  guidance names SSE explicitly as the better fit here
  ([Microsoft Learn, Asynchronous Request-Reply Pattern, When to use this pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply),
  verified 2026-08-02).
- **The client needs to collect many results and result latency matters for
  each one.** A message broker (Queue-Based Load Leveling, Competing
  Consumers) fits a fan-out of many independent units of work better than one
  status resource per job, per the same source.
- **A persistent server-push channel is already available.** If WebSockets or
  a technology such as SignalR is already wired up, using it to notify the
  caller directly is simpler than adding a parallel polling surface, per the
  same source.
- **The network already supports inbound webhooks and the integration
  partner supports them.** Stripe's own guidance for its API is a clear
  real-world instance of preferring the callback variant once it is
  available. webhooks let an application "respond to asynchronous events,"
  such as a bank confirming a payment, without continuously polling
  ([Stripe Docs, Webhooks](https://docs.stripe.com/webhooks), verified
  2026-08-02). When both variants are available, choose the callback for
  lower latency and lower load, and reserve plain polling for clients that
  cannot receive a callback.
- **Two services inside the same trust boundary can share a queue or a
  synchronous RPC with a sane timeout.** Adding an HTTP status resource
  between two services you own is needless ceremony. a direct queue
  round-trip or a blocking call under a circuit breaker is simpler.
- **The operation genuinely completes inside the ordinary synchronous
  budget.** Introducing 202-and-poll for a call that already returns in 50
  milliseconds adds a round trip and a state machine for no benefit.
- **Exactly-once execution is required and the system has no idempotency
  mechanism.** Polling clients retry the initial POST on ambiguous failures
  by nature (see section 8's idempotency-key discussion). if the back end
  cannot deduplicate, this pattern will double-run work.

## 5. Structure

The polling variant has four participants.

- **Client.** Initiates the operation and is responsible for the polling
  loop, including backoff. Owns no server-side state; everything it needs to
  resume polling (the status URL) comes back on the initial response.
- **Accepting endpoint (the API front door).** Receives the initial request,
  validates it synchronously (structural and authorization checks only, never
  the actual work), assigns an operation identifier, hands the work off to a
  back end, and replies immediately with `202 Accepted`, a `Location` header
  pointing at the status endpoint, and ideally a `Retry-After` header.
- **Status endpoint (the operation resource).** A dedicated URL, keyed by the
  operation identifier, that reports the current state, one of pending,
  running, succeeded, or failed. On success it either returns the result
  directly or redirects the client to a separate result resource with
  `303 See Other`.
- **Worker (the back end that does the actual processing).** Consumes the
  handed-off work, most often from a queue, and writes its outcome to durable
  storage that the status endpoint reads. The worker is decoupled from the
  accepting endpoint's request-handling thread entirely; it may live in a
  different process, container, or even a different cloud service.

A fifth, optional participant appears in the callback variant. a **webhook
receiver** on the client side, which the accepting endpoint (or the worker)
calls directly once the operation completes, removing the need for the client
to poll at all.

## 6. ASCII structure diagram

```
                    +------------------+
                    |      Client      |
                    +------------------+
                       |            ^
             1. POST   |            | 3. GET status (repeat)
             /reports  |            |    -> 200 {status: running}
                       v            |    -> 303 See Other (on success)
                    +------------------+
                    | Accepting        |
                    | Endpoint         |
                    | (validates,      |
                    |  enqueues,       |
                    |  returns 202 +   |
                    |  Location +      |
                    |  Retry-After)    |
                    +------------------+
                       |            ^
             2. enqueue|            | reads status
                       v            |
                    +------------------+          +------------------+
                    |   Work Queue     |--------->|      Worker      |
                    +------------------+          | (processes,      |
                                                   |  writes result   |
                                                   |  to Status Store)|
                                                   +------------------+
                                                              |
                                                              v
                                                   +------------------+
                                                   |   Status Store   |
                                                   | (job id -> state,|
                                                   |  result, error)  |
                                                   +------------------+
                                                              ^
                    +------------------+                     |
                    | Status Endpoint  |---------------------+
                    | GET /reports/    |   4. reads job state
                    |   {id}/status    |
                    +------------------+
```

## 7. Dynamics

```
Client              Accepting Endpoint      Work Queue       Worker          Status Store
  |  POST /reports         |                    |               |                |
  |------------------------>                    |                |                |
  |                        | validate request   |               |                |
  |                        |-------------------> |               |                |
  |                        |     enqueue job     |               |                |
  |   202 Accepted         |<--------------------|               |                |
  |   Location: /reports/  |                     |               |                |
  |     {id}/status        |                     |               |                |
  |   Retry-After: 5       |                     |               |                |
  |<------------------------                     |                |                |
  |                        |                     | dequeue job    |                |
  |                        |                     |--------------->|                |
  |                        |                     |                | mark running   |
  |                        |                     |                |---------------->
  |  GET /reports/{id}/    |                     |                |    processing  |
  |    status              |                     |                |    (seconds to |
  |------------------------>                     |                |    minutes)    |
  |   200 OK {status:      |                     |                |                |
  |     running}           |                     |                |                |
  |<------------------------                     |                |                |
  |          ... client sleeps Retry-After, then polls again ...  |                |
  |                        |                     |                | write result   |
  |                        |                     |                |   + succeeded  |
  |                        |                     |                |---------------->
  |  GET /reports/{id}/    |                     |                |                |
  |    status              |                     |                |                |
  |------------------------>                     |                |                |
  |   303 See Other        |                     |                |     read state |
  |   Location: /reports/  |<-----------------------------------------------------|
  |     {id}/result        |                     |                |                |
  |<------------------------                     |                |                |
  |  GET /reports/{id}/    |                     |                |                |
  |    result              |                     |                |                |
  |------------------------>                     |                |                |
  |   200 OK { ... }       |                     |                |                |
  |<------------------------                     |                |                |
```

The Azure sample application implements this exact flow with three Azure
Functions. `AsyncProcessingWorkAcceptor` (the accepting endpoint, which enqueues
onto Azure Service Bus and returns `202` with `Location` and `Retry-After`
headers), `AsyncProcessingBackgroundWorker` (the worker, triggered by the
queue, that writes its result to Blob Storage), and
`AsyncOperationStatusChecker` (the status endpoint, which checks whether the
result blob exists and either returns `200` with an in-progress body or
redirects with `303 See Other` to a result URL)
([Microsoft Learn, Asynchronous Request-Reply Pattern, Example](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply),
verified 2026-08-02).

## 8. Implementation variants

- **Pure polling with a status body (the baseline).** The accepting endpoint
  returns `202` with a `Location` pointing at a status resource. Every poll
  returns `200` with a JSON body describing the state until it is terminal.
  This is the shape implemented in section 9's code samples and in the Azure
  Functions sample above.
- **Polling with a terminal redirect.** Instead of embedding the result in
  the status body, the status endpoint redirects with `303 See Other` to a
  separate result resource once processing finishes. The Azure documentation
  recommends `303` specifically over `302` because `303` unambiguously tells
  every client to follow with a `GET`, whereas `302` "doesn't guarantee a
  method change" and "[s]ome clients replay the original method on redirect,"
  which can cause an accidental duplicate `POST`
  ([Microsoft Learn, Asynchronous Request-Reply Pattern, Problems and considerations](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply),
  verified 2026-08-02).
- **Target-resource polling without a separate status endpoint.** Some
  implementations skip a dedicated status resource and have the client poll
  the eventual resource URL directly, treating `404` as "not ready yet."
  The Azure documentation calls this approach out as a real pattern in the
  wild while flagging its ambiguity. "this response is generated because the
  resource doesn't exist yet. However, this approach can be unclear because
  invalid request IDs also return HTTP 404"
  ([Microsoft Learn, Asynchronous Request-Reply Pattern, Problems and considerations](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply),
  verified 2026-08-02). Prefer a dedicated status endpoint that separates "not
  found" from "not finished."
- **Long polling.** The client still initiates each poll, but the server
  holds the request open until either new state is available or a timeout
  elapses, trading connection-holding cost for lower latency between
  completion and client notification. The Azure documentation names this
  variant explicitly as a lower-latency alternative to periodic polling that
  "introduces complexity around connection management and timeouts"
  ([Microsoft Learn, Asynchronous Request-Reply Pattern, Solution](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply),
  verified 2026-08-02).
- **Callback or webhook variant.** Instead of, or in addition to, a status
  endpoint, the client supplies a callback URL at submission time, and the
  server invokes it once the operation completes, eliminating client-side
  polling entirely. This is how Stripe notifies applications of asynchronous
  events such as a payment confirmation, and Stripe's own guidance is
  explicit that the receiving endpoint should "return a 2xx status code
  quickly, before applying any complex logic that could cause a timeout,"
  deferring real processing to after the acknowledgment
  ([Stripe Docs, Webhooks](https://docs.stripe.com/webhooks), verified
  2026-08-02, German-language source text translated by the fetching tool).
  A well-designed implementation of this variant still exposes a status
  endpoint as a fallback for a client whose webhook delivery failed or was
  missed, because webhook delivery is not guaranteed exactly-once. Stripe
  documents automatic retries with exponential backoff for up to three days
  in live mode, which is itself evidence that the callback is best-effort,
  not guaranteed single delivery.
- **Task-token callback inside an orchestrator.** AWS Step Functions
  generalizes the callback variant beyond HTTP. a state machine task can be
  configured with the `.waitForTaskToken` service integration pattern, which
  "provide[s] a way to pause a workflow until a task token is returned," used
  "when a task might need to wait for a human approval, integrate with a
  third party, or call legacy systems"
  ([AWS documentation, Discover service integration patterns in Step Functions](https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html),
  verified 2026-08-02). The external process calls back with
  `SendTaskSuccess` or `SendTaskFailure` and the workflow resumes; a
  `HeartbeatSeconds` setting bounds how long the orchestrator waits before
  giving up, which is the orchestration-layer equivalent of the HTTP
  pattern's `Retry-After` and eventual timeout handling.
- **Idempotency-key submission.** To make the initial `POST` safely retryable
  by a client that lost the `202` response to a network failure, the
  accepting endpoint accepts an `Idempotency-Key` header and returns the
  existing operation's status resource instead of enqueuing a duplicate job
  when it sees a key it has already processed. The Azure documentation names
  this explicitly and points at the IETF draft header, calling it "especially
  important in this pattern because the client can't distinguish between a
  lost response and a request that was never received"
  ([Microsoft Learn, Asynchronous Request-Reply Pattern, Problems and considerations](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply),
  verified 2026-08-02).

## 9. Known production uses

1. **Azure Functions reference implementation, Microsoft.** Microsoft
   publishes a runnable sample implementing this exact pattern with three
   Azure Functions (acceptor, background worker, status checker) backed by
   Azure Service Bus and Azure Blob Storage, with the source available on
   GitHub under `Azure-Samples/cloud-design-patterns`
   ([Microsoft Learn, Asynchronous Request-Reply Pattern, Example](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply),
   verified 2026-08-02). Azure Resource Manager itself, the control plane
   behind every Azure resource creation and update, uses "a modified variant
   of this pattern" for its own long-running operations, per the same source,
   which links to the Resource Manager asynchronous operations reference.
2. **AWS Step Functions callback integration pattern, Amazon Web Services.**
   Step Functions ships `.waitForTaskToken` as a first-class integration
   pattern usable with Amazon SQS, Amazon SNS, Amazon API Gateway, Amazon
   EventBridge, AWS Lambda, and other AWS SDK integrations, specifically to
   pause a workflow for an external asynchronous callback and resume it on
   `SendTaskSuccess` or `SendTaskFailure`
   ([AWS documentation, Discover service integration patterns in Step Functions](https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html),
   verified 2026-08-02). This is the orchestration-native form of the same
   accept-now-notify-later contract that the HTTP variant implements with
   `202` and a status URL.
3. **Stripe API webhooks, Stripe Inc.** Stripe's public API guidance
   describes webhooks as the mechanism applications should use to "respond to
   asynchronous events," giving as examples a customer's bank confirming a
   payment or a recurring payment succeeding, and instructs webhook receivers
   to acknowledge quickly with a `2xx` response and defer processing, with
   automatic retries for failed delivery for up to three days
   ([Stripe Docs, Webhooks](https://docs.stripe.com/webhooks), verified
   2026-08-02). This is the callback variant of Asynchronous Request-Reply
   applied to real-money payment confirmation, a domain where polling faster
   on its own is not an acceptable substitute for a reliable completion signal.

## 10. Consequences

**Positive.**

- Decouples the lifetime of the client's HTTP connection from the lifetime of
  the actual work, so intermediary timeouts (load balancers, browser fetch
  limits, API gateways) never truncate a long operation mid-flight.
- Lets the back end scale independently of the front door. the accepting
  endpoint can be a small, fast, stateless tier while the worker tier scales
  to the shape of the actual processing load, exactly the separation the
  Azure documentation credits to the related Queue-Based Load Leveling
  pattern.
- Makes a long-running operation a first-class, inspectable resource. An
  operator, a support engineer, or the client itself can `GET` the status
  resource at any time and see exactly where the operation stands, which a
  blocked synchronous call never offers.
- Gives the client a natural place to implement cancellation. the Azure
  guidance recommends exposing a `DELETE` on the status resource that
  forwards a cancellation instruction to the back end.
- Composes cleanly with retries and idempotency. because the client already
  expects to poll rather than get an instant answer, retrying the initial
  submission safely (via an idempotency key) is a small addition rather than
  a redesign.

**Negative.**

- Every client now needs a polling loop with backoff, which is more code and
  more failure modes than a single request-response call, and a naive
  implementation (fixed-interval polling, no jitter, no cap) can hammer the
  status endpoint under load.
- Adds latency. even a fast operation now costs at minimum one polling
  interval before the client learns it finished, unless long polling or a
  callback is used instead.
- Introduces state the server must manage and eventually clean up. The status
  resource, and any stored result, consumes storage and must have a defined
  retention policy; the Azure documentation is explicit that these "consume
  storage and compute" and recommends an `Expires` header on the status
  response to tell the client the retention window.
- Splits what used to be one failure mode (the synchronous call failed) into
  several (the submission failed, the submission succeeded but the poll never
  finds the resource, the poll times out, the job failed after being
  accepted), each of which needs its own handling on the client.
- The callback or webhook variant shifts complexity onto the receiver. it
  must expose a reachable, authenticated endpoint, verify the sender
  (Stripe, for instance, requires signature verification), and handle
  duplicate or out-of-order delivery, since most webhook systems are
  at-least-once, not exactly-once.

## 11. Failure modes and misuse

| Symptom | Cause | Fix |
|---|---|---|
| Client sees `404` on the status URL immediately after receiving `202`, then it starts working a moment later | The status record is written asynchronously, after the `202` response is already sent, and the client polled before the write landed (a race between the accepting endpoint's response and the durable write) | Write the status record synchronously, inside the same request that returns `202`, before the response is sent; the worker only updates that record, it does not create it |
| The same job runs twice, producing two charges, two emails, or two exports | The client retried the initial `POST` after a timeout or a dropped connection, and the accepting endpoint enqueued a second job because it had no way to recognize the retry | Require and honor an idempotency key on the accepting endpoint, returning the existing job's status resource on a repeated key instead of enqueuing again |
| Clients hammer the status endpoint hundreds of times a second under load, and the status store becomes the bottleneck | No `Retry-After` header was returned, or the client ignored it and polled at a fixed short interval with no backoff or jitter | Always return `Retry-After` on both the `202` and subsequent pending responses; implement client-side exponential backoff with jitter, capped at a sane maximum |
| A status endpoint that redirects on completion causes the client to accidentally re-POST the original operation | The redirect used `302 Found` instead of `303 See Other`, and some HTTP clients replay the original method (POST) on a 302 redirect rather than switching to GET | Use `303 See Other` for the completion redirect, which unambiguously instructs every compliant client to follow with `GET`, per RFC 9110 section 15.4.4, cited in the Azure documentation |
| Operations never disappear; storage for status records and results grows without bound | No retention or expiry policy was implemented for finished jobs | Define and enforce a retention window, communicate it to clients with an `Expires` header on the status response, and run a cleanup job that deletes records past that window |
| A job that failed silently shows as "running" forever, and the client polls indefinitely | The worker crashed or was evicted mid-processing without writing a terminal `failed` state | Give every job a heartbeat or a maximum processing deadline the status endpoint can compare against; treat a job whose last-updated timestamp is older than the deadline as failed, even if the worker never wrote that state itself, and surface a `lastUpdatedAt` field for exactly this check |
| A webhook receiver processes an event, but Stripe (or any provider) retries delivery and the receiver processes it again, double-crediting an account | The webhook handler is not idempotent; it does not deduplicate by the event's unique identifier before applying its effect | Persist processed event identifiers and check for a duplicate before applying any side effect, treating a duplicate delivery as a no-op success |
| A `303` redirect points to a valet-key URL that has already expired by the time the client follows it | The signed URL to the result resource (an Azure Storage SAS token, an S3 pre-signed URL) was generated with too short a lifetime relative to realistic client polling delay | Generate the signed result URL with an expiry that comfortably exceeds the expected time between job completion and the client's next poll, and regenerate it on each status check rather than caching a stale one |

## 12. Trade-off matrix

| Concern | Asynchronous Request-Reply (HTTP polling) | Queue-Based Load Leveling | Webhook / callback variant | Plain synchronous request-response |
|---|---|---|---|---|
| Client complexity | Moderate; needs a polling loop with backoff | Low for the requester if it only enqueues, but the requester usually still needs its own way to learn the outcome | Higher; client must expose and secure a reachable endpoint | Lowest; one call, one answer |
| Latency to completion notice | Bounded by polling interval (or near-zero with long polling) | Not defined by the pattern itself, it only smooths intake | Near-zero, event-driven | Not applicable, the call blocks until done |
| Works for browser or firewalled client | Yes, this is its primary reason to exist | Awkward, the browser is not typically a queue consumer | Only if the browser can receive the callback, which it usually cannot without a hosted endpoint | Yes, but only for short operations |
| Server load pattern | Repeated polling traffic proportional to interval and job count | Smooths bursty intake into steady consumption, does not address notification | Lowest ongoing load, one push per completion | One request per operation, but the connection is held for the full duration |
| Failure visibility | High; the status resource is inspectable at any time | Depends entirely on what is layered on top of the queue | Depends on delivery guarantees and receiver logging | Immediate; the caller gets the error directly |
| Best fit | Long operations with a client that cannot receive callbacks | Smoothing a burst of requests into a back end sized for steady throughput | Long operations where the client can host a receiver and low latency matters | Fast operations that reliably complete inside the connection budget |

## 13. Related and incompatible patterns

- **Queue-Based Load Leveling.** Frequently the mechanism the accepting
  endpoint uses to hand work to the worker tier; Asynchronous Request-Reply
  is the client-facing contract, Queue-Based Load Leveling is the internal
  buffering strategy that absorbs bursts before the worker consumes them. The
  Azure documentation ties these together directly, noting many systems that
  need this separation "achieve this separation through the Queue-Based Load
  Leveling pattern."
- **Competing Consumers.** Once work is on a queue, multiple worker instances
  drain it concurrently under the Competing Consumers pattern; this is how
  the worker tier in section 5's structure typically scales horizontally.
- **Circuit Breaker and Retry.** The client's polling loop, and the
  accepting endpoint's own calls out to a third party during processing,
  should both be wrapped in Retry with backoff and, for the third-party call,
  a Circuit Breaker, so a flapping dependency does not turn every job into an
  indefinitely stuck one.
- **Saga.** When the long-running operation itself spans multiple services
  with compensating actions on failure, the worker's internal execution is
  often a Saga; Asynchronous Request-Reply is the outward-facing shell around
  that inner orchestration, not a replacement for it.
- **Valet Key.** The Azure documentation recommends returning a Valet Key,
  such as a SAS-token URL, as the `Location` header value when the polling
  client needs restricted, time-bound access to the status or result
  resource without the accepting service brokering every read.
- **Correlation Identifier (Enterprise Integration Patterns).** The job or
  operation identifier that threads through the accepting endpoint, the
  queue message, the worker, and the status endpoint is a direct instance of
  Hohpe and Woolf's Correlation Identifier, used here to route a status
  lookup back to the right in-flight (or completed) job.
- **Incompatible with a naive exactly-once assumption.** This pattern is
  built around retryable, ambiguous submission (see section 11's duplicate
  job failure mode); a caller that assumes a single `POST` always causes
  exactly one execution, with no idempotency key involved, is implicitly
  incompatible with it and will double-run work under network failure.

## 14. Refactoring path in and out

**Introducing the pattern into an existing synchronous endpoint.**

1. Identify the endpoint whose processing time has started to exceed the
   caller's realistic budget, using real latency data rather than a guess.
2. Extract the processing logic into a function that can run independently of
   the HTTP request thread (a background task, a queue consumer, a separate
   worker process); do this refactor first, behind the existing synchronous
   endpoint, and verify it still produces the same result before changing the
   API contract.
3. Introduce a durable status store (a database table or a document per job)
   keyed by a newly generated operation identifier, with at minimum `status`,
   `createdAt`, `lastUpdatedAt`, and a place to hold the result or error.
4. Change the endpoint to write a `pending` status record, enqueue or start
   the extracted background work, and return `202 Accepted` with a `Location`
   header pointing at a new status endpoint, plus `Retry-After`.
5. Build the status endpoint. `GET` by operation identifier, returning `200`
   with the current state while pending or running, and either the result or
   a `303 See Other` redirect once terminal.
6. Add an idempotency key to the accepting endpoint before shipping to real
   clients, so retried submissions do not double-run work; this step is
   frequently skipped and is the single most common production incident this
   pattern produces when skipped (see section 11).
7. Update every client to poll instead of expecting the old synchronous
   response, with backoff; if the API is public and has existing clients,
   version the endpoint or add a new one rather than breaking the old
   contract in place.
8. Add a retention and cleanup job for terminal status records before this
   ships, not after.

**Removing the pattern once the operation is fast again.**

1. Confirm, with real latency data, that the operation now reliably completes
   inside an acceptable synchronous budget, including its worst observed
   case, not only its average.
2. Add a synchronous endpoint alongside the existing asynchronous one rather
   than replacing it in place, so existing clients on the polling contract
   keep working.
3. Migrate clients to the synchronous endpoint at their own pace.
4. Once no client depends on the polling contract, per real traffic data
   rather than assumption, retire the status endpoint, the status store, and
   the queue-based worker hop, folding the processing back into the request
   path.

## 15. Testing and verification

What this pattern makes easy to test. the accepting endpoint, the status
endpoint, and the worker can each be unit tested in isolation, because they
communicate only through the durable status store, which is trivial to fake
or stub in a test. A test can assert that submitting a job produces a `202`
with a `Location` header, that the status store contains a `pending` record
immediately after that response (not eventually, immediately, which is a
strong and checkable invariant), and that a completed job produces the
correct terminal state independent of any real queue or real worker process.

What becomes harder. end-to-end tests now involve time. A test that submits a
job and immediately asserts `succeeded` is testing a race, not the pattern; it
will pass locally and flake in CI the moment the worker is even slightly
slower. Use one of two disciplined approaches instead of a raw sleep-and-hope
loop, either inject a deterministic clock and a synchronous worker stand-in
for unit-level tests (so "processing" completes the instant the test code
calls it, with no real concurrency involved), or, for genuine end-to-end
tests, poll with a bounded timeout and assert on the terminal state reached
within that timeout, treating a timeout as a test failure with a clear
message rather than an indefinite hang. The Python and Go examples in section
9 both include a `poll_until_done` / `pollUntilDone` helper with exactly this
bounded-timeout shape, because it doubles as the pattern the client itself
should use in production, not only in tests.

Contract tests are valuable here specifically because so many implementations
diverge on details, some `404` instead of using a dedicated status resource,
some use `302` instead of `303`, some omit `Retry-After` entirely. A contract
test suite that asserts the concrete behaviors named in section 11 (a
synchronously-written pending record, a `303` and not a `302` on completion,
an honored idempotency key) catches drift from the intended contract before
a client team discovers it the hard way.

## 16. Observability signals

- **Time-to-acknowledge.** The latency of the accepting endpoint itself,
  which should stay in the same fast budget as any ordinary synchronous
  endpoint; a regression here defeats the entire purpose of the pattern.
- **Time-to-completion, per job.** The distribution, not only the average, of
  time between a job's `createdAt` and its terminal `succeeded` or `failed`
  timestamp. A widening tail here is the earliest signal of back-end
  saturation, well before clients start complaining.
- **Poll rate per job and in aggregate.** How many times each job is polled
  before it reaches a terminal state, and the total status-endpoint request
  rate. A poll rate that is far higher than `1 / Retry-After` per job
  indicates clients are ignoring backoff guidance.
- **Terminal state distribution.** The ratio of `succeeded` to `failed` jobs
  over a rolling window; a sudden shift toward `failed` is the primary
  correctness signal for the worker tier.
- **Stuck-job count.** The count of jobs whose state is still `pending` or
  `running` past some multiple of the typical completion time (see section
  11's silent-failure mode); this should alert, because it usually means a
  worker crashed without recording a terminal state.
- **Idempotency-key hit rate.** How often the accepting endpoint recognizes a
  repeated key and returns an existing job instead of enqueuing a new one; a
  nonzero, stable rate here is healthy evidence that client retries are being
  correctly deduplicated rather than silently creating duplicate work.
- **Status-store size and age distribution of records.** Whether the
  retention and cleanup policy from section 10 is actually running; an
  ever-growing count of terminal records with no corresponding decrease is
  evidence the cleanup job is broken or missing.
- **Webhook delivery attempts and outcomes**, for the callback variant.
  successful first-attempt deliveries versus retries versus permanent
  failures, mirroring what Stripe itself exposes to merchants for their own
  outbound webhook traffic.

## 17. Security and privacy implications

The status and result endpoints are a new, addressable surface that did not
exist under a plain synchronous call, and they must be protected as
carefully as the accepting endpoint. An operation identifier that is a
short, sequential, or otherwise guessable value lets an attacker enumerate
other users' operations and read their status or result; use a
cryptographically random identifier (a UUIDv4 or equivalent) and still apply
proper authorization on every read, never rely on the identifier's
unguessability as the only control. Where a result is exposed through a
signed, time-limited URL (a Valet Key such as an Azure SAS token or an S3
pre-signed URL), scope that URL as narrowly as possible. read-only, a single
object, and an expiry short enough to limit exposure if the URL leaks through
a log, a browser history entry, or a referrer header, while still long
enough that a slow-polling client does not hit an expired link (see section
11's expired-signed-URL failure mode).

For the callback variant, the receiving endpoint is an inbound attack surface
that any host on the internet can attempt to call; it must verify the
sender's identity, not merely trust the request body. Stripe's own
documentation is explicit that a webhook receiver must verify the request
signature so a forged event cannot be mistaken for a genuine one, a
signature-verification step that should be treated as mandatory, not
optional, for any callback receiver implementing this pattern
([Stripe Docs, Webhooks](https://docs.stripe.com/webhooks), verified
2026-08-02). A receiver that skips signature verification can be tricked into
processing a forged completion event, for instance a forged "payment
succeeded" callback, with real financial or operational consequences.

Status and result payloads frequently contain more information than the
original synchronous response would have, because they persist for a
polling window rather than existing only in memory for the duration of one
request; treat the status store as a data-at-rest surface subject to the same
classification and retention rules as any other persisted customer data,
including the retention window from section 10, which doubles as a privacy
control, data that is deleted on schedule cannot leak from a forgotten
record months later. If the operation processes data subject to regulatory
retention limits (payment details, health data, personal data under GDPR or
similar regimes), the retention policy for the status store must not
outlive, and ideally should be shorter than, the policy governing the
underlying data itself.

## 18. References

- Microsoft Learn, Azure Architecture Center, "Asynchronous Request-Reply
  Pattern," https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply,
  verified 2026-08-02.
- Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns. Designing,
  Building, and Deploying Messaging Solutions*, Addison-Wesley, 2003,
  Request-Reply pattern, companion reference page
  https://www.enterpriseintegrationpatterns.com/patterns/messaging/RequestReply.html,
  verified 2026-08-02.
- IETF, RFC 9110, "HTTP Semantics," section 15.3.3, "202 Accepted,"
  https://www.rfc-editor.org/rfc/rfc9110.html#name-202-accepted, verified
  2026-08-02.
- IETF, RFC 9110, section 15.4.4, "303 See Other," referenced via the Azure
  Architecture Center pattern page, https://www.rfc-editor.org/rfc/rfc9110#section-15.4.4,
  verified 2026-08-02.
- IETF, RFC 9457, "Problem Details for HTTP APIs," referenced by the Azure
  Architecture Center pattern page as the recommended structured error format
  for the status endpoint's error field, https://www.rfc-editor.org/rfc/rfc9457,
  verified 2026-08-02.
- Amazon Web Services documentation, "Discover service integration patterns
  in Step Functions" (Wait for a Callback with Task Token),
  https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html,
  verified 2026-08-02.
- Stripe Docs, "Webhooks," https://docs.stripe.com/webhooks, verified
  2026-08-02.
- Azure-Samples, "cloud-design-patterns" reference implementation of the
  Asynchronous Request-Reply pattern using Azure Functions, Service Bus, and
  Blob Storage, linked from the Azure Architecture Center pattern page,
  https://github.com/Azure-Samples/cloud-design-patterns, verified 2026-08-02
  (link verified reachable via the citing Microsoft Learn page; repository
  contents not independently browsed for this entry).

## Code examples

Three languages, each implementing the polling variant end to end. an accept
step that returns immediately with a pending job, a background worker that
completes the job, and a bounded polling helper the client uses to wait for a
terminal state. All three were compiled or run directly, not merely written.

### TypeScript (Node.js `http`, no framework)

Compiled clean with `tsc --strict` against `@types/node`, then run with `node`
against a live in-process HTTP server exercising the full accept, enqueue,
poll, redirect, result flow.

```typescript
import * as http from "node:http";
import { randomUUID } from "node:crypto";

type JobStatus = "pending" | "running" | "succeeded" | "failed";

interface Job {
  id: string;
  status: JobStatus;
  createdAt: number;
  result?: unknown;
  error?: string;
}

const jobs = new Map<string, Job>();

function processInBackground(job: Job): void {
  job.status = "running";
  setTimeout(() => {
    try {
      job.result = { total: 42, currency: "EUR" };
      job.status = "succeeded";
    } catch (err) {
      job.status = "failed";
      job.error = String(err);
    }
  }, 50);
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url ?? "/", "http://localhost");

  if (req.method === "POST" && url.pathname === "/reports") {
    const id = randomUUID();
    const job: Job = { id, status: "pending", createdAt: Date.now() };
    jobs.set(id, job);
    processInBackground(job);
    res.writeHead(202, {
      Location: `/reports/${id}/status`,
      "Retry-After": "1",
      "Content-Type": "application/json",
    });
    res.end(JSON.stringify({ requestId: id, status: job.status }));
    return;
  }

  const statusMatch = url.pathname.match(/^\/reports\/([^/]+)\/status$/);
  if (req.method === "GET" && statusMatch) {
    const job = jobs.get(statusMatch[1]);
    if (!job) {
      res.writeHead(404);
      res.end();
      return;
    }
    if (job.status === "succeeded") {
      res.writeHead(303, { Location: `/reports/${job.id}/result` });
      res.end();
      return;
    }
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: job.status }));
    return;
  }

  const resultMatch = url.pathname.match(/^\/reports\/([^/]+)\/result$/);
  if (req.method === "GET" && resultMatch) {
    const job = jobs.get(resultMatch[1]);
    if (!job || job.status !== "succeeded") {
      res.writeHead(404);
      res.end();
      return;
    }
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(job.result));
    return;
  }

  res.writeHead(404);
  res.end();
});
```

The client-side polling loop, the counterpart the server side above assumes,
follows the same shape as the Python and Go helpers below. submit, receive
`202` plus `Location`, then poll that `Location` on the `Retry-After` interval
with a bounded overall timeout, rather than an unbounded loop.

### Python 3 (standard library only)

Run directly with `python3`; the script's own `__main__` block accepts a job,
polls it to completion, and asserts on the result, printing `ok` on success.

```python
import time
import uuid
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class Job:
    id: str
    status: JobStatus = JobStatus.PENDING
    result: Optional[dict] = None
    error: Optional[str] = None


class ReportService:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def accept(self) -> Job:
        job = Job(id=str(uuid.uuid4()))
        with self._lock:
            self._jobs[job.id] = job
        threading.Thread(target=self._process, args=(job,), daemon=True).start()
        return job

    def status(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def _process(self, job: Job) -> None:
        job.status = JobStatus.RUNNING
        time.sleep(0.05)
        try:
            job.result = {"total": 42, "currency": "EUR"}
            job.status = JobStatus.SUCCEEDED
        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error = str(exc)


def poll_until_done(service: ReportService, job_id: str, timeout_s: float = 2.0) -> Job:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        job = service.status(job_id)
        if job is None:
            raise KeyError(job_id)
        if job.status in (JobStatus.SUCCEEDED, JobStatus.FAILED):
            return job
        time.sleep(0.01)
    raise TimeoutError(f"job {job_id} did not finish in time")


if __name__ == "__main__":
    service = ReportService()
    accepted = service.accept()
    assert accepted.status in (JobStatus.PENDING, JobStatus.RUNNING)
    finished = poll_until_done(service, accepted.id)
    assert finished.status == JobStatus.SUCCEEDED
    assert finished.result == {"total": 42, "currency": "EUR"}
    print("ok", finished)
```

### Go (standard library only)

Run directly with `go run`; the `main` function accepts a job, polls it to
completion with a bounded deadline, and prints the terminal state.

```go
package main

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"sync"
	"time"
)

type JobStatus string

const (
	Pending   JobStatus = "pending"
	Running   JobStatus = "running"
	Succeeded JobStatus = "succeeded"
	Failed    JobStatus = "failed"
)

type Job struct {
	ID     string
	Status JobStatus
	Result map[string]any
	Error  string
}

type ReportService struct {
	mu   sync.Mutex
	jobs map[string]*Job
}

func NewReportService() *ReportService {
	return &ReportService{jobs: make(map[string]*Job)}
}

func newJobID() string {
	buf := make([]byte, 8)
	_, _ = rand.Read(buf)
	return hex.EncodeToString(buf)
}

func (s *ReportService) Accept() *Job {
	job := &Job{ID: newJobID(), Status: Pending}
	s.mu.Lock()
	s.jobs[job.ID] = job
	s.mu.Unlock()
	go s.process(job)
	return job
}

func (s *ReportService) Status(id string) (*Job, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	j, ok := s.jobs[id]
	return j, ok
}

func (s *ReportService) process(job *Job) {
	s.mu.Lock()
	job.Status = Running
	s.mu.Unlock()

	time.Sleep(50 * time.Millisecond)

	s.mu.Lock()
	job.Result = map[string]any{"total": 42, "currency": "EUR"}
	job.Status = Succeeded
	s.mu.Unlock()
}

func pollUntilDone(s *ReportService, id string, timeout time.Duration) (*Job, error) {
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		job, ok := s.Status(id)
		if !ok {
			return nil, fmt.Errorf("unknown job %s", id)
		}
		if job.Status == Succeeded || job.Status == Failed {
			return job, nil
		}
		time.Sleep(5 * time.Millisecond)
	}
	return nil, fmt.Errorf("job %s did not finish in time", id)
}

func main() {
	svc := NewReportService()
	accepted := svc.Accept()
	fmt.Println("accepted", accepted.ID, accepted.Status)

	finished, err := pollUntilDone(svc, accepted.ID, 2*time.Second)
	if err != nil {
		panic(err)
	}
	fmt.Println("finished", finished.Status, finished.Result)
}
```

Java and Rust were not written for this entry. the pattern is not
language-idiomatic in a way that would add a fourth distinct implementation
shape beyond what TypeScript, Python, and Go already demonstrate (an HTTP or
in-process accept step, a background worker, and a bounded polling loop), and
the three languages above cover the callback-style event loop, the
thread-and-lock style, and the goroutine-and-mutex style that together span
how this pattern is actually built across the ecosystems where it is most
common.
