---
name: Gatekeeper
slug: gatekeeper
family: 08-cloud-distributed
category: Security
aliases: [Broker Pattern, Validating Gateway, Bastion Broker]
first_described: "Microsoft patterns & practices, Cloud Design Patterns guide, 2014"
maturity: established
related: [gateway-offloading, gateway-routing, gateway-aggregation, valet-key, federated-identity, quarantine, sidecar, rate-limiting-pattern]
incompatible_with: []
verified: 2026-08-03
---

# Gatekeeper

## 1. Name, aliases, and lineage

The canonical name is Gatekeeper. Microsoft's patterns & practices team published it as one of
twenty four patterns in the original Cloud Design Patterns guide in 2014, filed under the
Security category, and it survives in the current Azure Architecture Center pattern catalog under
the same name and category (Microsoft, Azure Architecture Center, "Gatekeeper Pattern," verified
2026-08-03, https://learn.microsoft.com/en-us/azure/architecture/patterns/gatekeeper). The Azure
Architecture Center's own definition states the pattern's job in one sentence. protect
applications and services "by using a dedicated component to broker requests between clients and
the application or service," where the broker "validates and sanitizes the requests" before
anything reaches the workload (same source).

The pattern's older lineage sits in network security rather than software architecture. The idea
of a single hardened host standing between an untrusted network and a protected one predates cloud
computing by decades and is documented under the name bastion host. Marcus J. Ranum's 1992 paper
on firewall design, republished on his own site and widely cited in security literature, describes
a bastion host as "a system identified by the firewall administrator as a critical strong point in
the network's security," a machine that receives "extra attention paid to their security" and
"regular audits" precisely because it sits exposed to the untrusted side of a boundary (Marcus J.
Ranum, "Thinking About Firewalls," 1992, cited via Wikipedia, "Bastion host," verified
2026-08-03, https://en.wikipedia.org/wiki/Bastion_host). Gatekeeper is the same idea moved into
application architecture. instead of a hardened machine guarding a subnet, it is a hardened,
minimally privileged process guarding an API surface, a data store, or a set of internal services.

Because the underlying idea is old and general, the name Gatekeeper is also used for at least one
concrete, well known implementation that is not the same thing as the architectural pattern this
entry describes. OPA Gatekeeper, a Kubernetes admission controller built on the Open Policy Agent
engine, hosted by the CNCF. OPA Gatekeeper "enforces CRD-based policies executed by Open Policy
Agent" and intercepts every create, update, and delete request the Kubernetes API server receives,
deciding to allow, deny, or warn before the change is persisted (Open Policy Agent, "Gatekeeper
documentation," verified 2026-08-03, https://open-policy-agent.github.io/gatekeeper/website/docs/).
OPA Gatekeeper is a specific, named production instance of the general Gatekeeper pattern applied
to the Kubernetes control plane rather than to an application's own API, and it is discussed as
one of the production uses in dimension 9. This entry is about the architectural pattern; readers
searching for the Kubernetes tool specifically should treat this entry as the pattern it
implements, not as documentation of the tool itself.

Aliases in practice include broker pattern (the Azure Architecture Center's own solution
description calls the component "a broker" between client and workload), validating gateway
(used informally where teams want to distinguish it from a routing-only gateway), and bastion
broker, a term this entry uses to name the specific combination of bastion host isolation with
application level request brokering, since no single standard term for that combination exists in
the literature surveyed.

## 2. Problem and context

A cloud service exposes one or more API endpoints across an untrusted network, typically the
public internet. The code that implements those endpoints usually does more than one job at once.
it authenticates the caller, authorizes the specific operation, validates and parses the request
body, and then goes on to read or write storage, call other internal services, or use credentials
that grant broad access to the backend. The Azure Architecture Center names this concentration of
responsibility as the root of the problem. "the code that implements the APIs triggers or performs
several tasks, including but not limited to authentication, authorization, parameter validation,
and some or all request processing," and that same code path "is likely to access storage and
other services on the client's behalf" (Microsoft, Azure Architecture Center, "Gatekeeper Pattern,"
verified 2026-08-03).

The failure this creates is not merely that a bug might exist in the API code. It is that the single
process handling untrusted input is also the process holding the keys. If an attacker finds any
exploitable flaw in that process, an injection point, a deserialization bug, a path traversal, an
authentication bypass, they do not just compromise a request handler, they land inside a process
that already has live credentials to storage accounts, queues, databases, and any other service
account the workload uses. The Azure Architecture Center states this plainly. if "a malicious user
compromises the system and gains access to the application's hosting environment, its security
mechanisms and access to data and other services are exposed," giving the attacker "unrestricted
access to credentials, storage keys, sensitive information, and other services" (same source).

The context in which this problem is sharpest is any system where the following three conditions
hold simultaneously. First, the endpoint is reachable from a network the operator does not fully
trust, usually the public internet, sometimes a large internal network with many tenants. Second,
the backend that the endpoint eventually calls holds sensitive data, high value credentials, or the
ability to perform an operation with real world consequences, a payment, a data mutation, an
infrastructure change. Third, the request handling code is complex enough that a defect in it is
plausible. it parses untrusted input, evaluates business rules, or composes calls to multiple
downstream systems. Where any of those three conditions is weak, for instance a purely internal
service with no untrusted input, the case for a dedicated Gatekeeper weakens correspondingly, a
point developed further in dimension 4.

## 3. Forces

Every force below pulls the design in a direction, and the Gatekeeper pattern is a specific,
named resolution of the tension between them, not a way to make the tension disappear.

**Coupling versus isolation.** A single request handling process that both talks to the client and
talks to the backend is tightly coupled to both roles. Splitting the two into a validating front
process and a privileged back process reduces the blast radius of a compromise in the front
process, at the direct cost of adding a network hop, a serialization boundary, and a second
component to build, deploy, and keep patched. The Gatekeeper pattern favors isolation over the
convenience of one process doing everything.

**Latency versus validation depth.** Every check the gatekeeper performs, schema validation, rate
limiting, authentication, payload sanitization, before forwarding a request costs time. A
security minded team wants deep, expensive validation; a latency sensitive workload wants the
fewest possible hops and the cheapest possible checks. The pattern favors validation depth and
accepts the latency cost, which is exactly why the Azure Architecture Center lists "adding the
extra layer to implement the Gatekeeper pattern is likely to affect performance because of the
extra processing and network communication required" as an explicit consideration (same source).

**Availability versus a single point of failure.** Routing all traffic through one broker tier
creates a natural chokepoint. If that tier is unavailable, every downstream operation it fronts
becomes unreachable even though the backend itself may be perfectly healthy. The Microsoft
documentation names this directly. "the gatekeeper can be a single point of failure (SPoF)," and
recommends "deploying redundant instances and using an autoscaling mechanism" to keep capacity and
availability intact as the mitigation (same source). The pattern accepts this risk in
exchange for centralizing the security surface, and pushes the burden of eliminating the SPoF onto
redundancy and autoscaling rather than pretending the risk away.

**Operational cost versus attack surface reduction.** Running a second tier, with its own
deployment pipeline, its own on call rotation, its own certificates, and its own scaling policy, is
strictly more operational work than running one tier. The pattern trades that ongoing cost for a
measurably smaller attack surface on the privileged backend, because the backend no longer accepts
any connection from the untrusted network at all; only the gatekeeper can reach it.

**Privilege minimization versus feature velocity.** The gatekeeper, by design, is not supposed to
touch storage or perform business logic; the Azure Architecture Center states that "the gatekeeper
shouldn't perform processing related to the application or services or access data. Its function
is solely to validate and sanitize requests" (same source). Keeping the gatekeeper's job narrow
keeps its own privilege minimal, which is the entire point, but it also means every new business
capability that needs a new kind of validation touches two components instead of one, slowing
feature velocity relative to a monolithic handler.

**Team topology.** A gatekeeper tier that is deliberately generic, doing authentication, schema
validation, and rate limiting for many backend services, tends to be owned by a platform or
security team rather than the feature teams that own the backends it protects. This split lowers
the coordination cost of getting security review right once instead of per feature team, at the
cost of a dependency. a feature team cannot ship a new endpoint's validation rules without going
through whichever team owns the gatekeeper tier, or the gatekeeper tier must expose a
self service way for feature teams to declare their own validation rules.

## 4. Applicability and non-applicability

**Reach for Gatekeeper when.**

- The system handles sensitive information, PII, payment data, health data, or credentials, and a
  direct compromise of the request handling code would expose that data or the keys to it. The
  Azure Architecture Center lists "you handle sensitive information" as the first condition for
  using the pattern (Microsoft, Azure Architecture Center, "Gatekeeper Pattern," verified
  2026-08-03).
- The service is exposed to a network you do not fully control, most commonly the public internet,
  and needs strong protection from malicious or malformed traffic, matching the second listed
  condition, "you expose services that require strong protection from malicious traffic" (same
  source).
- The operation behind the endpoint is mission critical and cannot tolerate the backend being
  directly reachable, matching "you perform mission-critical operations that can't tolerate direct
  exposure of back-end services" (same source).
- Request validation and sanitization genuinely need to be a separate concern from core business
  processing, for instance because the validation rules are shared across many backend services, or
  because a security or compliance team must own and audit the validation logic independently of
  the teams that own business logic, matching the fourth listed condition (same source).
- A regulatory or contractual requirement mandates that backend systems holding regulated data are
  never directly reachable from an untrusted network, which is common in payment card processing
  and healthcare contexts and is naturally satisfied by keeping the backend's endpoints internal
  only, as the pattern requires.

**Do not reach for Gatekeeper when.**

- The backend service's own platform already provides the validation and security controls you
  need without a dedicated tier, in which case adding a gatekeeper duplicates work the platform
  already does. The Azure Architecture Center states plainly that the pattern "might not be
  suitable when you can satisfy security and validation requirements through built-in platform
  controls on the back-end service without adding a dedicated gatekeeper tier" (same source).
- The system has a strict end to end latency budget that the added network hop and validation work
  would violate; the same source lists "added network hops and validation latency violate strict
  end-to-end latency requirements" as a case where the pattern is a poor fit.
- The service is purely internal, reachable only from a small number of known, already trusted
  callers inside a private network with no untrusted ingress, so there is no untrusted request
  stream to broker in the first place. Adding a gatekeeper here adds a hop and an availability risk
  with no corresponding security gain.
- The team lacks the operational capacity to run a second tier with its own redundancy and scaling,
  because an under resourced gatekeeper becomes the single point of failure the pattern already
  warns about, without delivering the isolation benefit that justifies the risk.
- The data or operation behind the endpoint is genuinely low value, public, and idempotent, so a
  compromise of the request handler would not expose anything worth protecting; the cost of the
  extra tier is not repaid by a proportional reduction in risk.
- The system already terminates untrusted traffic at a managed edge that performs equivalent
  validation, for example a fully managed API gateway with schema validation, authentication, and
  rate limiting built in, and the backend is never directly reachable regardless. Here the managed
  edge is functioning as the gatekeeper already; standing up a second, custom one is redundant
  unless the managed edge cannot express the specific validation the workload needs.

## 5. Structure

The pattern names four participants, though production systems frequently split the trusted host
role into more than one internal tier, described further under dimension 8.

**Client.** Any caller on the untrusted side of the boundary. a browser, a mobile app, a
third party integration, or another organization's server. The client only ever knows the
gatekeeper's address; it has no knowledge of, and no network path to, the trusted host.

**Gatekeeper.** A dedicated component, running with the minimum privilege needed to receive and
inspect a request. Its responsibilities are exactly three. accept the request on a public or
semi public endpoint, validate and sanitize it (structural validation, authentication, rate
limiting, payload inspection), and forward only the requests that pass validation to the trusted
host over an internal channel. The gatekeeper holds no credentials for storage or downstream
services; if it needs to authenticate the caller, it does so against an identity provider, not
against the resource the request ultimately touches.

**Trusted host (also called the key master in the original guide's diagram, and internally
called the backend in most real systems).** The component that holds the actual credentials,
storage keys, database connections, or service account tokens needed to perform the requested
operation. It exposes only an internal endpoint, one reachable exclusively from the gatekeeper's
network segment, never from the client's network. It may perform its own additional validation,
but the Azure Architecture Center is explicit that "the gatekeeper should perform the core
validation," leaving the trusted host free to assume the request has already been sanitized for
the common cases, while still practicing defense in depth for anything gatekeeper specific
validation would miss (Microsoft, Azure Architecture Center, "Gatekeeper Pattern," verified
2026-08-03).

**Services and data.** The storage accounts, databases, message queues, or downstream APIs that
the trusted host is the only participant authorized to reach directly.

The relationship between these participants is strictly one directional and strictly layered. the
client can only reach the gatekeeper, the gatekeeper can only reach the trusted host, and the
trusted host is the only participant that can reach services and data. No participant is allowed
to skip a layer. This is the property the pattern is built to enforce, and it is also the property
every failure mode in dimension 11 comes from violating, even slightly.

## 6. ASCII structure diagram

```
                     UNTRUSTED NETWORK
        (internet, third-party callers, mobile clients)
                            |
                            v
+---------------------------------------------------------+
|                       CLIENT(S)                          |
+---------------------------------------------------------+
                            |
                    public endpoint only
                            |
                            v
+-----------------------------------------------------------+
|                       GATEKEEPER                           |
|  - authenticates the caller                                 |
|  - validates schema, size, and content of the request       |
|  - applies rate limiting and abuse checks                   |
|  - holds NO storage keys, NO downstream service credentials |
|  - runs in a limited-privilege compute boundary              |
+-----------------------------------------------------------+
                            |
                internal-only endpoint
             (private network, mTLS, or VNet)
                            |
                            v
+-----------------------------------------------------------+
|                     TRUSTED HOST                            |
|  - performs the actual business operation                    |
|  - holds credentials for storage and downstream services     |
|  - never exposes a public endpoint                            |
|  - may run additional, backend-specific validation           |
+-----------------------------------------------------------+
                            |
                 credentialed, internal calls
                            |
                            v
+-----------------------------------------------------------+
|                  SERVICES AND DATA                          |
|          (storage, database, queue, downstream APIs)         |
+-----------------------------------------------------------+
```

## 7. Dynamics

The runtime flow is a single request pipeline with a hard trust boundary in the middle. The
sequence below traces one request from an untrusted client through to a completed response,
including the two decision points where the gatekeeper can short circuit the flow.

```
Client               Gatekeeper                Trusted Host          Services/Data
  |                      |                            |                    |
  |--- HTTPS request --->|                            |                    |
  |                      |-- authenticate caller       |                    |
  |                      |-- validate schema/size      |                    |
  |                      |-- rate-limit check           |                    |
  |                      |                            |                    |
  |                      | [request fails validation]  |                    |
  |<--- 4xx response ----|                            |                    |
  |                      |                            |                    |
  |                      | [request passes validation] |                    |
  |                      |-- forward sanitized req --->|                    |
  |                      |   (internal channel, mTLS)  |                    |
  |                      |                            |-- extra backend    |
  |                      |                            |   validation       |
  |                      |                            |-- fetch/mutate --->|
  |                      |                            |<-- result ---------|
  |                      |<---- backend response ------|                    |
  |<--- 2xx response ----|                            |                    |
  |                      |                            |                    |
```

The critical property this diagram is meant to make visible is that the client's connection
terminates entirely at the gatekeeper. There is no pass through TCP or HTTP tunnel from client to
trusted host; the gatekeeper originates a fresh, separate connection to the trusted host only after
it has independently decided the request is safe to forward. This is what makes the gatekeeper a
broker rather than a transparent proxy. a transparent reverse proxy forwards bytes with limited
inspection, while a gatekeeper terminates, inspects, and reconstructs the request before the second
hop, which is exactly the distinction Azure's own description draws when it says the gatekeeper
"acts like a firewall in a typical network topography," except that "unlike a traditional
firewall, it allows the gatekeeper to examine requests in detail and make an application-driven
decision about whether to pass the request to the trusted host" (Microsoft, Azure Architecture
Center, "Gatekeeper Pattern," verified 2026-08-03).

A second dynamic worth naming explicitly is the layered variant Azure's current documentation
recommends for production systems, where the single gatekeeper box in dimension 6 is itself split
into an outer and inner layer with different scopes of trust. In the worked example on the current
Azure Architecture Center page, an outer layer (a web application firewall in front of an
application gateway) inspects all internet facing traffic and blocks obviously malicious payloads,
such as SQL injection and cross site scripting patterns, before anything reaches an inner layer (an
API management gateway) that applies API specific policy, such as JWT validation and rate limiting,
before finally forwarding only approved traffic to a private backend (same source). The two layers
compose the same trust narrowing dynamic twice in sequence rather than once.

## 8. Implementation variants

**Single process gatekeeper in front of a private backend.** The simplest form. one HTTP service
that terminates public traffic, validates and authenticates, then makes an internal call (HTTP,
gRPC, or a message published to an internal queue) to a backend service reachable only on a
private network or via a private endpoint. This is the shape shown in the diagrams above and the
shape demonstrated in the code samples in dimension 9's companion listings.

**Layered gatekeeper (WAF plus API gateway).** As described in dynamics, an edge layer handling
network and payload level threats (a web application firewall, DDoS protection) sits in front of a
second, API aware layer handling authentication, schema validation, and policy (an API gateway).
Azure's current worked example composes Azure Application Gateway with Web Application Firewall as
the outer layer and Azure API Management as the inner layer, each emitting its own logs, with only
the inner layer's approved traffic reaching a private App Service backend behind a private endpoint
(Microsoft, Azure Architecture Center, "Gatekeeper Pattern," verified 2026-08-03). This variant
trades one extra hop and one extra component for the ability to reason about network level and
application level threats with two specialized tools rather than one generalist.

**Sidecar gatekeeper.** Instead of a standalone tier, the validating logic runs as a sidecar
process co located with each backend instance, intercepting all inbound traffic to that instance
before it reaches the application code, commonly implemented with a service mesh proxy such as
Envoy. This variant keeps the isolation property, the application code never sees unvalidated
traffic directly, while avoiding a separate, independently scaled tier; the trade-off is that the
sidecar shares the failure domain (the same pod or VM) as the backend it protects, which is a
weaker isolation guarantee than a fully separate compute boundary.

**Serverless authorizer as gatekeeper.** A managed API gateway invokes a small, stateless function
as a pluggable authorization and validation step before routing the request onward. AWS API Gateway
Lambda authorizers are the clearest named instance. the gateway "checks if the method request is
configured with a Lambda authorizer" and, if so, "calls the Lambda function," which "authenticates
the caller" and "returns an IAM policy and a principal identifier"; only if the returned policy
allows the request does API Gateway "invoke the method" (Amazon Web Services, "Use API Gateway
Lambda authorizers," AWS API Gateway Developer Guide, verified 2026-08-03,
https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html).
This is a gatekeeper implemented as a narrowly scoped function rather than a long running service,
and it pushes the operational cost of running redundant gatekeeper instances entirely onto the
managed platform.

**Admission controller as gatekeeper for control plane operations.** Instead of guarding a data
plane API, the gatekeeper sits in front of a control plane, validating and potentially rejecting
requests before they are persisted as system state. OPA Gatekeeper is the concrete instance. it
runs as "both a validating and mutating admission controller," intercepting every Kubernetes API
request to create, update, or delete a resource, evaluating it against declared policy before the
change reaches etcd (Open Policy Agent, "Gatekeeper documentation," verified 2026-08-03). This
variant generalizes the pattern from protecting a business API to protecting any system whose
state changes flow through a single, interceptable choke point.

**Language idiomatic notes.** The pattern has no meaningfully different shape by language; it is an
architectural, process level boundary rather than a code level construct, so there is no closure
based or functional variant analogous to how Strategy collapses into a lambda. The only language
level variation that matters is which HTTP or RPC framework a given ecosystem reaches for to
implement the two hops, which is why the code examples in this entry are written at the level of a
minimal HTTP server rather than tied to a specific framework.

## 9. Known production uses

**Azure Application Gateway with Web Application Firewall, layered in front of Azure API
Management, in front of a private Azure App Service backend.** This is Microsoft's own documented
reference architecture for the pattern. the WAF layer "inspects internet-facing traffic and applies
security controls before traffic reaches the API tier," detecting and blocking "SQL injection and
cross-site scripting patterns," enforcing "protocol and request-size rules," and applying "bot and
IP-based filtering," while API Management applies "API-specific controls" such as JWT validation
and rate limiting and forwards "only approved traffic to private back ends" that remain reachable
solely through a private endpoint (Microsoft, Azure Architecture Center, "Gatekeeper Pattern,"
verified 2026-08-03).

**OPA Gatekeeper on Kubernetes, a CNCF hosted project.** Deployed as a validating and mutating
admission webhook, it intercepts every API server request that would create, modify, or delete a
cluster resource and evaluates it against CRD defined policies executed by the Open Policy Agent
engine, denying, warning on, or auditing violations "without blocking changes" when run in audit
only mode (Open Policy Agent, "Gatekeeper documentation," verified 2026-08-03,
https://open-policy-agent.github.io/gatekeeper/website/docs/). This is a named, widely deployed,
CNCF governed implementation of exactly the broker and validate role the pattern describes, applied
to a control plane instead of a business API.

**AWS API Gateway with a Lambda authorizer fronting private backend integrations.** API Gateway
receives the client request, invokes a Lambda function that authenticates the caller "by calling
out to an OAuth provider," "by calling out to a SAML provider," or "by generating an IAM policy
based on the request parameter values," and only forwards the request to the backend integration
once that function returns an Allow policy; a Deny policy or a missing policy causes API Gateway to
return a 403 or 401 without the backend integration ever being invoked (Amazon Web Services, "Use
API Gateway Lambda authorizers," AWS API Gateway Developer Guide, verified 2026-08-03). The
authorizer function runs with narrowly scoped IAM permissions of its own, distinct from the
credentials the backend integration uses, matching the pattern's requirement that the gatekeeper
component hold different, lesser privileges than the trusted host it fronts.

## 10. Consequences

**Positive.**

- The privileged backend's credentials, storage keys, and downstream service tokens are never
  exposed to the network segment that receives untrusted traffic, so a compromise of the internet
  facing tier does not automatically hand an attacker those credentials, per the Azure
  Architecture Center's stated benefit that "if the gatekeeper becomes compromised, attackers can't
  access these credentials or keys" (Microsoft, Azure Architecture Center, "Gatekeeper Pattern,"
  verified 2026-08-03).
- Validation, authentication, and abuse detection logic is centralized in one auditable tier
  instead of being scattered across every backend service, which lets a security or platform team
  review, test, and update that logic once rather than per service.
- Rate limiting and throttling become cheaper to implement correctly, because the Azure
  Architecture Center's Well Architected Framework notes observe that "you can use this pattern to
  implement throttling at a gatekeeper level rather than implement rate checks at the node level,"
  avoiding the coordination cost of "rate state coordination among all nodes" (same source).
- Observability improves at the boundary. every request that enters the system passes through one
  place, which is a natural point to emit a correlation ID, structured logs, and consistent metrics
  before the request fans out into the rest of the system, as described in dimension 16.

**Negative.**

- Latency increases because of the added network hop and the validation work itself, an effect the
  Azure Architecture Center calls out directly under problems and considerations (same source).
- The gatekeeper tier is a new single point of failure if it is not independently made redundant
  and autoscaled; an outage there takes down every backend it fronts even if those backends are
  healthy (same source).
- Operational surface area grows. there is now a second deployable, a second set of certificates or
  service identities, a second thing to patch, monitor, and put on call rotation for.
- The separation is only as strong as the network boundary enforcing it. If the trusted host's
  internal endpoint is ever accidentally exposed, made reachable from the untrusted network, or
  reachable through a misconfigured peering or a shared broad security group, the entire benefit of
  the pattern evaporates while the extra hop and cost remain, a failure mode covered in dimension
  11.
- Feature velocity slows slightly for any change that needs new validation rules, since it now
  spans two components and, depending on team topology, may cross a team boundary.

## 11. Failure modes and misuse

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | The trusted host is reachable directly from the internet during an incident, bypassing the gatekeeper entirely, discovered via a security scan or a penetration test. | The trusted host's endpoint was given a public IP, an overly broad security group, or a load balancer rule that was never removed after a migration, so the isolation the pattern depends on was never actually enforced at the network layer. | Enforce the internal only requirement mechanically, not by convention. put the trusted host behind a private endpoint or a network policy that denies all ingress except from the gatekeeper's identity or subnet, and add an automated, recurring network reachability check that fails a deploy or pages on call if the trusted host becomes reachable from outside. |
| 2 | The gatekeeper itself is compromised and the attacker still gets useful access, even though it was supposed to be free of privileged credentials. | The gatekeeper was given broader privileges than validation requires, commonly because a developer added a quick database read to the gatekeeper for convenience, or reused the trusted host's service account instead of provisioning a scoped one. | Audit the gatekeeper's IAM role or service account on every deploy for any grant beyond what authentication, schema validation, and rate limiting require; treat any storage, database, or downstream service credential appearing in the gatekeeper's configuration as a defect. |
| 3 | The system experiences a full outage even though the trusted host and backend services report healthy. | The gatekeeper tier has no redundancy, no autoscaling, or a single replica behind a load balancer with no health check, so it becomes the single point of failure the pattern documentation explicitly warns about. | Run the gatekeeper across multiple availability zones with autoscaling triggered on both CPU and request queue depth, and alert independently on gatekeeper tier health separate from backend health so an operator can distinguish a front door outage from a house outage. |
| 4 | Legitimate traffic is intermittently rejected with 4xx errors that do not correspond to any real client error, and the rejection rate correlates with total traffic volume rather than with any specific bad payload. | The gatekeeper's validation rules are too strict for legitimate edge cases, most often a schema that was written against a narrow sample of real traffic, or a rate limit set without headroom for legitimate bursty clients. | Run new or changed validation rules in a shadow, log only mode against production traffic before enforcing them, comparing the would be reject rate against the current reject rate before flipping enforcement on. |
| 5 | Requests take significantly longer to complete after the gatekeeper tier was introduced, and the increase is disproportionate to the validation work being performed. | The gatekeeper opens a new TCP or TLS connection to the trusted host on every request instead of reusing a connection pool, or performs a blocking, unbounded external call, such as a synchronous OAuth token introspection request, on the hot path for every single request. | Use a persistent, pooled connection between the gatekeeper and the trusted host, and cache or locally validate tokens where the token format allows it, for example verifying a signed JWT locally instead of calling an introspection endpoint on every request. |
| 6 | The gatekeeper performs business logic, such as computing a derived value or making a decision that depends on current backend state, and that logic drifts out of sync with the trusted host's own copy of the same logic over time. | The line between validate and sanitize and process the request was not enforced, so a developer added a convenience shortcut, computing something in the gatekeeper because it was faster than round tripping to the backend, which is exactly what the Azure Architecture Center's explicit consideration against the gatekeeper performing "processing related to the application or services" warns against (Microsoft, Azure Architecture Center, "Gatekeeper Pattern," verified 2026-08-03). | Treat any logic in the gatekeeper that depends on backend state, rather than on the request in isolation, as a defect; move it to the trusted host and have the gatekeeper forward the minimum information the trusted host needs to make the same decision itself. |
| 7 | An attacker successfully forges the gatekeeper's identity when calling the trusted host, for instance by spoofing a source IP or a header the trusted host trusted as proof of gatekeeper origin. | The internal channel between gatekeeper and trusted host relies on a weak trust signal, an IP allowlist alone, or a static shared secret in a header, rather than mutual authentication. | Use mutual TLS or a short lived, cryptographically verifiable service identity token between the gatekeeper and the trusted host, so the trusted host authenticates the gatekeeper's identity cryptographically rather than trusting network position or a static header value alone. |

## 12. Trade-off matrix

The comparison below evaluates Gatekeeper against three named, closely related alternatives across
the forces named in dimension 3. Gateway Offloading and Gateway Routing are two of the three
gateway patterns Azure catalogs alongside Gatekeeper; a Web Application Firewall deployed alone,
without an application aware inner layer, is included because it is the single most common thing
teams reach for instead of a full gatekeeper.

| Force | Gatekeeper | Gateway Routing | Gateway Offloading | WAF alone (no inner layer) |
|---|---|---|---|---|
| Isolation of privileged credentials from untrusted network | Strong. Backend holds no public endpoint and the gatekeeper holds no backend credentials. | Weak. A routing gateway forwards requests to whichever backend matches a rule, but does not remove the backend's own need to validate and it commonly still shares a trust domain with the backends it routes to. | Moderate. Offloading (TLS termination, compression, caching) removes repetitive work from every backend, but the offloading gateway is not designed to make an application aware allow or deny decision about payload content. | Moderate to strong for network and payload level threats, but the WAF alone does not narrow the backend's reachability; a misconfigured backend can still be reached directly unless a separate network control enforces it. |
| Depth of request validation | Deep. Purpose built for authentication, schema validation, and sanitization as its sole job. | Shallow. Primarily URL and header based routing decisions, not payload validation. | Shallow to none by design; offloading is about cost and performance, not content inspection. | Deep for known attack signatures (SQLi, XSS) but shallow for application specific schema or business rule validation. |
| Added latency | One extra hop, plus validation cost. | One extra hop, routing cost is typically negligible. | Often reduces backend latency by moving TLS and compression off the backend, though it adds its own hop. | One extra hop, inspection cost is usually low per request but scales with rule set size. |
| Operational cost | Highest. a dedicated tier plus its own redundancy, scaling, and certificate management. | Moderate. usually a managed component with routing rules as configuration. | Moderate. usually a managed component, offloading is often a checkbox feature of an existing gateway. | Low to moderate, frequently a managed, largely self operating service. |
| Single point of failure risk | Present, explicitly documented, mitigated by redundancy and autoscaling. | Present but usually mitigated by the same managed platform that provides routing. | Present but the failure mode is usually degraded performance, not an outright block, since offloading failures can often fail open to direct TLS termination in some configurations. | Present; a WAF that fails closed under overload can itself cause an outage. |
| Best combined with | Gateway Offloading (to reduce the gatekeeper's own TLS and compression cost) and Rate Limiting (to bound abuse before it reaches validation logic). | Gatekeeper, layered in front, to add validation the routing layer itself does not provide. | Gatekeeper, layered behind it, so offloading handles transport concerns and the gatekeeper handles content and identity concerns. | An inner, application aware layer (an API gateway or a custom gatekeeper), because a WAF alone does not narrow backend reachability or perform business schema validation. |

## 13. Related and incompatible patterns

**Gateway Offloading.** Frequently composed with Gatekeeper rather than substituted for it. Gateway
Offloading is about moving expensive, repetitive cross cutting work, TLS termination, compression,
certificate management, off every backend instance and into a shared gateway tier. A gatekeeper can
sit behind an offloading gateway, receiving already decrypted traffic, or the offloading concerns
can be folded into the gatekeeper itself; either composition is common, and Azure explicitly lists
combining the gateway family patterns as a recommended practice (Microsoft, Azure Architecture
Center, "Cloud Design Patterns" index, verified 2026-08-03, https://learn.microsoft.com/en-us/azure/architecture/patterns/).

**Gateway Routing and Gateway Aggregation.** Both are about shaping how requests are directed to,
or combined across, multiple backend services; neither is primarily a security boundary. A system
frequently layers all three gateway patterns behind one public endpoint, as Azure's own combination
guidance suggests, with Gatekeeper adding the validation and isolation layer that routing and
aggregation alone do not provide.

**Valet Key.** A different way to reduce the attack surface of a privileged backend. instead of
brokering every request through a validating intermediary, Valet Key issues the client a scoped,
time limited token that grants direct, restricted access to a specific resource, bypassing the
application tier entirely for that operation. The two patterns solve overlapping problems with
opposite strategies, Gatekeeper keeps every request flowing through a broker, Valet Key removes the
broker from the data path for the specific operation the key covers, and they compose well when a
system uses Gatekeeper for its general API surface but issues valet keys for high volume, low risk
operations such as direct blob upload.

**Federated Identity.** Complementary rather than overlapping. Federated Identity delegates
authentication decisions to an external identity provider, while Gatekeeper is the component that
typically calls that identity provider and enforces the resulting decision before forwarding a
request. A gatekeeper without federated identity still has to implement its own authentication
logic; pairing the two moves that logic to a specialized, externally maintained provider.

**Quarantine.** Related in spirit. Quarantine checks that external assets meet an agreed quality bar
before the workload consumes them, most commonly applied to files, artifacts, or third party
packages rather than live API requests. A gatekeeper is effectively Quarantine applied continuously
to inbound network requests rather than to artifacts at rest.

**Sidecar.** An implementation variant of Gatekeeper rather than a competing pattern, as described
in dimension 8; a sidecar proxy co located with a backend instance can perform the gatekeeper role
at the granularity of a single instance rather than a shared tier.

**Rate Limiting and Throttling.** Both are specific behaviors a gatekeeper commonly implements
rather than patterns it competes with; a gatekeeper without any rate limiting logic is an
incomplete implementation of the pattern for any internet facing system, since unbounded request
volume is one of the threats the pattern exists to blunt.

**Incompatible with.** No pattern surveyed is architecturally incompatible with Gatekeeper in the
sense of being unable to coexist. The closest thing to a genuine incompatibility is a system that
has already adopted a zero trust, mutual TLS everywhere model where every service, not just the
edge, independently authenticates and authorizes every caller regardless of network position; in
that model a dedicated Gatekeeper tier's isolation benefit is largely subsumed by the mesh itself,
though a gatekeeper can still add value as the place where schema validation and business specific
sanitization live, since a service mesh typically does not perform application level payload
validation.

## 14. Refactoring path in and out

**Introducing the pattern into an existing monolithic handler.** Start by identifying which
endpoints currently both accept untrusted input and directly hold or use privileged credentials in
the same process. For each one, extract the validation and authentication logic that currently
lives inline into a separate function or module first, without moving it to a separate process yet;
this is a safe, purely internal refactor that clarifies exactly what the eventual gatekeeper's
responsibilities will be. Next, stand up the new gatekeeper as a thin process that calls the
existing monolith over the network instead of in process, initially over the same network segment,
so the only change is the process boundary, not the trust boundary; verify correctness and
performance at this stage before tightening anything. Only once the gatekeeper is proven correct in
production should the trusted host's endpoint actually be moved behind a private endpoint or
network policy that removes its public reachability, because this final step is the one that
removes the fallback path if something in the new gatekeeper turns out to be wrong. Roll this out
incrementally, one endpoint or one traffic percentage at a time, so a defect in the new validation
path is caught against a small blast radius rather than an all at once cutover.

**Removing the pattern when it stops earning its place.** A gatekeeper stops earning its place when
the conditions in dimension 4's non-applicability list start to hold. the backend service's own
platform now offers equivalent controls natively, or the security and compliance requirement that
originally justified the pattern has changed, or the latency cost has become unacceptable relative
to the security benefit as measured against actual incident data rather than a hypothetical risk.
Removing it safely means first proving, with data, that the backend platform's native controls
cover what the gatekeeper currently does, then running both in parallel with the gatekeeper in log
only or shadow mode to compare outcomes, and only then retiring the gatekeeper tier and exposing the
backend's own endpoint, ideally still behind whatever native platform controls replaced the
gatekeeper's job. Removing the tier without first replacing its function with something equivalent
reintroduces the exact problem in dimension 2 the pattern was adopted to solve.

## 15. Testing and verification

**What becomes easy to test because of this pattern.** Validation and sanitization logic is
isolated in one component with a narrow, well defined contract, request in, allow or reject
decision out, so it can be unit tested exhaustively against a large set of malformed, oversized, and
malicious payloads without needing to spin up the trusted host, storage, or any downstream service
at all. The trusted host's own tests correspondingly get simpler, because it can assume its inputs
have already passed a known validation contract, letting its test suite focus on business logic
correctness rather than re-deriving input sanitization edge cases.

**What becomes harder to test because of this pattern.** End to end tests now need to exercise two
network hops and two separately deployed components instead of one, so a test environment has to
stand up both tiers with the correct internal network configuration between them, or the test does
not actually exercise the isolation property the pattern exists to provide. It is easy to
accidentally test only the trusted host directly, bypassing the gatekeeper entirely in a test
environment for convenience, which silently stops verifying that the gatekeeper's validation rules
actually match what the trusted host expects; this drift is exactly how failure mode 4 in dimension
11 tends to originate in practice.

**Techniques and test doubles that apply.** Contract tests between the gatekeeper and the trusted
host, verifying that every request the gatekeeper forwards is structurally acceptable to the
trusted host and that every rejection the gatekeeper issues corresponds to input the trusted host
would also have rejected, catch drift between the two components' understanding of what is valid.
A fake, in memory trusted host that records every request it receives, used in the gatekeeper's own
test suite, lets the gatekeeper's tests assert precisely what was and was not forwarded without
needing a live backend. Fuzzing the gatekeeper's public endpoint directly, with malformed,
oversized, and adversarially crafted payloads, is the most direct verification that the isolation
property holds, since the entire value of the pattern rests on the gatekeeper correctly rejecting
what should never reach the trusted host. Network level tests, attempting to reach the trusted
host's internal endpoint from outside the gatekeeper's network segment and asserting the attempt
fails, are the only tests that actually verify the isolation the pattern promises rather than merely
verifying application level behavior.

## 16. Observability signals

**What to log at the gatekeeper.** Every request should produce a structured log line recording the
caller's identity or IP, the requested operation, the validation outcome (accepted, rejected, and
which specific rule caused a rejection), and the latency of the validation step itself, separate
from the latency of the downstream call. Azure's worked reference architecture specifically calls
out that the web application firewall layer's "diagnostic logs record matched and blocked rules per
request," while the API management layer "emits gateway logs that capture request duration,
response codes, and policy outcomes," and recommends collecting both centrally and "generating or
forwarding a correlation ID at the edge and propagating it through" every subsequent layer so a
single transaction remains traceable end to end (Microsoft, Azure Architecture Center, "Gatekeeper
Pattern," verified 2026-08-03).

**What a healthy gatekeeper looks like on a dashboard.** A steady, expected rejection rate that
correlates with known bot and scanner traffic rather than spiking unpredictably; validation latency
that stays flat regardless of request volume, since a validation step whose latency grows with
concurrent load usually indicates a lock, an unpooled connection, or a synchronous external call on
the hot path, matching failure mode 5 in dimension 11; and a request forwarding rate to the trusted
host that tracks the accepted request rate one to one, since any divergence between requests
accepted by the gatekeeper and requests received by the trusted host indicates either dropped
requests or, more dangerously, requests reaching the trusted host through a path other than the
gatekeeper.

**What a failing gatekeeper looks like.** A sudden change in the rejection rate, in either
direction, without a corresponding change in traffic composition is the first signal something is
wrong, either the validation rules changed unexpectedly, or the traffic mix genuinely changed and
the rules need review. A nonzero count of requests reaching the trusted host's internal endpoint
whose originating identity does not match the gatekeeper's own service identity, which requires the
trusted host itself to log and alert on caller identity rather than trusting network position alone,
is the strongest possible signal that failure mode 1 or 7 in dimension 11 is happening in
production, and this signal only exists if the trusted host is instrumented to check for it in the
first place.

## 17. Security and privacy implications

The entire purpose of this pattern is a security implication, so the honest framing here is where
the pattern's security guarantee is strong, where it is only as strong as its weakest supporting
control, and what privacy specific implications follow from centralizing request inspection in one
place.

**Where the guarantee is strong.** Credential exposure risk from a compromise of the internet
facing tier is genuinely reduced, because the gatekeeper never holds the credentials an attacker
would want. This is a structural guarantee, not merely a best practice; as long as the network
isolation between gatekeeper and trusted host is actually enforced, no code level bug in the
gatekeeper can leak a credential that the gatekeeper never had.

**Where the guarantee depends on supporting controls.** The isolation guarantee is only as strong
as the network control enforcing it. A gatekeeper pattern implemented in the application's code and
documentation, but not backed by an actual network policy, security group, or private endpoint
denying direct access to the trusted host, provides zero additional protection over a monolithic
handler, because nothing stops an attacker who discovers the trusted host's address from connecting
to it directly. This is failure mode 1 in dimension 11 and it is worth restating here because it is
the single most common way teams believe they have this pattern's protection without actually
having it.

**Data handling implication of centralized inspection.** Because every request passes through the
gatekeeper, the gatekeeper is also the natural place where sensitive data first enters logs, traces,
and metrics, which means the gatekeeper's own logging configuration becomes a privacy control point.
A gatekeeper that logs full request bodies for debugging convenience can inadvertently become a
store of exactly the sensitive data, credentials, personal information, payment details, the
pattern was adopted to protect, so logging at the gatekeeper should redact or omit request body
content by default and log only what is needed to explain a validation decision, matching the
principle that the gatekeeper's own footprint should stay as narrow as the privilege it holds.

**Denial of service surface.** Centralizing all traffic through one tier concentrates the denial of
service target as well as the security benefit; an attacker who cannot reach the trusted host
directly can still attempt to overwhelm the gatekeeper itself, which is why rate limiting and
autoscaling at the gatekeeper tier are not optional hardening but a load bearing part of the
pattern's own availability story, as discussed in dimensions 3 and 10.

## 18. References

1. Microsoft, "Gatekeeper Pattern," Azure Architecture Center, verified 2026-08-03.
   https://learn.microsoft.com/en-us/azure/architecture/patterns/gatekeeper
2. Microsoft, "Design Patterns," patterns & practices Cloud Design Patterns guide (archived,
   originally published 2014), verified 2026-08-03.
   https://learn.microsoft.com/en-us/previous-versions/msp-n-p/dn600223(v=pandp.10)
3. Microsoft, "Cloud Design Patterns" catalog index, Azure Architecture Center, verified
   2026-08-03. https://learn.microsoft.com/en-us/azure/architecture/patterns/
4. Wikipedia, "Bastion host," citing Marcus J. Ranum, "Thinking About Firewalls," 1992, verified
   2026-08-03. https://en.wikipedia.org/wiki/Bastion_host
5. Open Policy Agent, "Gatekeeper documentation," CNCF, verified 2026-08-03.
   https://open-policy-agent.github.io/gatekeeper/website/docs/
6. Amazon Web Services, "Use API Gateway Lambda authorizers," AWS API Gateway Developer Guide,
   verified 2026-08-03.
   https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html

## Code examples

All three samples implement the same minimal shape. a gatekeeper process that validates an inbound
request (schema, size, a simple bearer token check, and per-caller rate limiting) and, only on
success, forwards a sanitized request to a trusted host over a separate connection. The trusted
host in each sample is a stand in for the privileged backend; it never receives anything that did
not pass through the gatekeeper's validation. All three were compiled or run locally.

### TypeScript

```typescript
// gatekeeper.ts
// A minimal Gatekeeper: validates, rate-limits, then forwards to a trusted host.
// Run with: npx tsc gatekeeper.ts --target es2020 --module commonjs --outDir dist

interface IncomingRequest {
  callerId: string;
  bearerToken: string;
  payload: Record<string, unknown>;
}

interface ValidationResult {
  ok: boolean;
  reason?: string;
}

const VALID_TOKEN = "trusted-caller-token";
const MAX_PAYLOAD_KEYS = 10;
const RATE_LIMIT_WINDOW_MS = 60_000;
const RATE_LIMIT_MAX_REQUESTS = 5;

const requestLog = new Map<string, number[]>();

function withinRateLimit(callerId: string): boolean {
  const now = Date.now();
  const timestamps = (requestLog.get(callerId) ?? []).filter(
    (t) => now - t < RATE_LIMIT_WINDOW_MS
  );
  if (timestamps.length >= RATE_LIMIT_MAX_REQUESTS) {
    requestLog.set(callerId, timestamps);
    return false;
  }
  timestamps.push(now);
  requestLog.set(callerId, timestamps);
  return true;
}

function validate(req: IncomingRequest): ValidationResult {
  if (req.bearerToken !== VALID_TOKEN) {
    return { ok: false, reason: "authentication failed" };
  }
  if (!withinRateLimit(req.callerId)) {
    return { ok: false, reason: "rate limit exceeded" };
  }
  const keyCount = Object.keys(req.payload).length;
  if (keyCount === 0 || keyCount > MAX_PAYLOAD_KEYS) {
    return { ok: false, reason: "payload shape invalid" };
  }
  for (const value of Object.values(req.payload)) {
    if (typeof value === "string" && /<script/i.test(value)) {
      return { ok: false, reason: "payload contains unsafe content" };
    }
  }
  return { ok: true };
}

// The trusted host: this function is the only thing on the "privileged" side.
// In a real deployment it lives in a separate process reachable only
// from the gatekeeper's network segment, never from the public internet.
function trustedHostHandle(sanitizedPayload: Record<string, unknown>): string {
  return `trusted host processed keys: ${Object.keys(sanitizedPayload).join(", ")}`;
}

function gatekeeperHandle(req: IncomingRequest): { status: number; body: string } {
  const result = validate(req);
  if (!result.ok) {
    return { status: 400, body: `rejected: ${result.reason}` };
  }
  // Only a validated, sanitized payload crosses the internal boundary.
  const response = trustedHostHandle(req.payload);
  return { status: 200, body: response };
}

function run(): void {
  const good: IncomingRequest = {
    callerId: "client-1",
    bearerToken: VALID_TOKEN,
    payload: { name: "order-42", amount: 19.99 },
  };
  const bad: IncomingRequest = {
    callerId: "client-2",
    bearerToken: "wrong-token",
    payload: { name: "order-43" },
  };
  console.log(gatekeeperHandle(good));
  console.log(gatekeeperHandle(bad));
}

run();
```

Compiled and run locally.

```
$ npx tsc gatekeeper.ts --target es2020 --module commonjs --outDir dist
$ node dist/gatekeeper.js
{ status: 200, body: 'trusted host processed keys: name, amount' }
{ status: 400, body: 'rejected: authentication failed' }
```

### Python

```python
# gatekeeper.py
# A minimal Gatekeeper: validates, rate-limits, then forwards to a trusted host.
# Run with: python3 gatekeeper.py

from __future__ import annotations
import re
import time
from dataclasses import dataclass, field
from typing import Any

VALID_TOKEN = "trusted-caller-token"
MAX_PAYLOAD_KEYS = 10
RATE_LIMIT_WINDOW_SECONDS = 60.0
RATE_LIMIT_MAX_REQUESTS = 5

_request_log: dict[str, list[float]] = {}


@dataclass
class IncomingRequest:
    caller_id: str
    bearer_token: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    ok: bool
    reason: str | None = None


def within_rate_limit(caller_id: str) -> bool:
    now = time.monotonic()
    timestamps = [
        t for t in _request_log.get(caller_id, [])
        if now - t < RATE_LIMIT_WINDOW_SECONDS
    ]
    if len(timestamps) >= RATE_LIMIT_MAX_REQUESTS:
        _request_log[caller_id] = timestamps
        return False
    timestamps.append(now)
    _request_log[caller_id] = timestamps
    return True


def validate(req: IncomingRequest) -> ValidationResult:
    if req.bearer_token != VALID_TOKEN:
        return ValidationResult(False, "authentication failed")
    if not within_rate_limit(req.caller_id):
        return ValidationResult(False, "rate limit exceeded")
    key_count = len(req.payload)
    if key_count == 0 or key_count > MAX_PAYLOAD_KEYS:
        return ValidationResult(False, "payload shape invalid")
    for value in req.payload.values():
        if isinstance(value, str) and re.search(r"<script", value, re.IGNORECASE):
            return ValidationResult(False, "payload contains unsafe content")
    return ValidationResult(True)


# The trusted host: the only place holding "privileged" logic in this sample.
# In production this runs as a separate process, reachable only from the
# gatekeeper's network segment, never from the public internet.
def trusted_host_handle(sanitized_payload: dict[str, Any]) -> str:
    return f"trusted host processed keys: {', '.join(sanitized_payload.keys())}"


def gatekeeper_handle(req: IncomingRequest) -> tuple[int, str]:
    result = validate(req)
    if not result.ok:
        return 400, f"rejected: {result.reason}"
    response = trusted_host_handle(req.payload)
    return 200, response


def main() -> None:
    good = IncomingRequest(
        caller_id="client-1",
        bearer_token=VALID_TOKEN,
        payload={"name": "order-42", "amount": 19.99},
    )
    bad = IncomingRequest(
        caller_id="client-2",
        bearer_token="wrong-token",
        payload={"name": "order-43"},
    )
    print(gatekeeper_handle(good))
    print(gatekeeper_handle(bad))


if __name__ == "__main__":
    main()
```

Run locally.

```
$ python3 gatekeeper.py
(200, 'trusted host processed keys: name, amount')
(400, 'rejected: authentication failed')
```

### Go

```go
// gatekeeper.go
// A minimal Gatekeeper: validates, rate-limits, then forwards to a trusted host.
// Run with: go run gatekeeper.go

package main

import (
	"fmt"
	"regexp"
	"sync"
	"time"
)

const (
	validToken           = "trusted-caller-token"
	maxPayloadKeys       = 10
	rateLimitWindow      = 60 * time.Second
	rateLimitMaxRequests = 5
)

var scriptPattern = regexp.MustCompile(`(?i)<script`)

type IncomingRequest struct {
	CallerID    string
	BearerToken string
	Payload     map[string]any
}

type ValidationResult struct {
	OK     bool
	Reason string
}

type rateLimiter struct {
	mu  sync.Mutex
	log map[string][]time.Time
}

func newRateLimiter() *rateLimiter {
	return &rateLimiter{log: make(map[string][]time.Time)}
}

func (r *rateLimiter) allow(callerID string) bool {
	r.mu.Lock()
	defer r.mu.Unlock()
	now := time.Now()
	var kept []time.Time
	for _, t := range r.log[callerID] {
		if now.Sub(t) < rateLimitWindow {
			kept = append(kept, t)
		}
	}
	if len(kept) >= rateLimitMaxRequests {
		r.log[callerID] = kept
		return false
	}
	kept = append(kept, now)
	r.log[callerID] = kept
	return true
}

var limiter = newRateLimiter()

func validate(req IncomingRequest) ValidationResult {
	if req.BearerToken != validToken {
		return ValidationResult{OK: false, Reason: "authentication failed"}
	}
	if !limiter.allow(req.CallerID) {
		return ValidationResult{OK: false, Reason: "rate limit exceeded"}
	}
	keyCount := len(req.Payload)
	if keyCount == 0 || keyCount > maxPayloadKeys {
		return ValidationResult{OK: false, Reason: "payload shape invalid"}
	}
	for _, v := range req.Payload {
		if s, ok := v.(string); ok && scriptPattern.MatchString(s) {
			return ValidationResult{OK: false, Reason: "payload contains unsafe content"}
		}
	}
	return ValidationResult{OK: true}
}

// trustedHostHandle stands in for the privileged backend. In production this
// runs as a separate process, reachable only from the gatekeeper's network
// segment, never from the public internet.
func trustedHostHandle(sanitized map[string]any) string {
	keys := make([]string, 0, len(sanitized))
	for k := range sanitized {
		keys = append(keys, k)
	}
	return fmt.Sprintf("trusted host processed %d keys", len(keys))
}

func gatekeeperHandle(req IncomingRequest) (int, string) {
	result := validate(req)
	if !result.OK {
		return 400, "rejected: " + result.Reason
	}
	return 200, trustedHostHandle(req.Payload)
}

func main() {
	good := IncomingRequest{
		CallerID:    "client-1",
		BearerToken: validToken,
		Payload:     map[string]any{"name": "order-42", "amount": 19.99},
	}
	bad := IncomingRequest{
		CallerID:    "client-2",
		BearerToken: "wrong-token",
		Payload:     map[string]any{"name": "order-43"},
	}
	status, body := gatekeeperHandle(good)
	fmt.Println(status, body)
	status, body = gatekeeperHandle(bad)
	fmt.Println(status, body)
}
```

Run locally.

```
$ go run gatekeeper.go
200 trusted host processed 2 keys
400 rejected: authentication failed
```
