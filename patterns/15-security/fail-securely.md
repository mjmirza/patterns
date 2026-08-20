---
name: Fail Securely
slug: fail-securely
family: 15-security
category: Security
aliases: [Fail Closed, Deny by Default, Fail-Safe Defaults, Safe Failure]
first_described: "Saltzer and Schroeder 1975"
maturity: established
related: [least-privilege, secure-by-default, defense-in-depth, zero-trust, complete-mediation]
incompatible_with: [fail-open, optimistic-authorization, default-allow]
verified: 2026-08-02
---

# Fail Securely

## 1. Name, aliases, and lineage

The canonical name in this catalog is Fail Securely. The phrase names the
engineering practice of choosing a failure state that preserves the security
property the control exists to protect. In access control that state is usually
deny. In cryptography it is usually no plaintext output. In network policy it
is usually no packet flow. In workflow automation it is usually no side effect
until the missing check returns a clear allow.

The oldest named lineage is Saltzer and Schroeder's design principle
**Fail-safe defaults**. Their 1975 paper, "The Protection of Information in
Computer Systems," lists fail-safe defaults among eight information protection
principles and explains the default as lack of access, with permission granted
only when the protection scheme identifies the conditions for access
([MIT copy of Saltzer and Schroeder, section I.A.3](https://web.mit.edu/Saltzer/www/publications/protection/Basic.html),
verified 2026-08-02). This entry uses Fail Securely rather than Fail-Safe
Defaults because current software teams apply the idea beyond access control.
The same decision shape appears in policy engines, service meshes, payment
flows, cryptographic modules, database row filters, and automation gates.

Common aliases carry different emphases.

- **Fail closed.** The system closes the gate when the control cannot make a
  trustworthy allow decision. This is common in network, proxy, and
  authorization discussions.
- **Deny by default.** The access control form. OWASP's Authorization Cheat
  Sheet says an application should deny access by default when no rule matches
  ([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html),
  verified 2026-08-02).
- **Safe failure.** A broader system-safety phrasing. It can mean protecting
  confidentiality, integrity, availability, or money, depending on the control.
- **Secure failure handling.** A coding phrasing used when exception paths,
  timeout paths, and partial dependency outages must preserve the security
  decision.

This pattern is not the same as making a system highly available. A service can
fail securely by refusing a request, and that refusal can still be an outage for
the user. That tension is the central trade in the pattern.

## 2. Problem and context

A program must make a decision that protects a resource, but the information
needed for that decision can be absent, stale, malformed, contradictory, late,
or produced by a dependency that is currently down. The request is still in
front of the system. The code can permit it, deny it, retry it, queue it, or
return an error. If the default path permits it, a missing policy, failed
lookup, parsing bug, network timeout, or unexpected enum value turns into a
security bypass.

The pattern appears in ordinary code. An API handler asks a policy service
whether a user may update an invoice. The policy service times out. The handler
has a catch block. If that catch block returns true because the team wanted to
avoid blocking legitimate users, the authorization boundary is now weaker than
the policy service. A data service enables row-level security but has not yet
created a policy for a new table. If the database returns every row until the
policy arrives, rollout order becomes a confidentiality risk. A proxy cannot
reach its external authorization service. If it forwards traffic anyway, the
proxy has become an allow-all side door during the exact moments when operators
have the least clarity.

Fail Securely fits when the failure path crosses a trust boundary or guards a
side effect that cannot be silently undone. Reads of private data, writes to
authoritative state, financial transfers, credential issuance, administrative
actions, network admission, cryptographic verification, and policy evaluation
belong in that group. The pattern is less useful for local formatting errors,
cache misses, or optional personalization where the failure cannot grant access,
change state, leak data, or weaken a later control.

The context matters. "Deny everything on error" is not a universal product
rule. A hospital downtime mode, an industrial safety controller, or an emergency
communications system can make availability the safer state. In those cases the
pattern still applies, but the safe state must be chosen through explicit threat
and hazard analysis, not by copying an access-control slogan.

There is also a release-engineering context. Many failures are born during
change, not during steady state. A feature flag is created before the policy
bundle. A database table is deployed before its row policy. A mobile client
sends a new action string before the server's authorization matrix has that
action. A gateway route is added with a path match but no external auth rule.
Fail Securely makes those rollout-order mistakes noisy. The first user sees a
denial, the dashboard shows missing policy, and the team fixes the grant. The
opposite default makes the first user successful and turns the mistake into a
latent exposure that may be found only by audit or abuse.

## 3. Forces

This dimension is engineering judgement unless a sentence cites a named source.

**Confidentiality versus availability.** The pattern favours confidentiality and
integrity over immediate service availability. A denied request can protect data
while still breaking a customer workflow. That trade is correct for many
authorization gates and wrong for some emergency systems.

**Integrity versus recovery speed.** Refusing a write keeps bad state out. It
also means operators need a retry, queue, or manual repair path for legitimate
writes that were blocked by a transient fault.

**Latency versus certainty.** Waiting for policy, identity, key status, or
fresh configuration increases the chance of a correct decision, but it can add
tail latency. Timeouts must be short enough to bound user impact and strict
enough that a slow dependency does not become a permit.

**Coupling versus central control.** A single policy decision point gives teams
one place to reason about fail-closed behaviour. It also couples callers to that
component's health. Distributed cached decisions reduce coupling, but stale
cached allows need a clear expiry and revocation story.

**Operability versus secrecy.** Operators need to see why a request was denied.
Attackers should not receive the missing policy name, group membership, table
name, or internal dependency error. The pattern favours detailed internal
events and bland external responses.

**Cost versus blast radius.** Building deny paths, negative tests, circuit
breakers, break-glass flows, and dashboards costs time. The return is reduced
blast radius when a dependency fails or a new route ships without policy.

**Team topology versus local autonomy.** Platform teams often own the policy
engine or admission layer. Product teams own features that need access. The
pattern favours a shared default and local explicit grants. That reduces
unreviewed access but can make feature teams wait for policy changes if the
workflow is ticket-driven.

**Cognitive load versus predictable failure.** Developers must learn that
unknown means deny, missing means deny, parse error means deny, and timeout
means deny. That discipline raises cognitive load, but the runtime state becomes
predictable under partial failure.

**User experience versus evidence.** A precise denial reason helps a legitimate
user fix a request. The same reason can help an attacker learn which part of the
policy nearly matched. The pattern favours generic user-facing errors paired
with evidence-rich internal logs. The product cost is support friction. The
security gain is less policy discovery by trial and error.

**Local fallback versus shared semantics.** A local fallback is tempting because
it lets a service keep working when the central decision point is down. The
danger is semantic drift. One service treats missing group data as deny, another
treats it as guest, and a third treats it as previous allow. The pattern favours
one shared failure contract even when implementation is local.

## 4. Applicability and non-applicability

Reach for Fail Securely when the following hold.

- A request crosses an authorization boundary and the allow decision depends on
  policy, identity, group membership, object ownership, device posture, tenant,
  data label, or risk score.
- A write has lasting consequences, such as publishing a payment, changing a
  role, issuing a token, rotating a key, deleting a record, or sending an email
  outside the organization.
- A system loads policy or security configuration at startup and could run with
  an empty, partial, or stale configuration after a deploy or dependency fault.
- A proxy, gateway, service mesh, queue worker, or job runner makes security
  decisions on behalf of downstream code.
- A cryptographic check, signature validation, certificate validation, token
  validation, or random-number source can fail.
- A new feature, route, resource type, event topic, or admin action should have
  no access until an owner adds explicit policy.
- The cost of a false allow is higher than the cost of a false deny.

Explicit non-applicability follows.

- Do not use fail-closed behaviour where human safety requires continued
  operation. A medical, aviation, industrial, or emergency system needs a hazard
  analysis that identifies the safe state. Sometimes that state is controlled
  degraded operation rather than denial.
- Do not use it as a substitute for capacity planning. If the policy service is
  down every week, refusing traffic is a symptom, not the cure.
- Do not hide product requirements behind "security says no." Public pages,
  anonymous downloads, trial flows, and open data can be intentionally
  accessible. They still need explicit allow rules so the openness is visible.
- Do not fail closed without a recovery path for business-critical operations.
  Use retry queues, operator override, limited break-glass, or delayed
  execution where the organization has accepted that path.
- Do not return detailed security internals to the caller. Failing securely is
  not a license to reveal which role, policy, key, table, or tenant check failed.
- Do not deny after a side effect has already occurred and call that secure.
  The decision must happen before the protected read, write, send, mint, or
  release.
- Do not treat a cached allow as safe forever. Cached policy can be a variant,
  but it needs expiry, invalidation, and an answer for emergency revocation.
- Do not apply it to harmless local fallbacks where the failure cannot weaken a
  control. Returning a default avatar or empty recommendation list is ordinary
  degradation, not this pattern.

## 5. Structure

The participants are roles, not classes.

- **Protected action.** The read, write, network flow, cryptographic release,
  workflow transition, or side effect that must not happen without a trustworthy
  allow decision.
- **Decision input.** The identity, request attributes, resource attributes,
  policy version, environment attributes, and risk data needed for the decision.
- **Policy decision point.** The code, service, database rule, or policy engine
  that evaluates the decision input and returns allow, deny, or an error state.
- **Policy enforcement point.** The code at the boundary that blocks or permits
  the protected action. It owns the default. If the decision point is silent,
  late, or confused, the enforcement point denies.
- **Safe default.** The local rule that maps missing, unknown, malformed,
  expired, or failed decision states to deny or to a named degraded mode.
- **Failure classifier.** The small part of the enforcement point that
  separates decision outcomes from transport errors, parse errors, timeouts,
  stale configuration, duplicate policies, and impossible states.
- **Audit sink.** The event stream, log, trace, or security analytics pipeline
  that records the denied decision without leaking sensitive values.
- **Recovery path.** The retry, queue, break-glass, operator procedure, or
  configuration repair path used when a legitimate request was denied by the
  safe default.

The important relationship is that the enforcement point sits before the
protected action and owns the local fail-closed rule. A central policy service
can be correct and the system can still fail open if callers translate errors to
allow. A database can support row security and still leak if the application
uses a bypass role. The pattern lives at the enforcement point, not in policy
documents alone.

The failure classifier should be boring by design. It should not contain
business exceptions such as "VIP users pass during outage" unless those
exceptions are policy decisions with their own tests and audit. Its job is to
translate machine states into the decision contract. Missing identity is deny.
Missing resource attributes is deny. Policy parse failure is deny. Expired
policy bundle is deny. Unknown action is deny. Only the policy decision point
can produce allow, and only when the input is complete enough for the policy to
mean what it says.

## 6. ASCII structure diagram

```
----------------+       +----------------------+       +----------------+
| Request        |------>| Policy Enforcement   |------>| Protected      |
| principal, obj |       | Point                | allow | Action         |
+----------------+       |                      |       | read or write  |
                         |  safe default: deny  |       +----------------+
                         +----------+-----------+
                                    |
                                    | decision input
                                    v
                         +----------+-----------+
                         | Policy Decision      |
                         | Point                |
                         | allow, deny, error   |
                         +----------+-----------+
                                    |
              +---------------------+---------------------+
              |                                           |
              v                                           v
   +----------------------+                  +----------------------+
   | Audit Sink           |                  | Recovery Path        |
   | deny reason, version |                  | retry, repair,       |
   | no secret values     |                  | break-glass          |
   +----------------------+                  +----------------------+

Any missing, stale, malformed, timeout, or unknown result maps to deny before
the protected action runs.
```

## 7. Dynamics

At runtime the pattern is a small state machine. The enforcement point asks the
decision point for a permit. Only one terminal state can execute the protected
action. All other terminal states deny, queue, or enter a named degraded mode.

```
Client        Enforcement Point       Decision Point        Protected Action
  |                  |                       |                       |
  |-- request ------>|                       |                       |
  |                  |-- evaluate ---------->|                       |
  |                  |                       |                       |
  |                  |<-- allow -------------|                       |
  |                  |-- execute protected action ------------------>|
  |<-- success ------|                       |                       |
  |                  |                       |                       |

Client        Enforcement Point       Decision Point        Audit Sink
  |                  |                       |                  |
  |-- request ------>|                       |                  |
  |                  |-- evaluate ---------->|                  |
  |                  |<-- deny, timeout,     |                  |
  |                  |    parse error,       |                  |
  |                  |    stale policy,      |                  |
  |                  |    unknown state -----|                  |
  |                  |-- record denial ------------------------>|
  |<-- generic deny -|                       |                  |
  |                  |                       |                  |

State rule:
  allow                       -> run action
  explicit deny               -> deny
  no matching rule            -> deny
  policy load failure         -> deny
  identity missing            -> deny
  dependency timeout          -> deny
  malformed decision response -> deny
  unknown enum value          -> deny
```

The pattern should be applied before irreversible work. If a handler charges a
card and then checks whether the actor may charge it, the later denial protects
the log more than the user. If a gateway forwards a request and then awaits an
authorization result, the protected action has already crossed the boundary.

## 8. Implementation variants

**Inline guard clause.** The caller checks policy and returns before the
protected action. This is easy to read in a small service, but coverage depends
on every route remembering the guard. Use it with route tests that prove the
guard is present.

**Central middleware or filter.** A web framework, RPC interceptor, queue
consumer wrapper, or gateway performs the decision before handler code runs.
OWASP recommends validating permissions on every request and points to filters
and middleware as technologies used for consistent checks
([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html),
verified 2026-08-02). This variant lowers missed-check risk, but the policy
model must be expressive enough for object-level decisions.

**Policy engine with default false.** A policy language or engine returns false
unless a rule proves allow. OPA Rego supports a `default allow := false` rule
for this shape ([Open Policy Agent policy language](https://www.openpolicyagent.org/docs/policy-language),
verified 2026-08-02). This variant is strong for many services sharing policy,
but callers must still map evaluation errors to deny.

**Database-enforced deny.** The database applies row or table policy even if the
application misses a check. PostgreSQL row security uses a default-deny policy
when row security is enabled and no policy exists for the table
([PostgreSQL row security documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html),
verified 2026-08-02). This variant moves the guard close to the data, but owner
roles and bypass roles need careful control.

**Network default deny.** A namespace, subnet, security group, firewall, or
service mesh starts from no traffic and adds named flows. Kubernetes documents
NetworkPolicy examples for default deny ingress, egress, and both directions
([Kubernetes NetworkPolicy documentation](https://kubernetes.io/docs/concepts/services-networking/network-policies/),
verified 2026-08-02). This variant is clear for service boundaries, but it can
break DNS, health checks, metrics, or control-plane traffic unless those flows
are explicit.

**Startup fail closed.** A service refuses to become ready unless it has loaded
valid security configuration, current keys, policy bundles, and required trust
anchors. This variant catches broken deploys early. The cost is a hard deploy
failure instead of a partially working service.

**Degraded mode.** The system refuses sensitive operations but permits harmless
ones. For example, read public content while blocking private reads and writes,
or accept a request into a pending queue while refusing execution. This variant
can preserve user workflow without granting access, but the harmless set must
be named and tested.

**Break-glass with audit.** An emergency path permits a blocked operation after
stronger authentication, bounded scope, time limits, ticket link, and noisy
audit. This is not a fail-open catch block. It is a separate allow rule for an
exceptional condition.

**Two-phase execution.** The system accepts a request, records it as pending,
and later executes it only after policy becomes available and returns allow.
This is useful for workflows where losing the request is expensive but executing
without policy is worse. The request itself must be treated as untrusted data
until approval. It should not reserve scarce inventory, send notifications, or
change authoritative state before the second phase.

**Static deny scaffold.** Some teams create policy files with every action set
to deny before the feature code lands. The later feature patch changes selected
actions to allow. This variant works well in repositories with code review
because the diff shows permission growth. It is weaker when policy is edited
manually in an admin console with no review trail.

**Generated authorization matrix.** A build step derives all known routes,
methods, message types, and admin actions, then fails the build if any action is
absent from the policy matrix. Runtime still denies unknown actions, but build
time catches many mistakes earlier. The trade is maintenance cost for the
extractor and the need to keep dynamic routes describable.

## 9. Known production uses

**AWS IAM policy evaluation.** AWS IAM enforcement starts from implicit deny,
requires an explicit allow for access, and gives explicit deny precedence over
allow in its policy evaluation logic
([AWS IAM policy evaluation logic](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic_policy-eval-denyallow.html),
verified 2026-08-02). This is a named production authorization system using
Fail Securely at large scale.

**Kubernetes NetworkPolicy default deny.** Kubernetes NetworkPolicy includes
documented default-deny policies for ingress, egress, and both directions by
selecting all pods and declaring policy types with no allowed peers
([Kubernetes NetworkPolicy documentation](https://kubernetes.io/docs/concepts/services-networking/network-policies/),
verified 2026-08-02). This is a named production platform pattern for network
admission, with the caveat that support depends on the cluster network plugin.

**PostgreSQL Row-Level Security.** PostgreSQL row security denies all normal row
access when row security is enabled on a table and no policy exists
([PostgreSQL row security documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html),
verified 2026-08-02). This is a named database production use where a missing
policy blocks rows rather than exposing them.

**Open Policy Agent Rego policies.** OPA's policy language documents default
values for complete definitions and shows `default allow := false` as an allow
rule fallback ([Open Policy Agent policy language](https://www.openpolicyagent.org/docs/policy-language),
verified 2026-08-02). This is a named policy-engine use. The production system
using OPA must still configure its own enforcement point to treat evaluation
errors as denial.

These examples are intentionally spread across identity, network, database, and
policy layers. That spread matters because Fail Securely is not tied to one
product shape. The common mechanism is the same: a protected action has no
permission until a valid rule grants it, and any gap in the rule path preserves
the closed state.

## 10. Consequences

This dimension is engineering judgement.

Positive consequences.

- Missing policy becomes visible as a denied request rather than an accidental
  grant.
- New routes, resources, tenants, roles, and workflow states start closed until
  a reviewer adds the allow rule.
- Dependency faults are less likely to become security incidents.
- The control has a smaller reasoning surface. Operators can ask, "What allowed
  this?" rather than hunting for every condition that might have denied it.
- Negative tests become easier. A test can delete or corrupt policy input and
  expect denial.
- Security incidents tend to stop at availability impact rather than data
  exposure or unauthorized mutation.
- Audit trails become more useful because deny, timeout, stale policy, and
  malformed input are first-class outcomes.

Negative consequences.

- Legitimate users can be blocked by policy outages, bad deploy order, stale
  identity data, clock skew, broken group sync, or malformed resource metadata.
- Support teams need tools to distinguish true denial from system failure.
- Product teams can feel slowed by explicit grants for every new operation.
- Overuse can create a brittle system where small policy faults become broad
  outages.
- Break-glass paths become attractive and can turn into a second authorization
  system if not constrained.
- Caching decisions becomes harder, because stale allows fight the pattern and
  stale denies create false outages.
- Error responses can become too vague for legitimate clients unless internal
  correlation IDs and operator logs are reliable.

## 11. Failure modes and misuse

This dimension is engineering judgement.

**Timeout becomes allow.** Symptom. Access spikes during policy-service latency
or outage, often with logs showing retries, socket timeouts, or fallback code.
Cause. The catch block maps an unavailable decision point to permit. Fix. Map
timeout to deny, add a short timeout budget, and build a retry or pending queue
for operations that can wait.

**Unknown enum becomes allow.** Symptom. A new action such as `EXPORT` or
`TRANSFER_OWNERSHIP` is accessible before the security review for that action.
Cause. A switch statement has a permissive default branch. Fix. Make unknown
actions deny, require exhaustive matching where the language supports it, and
add a test that a bogus action is denied.

**Policy load failure starts the service.** Symptom. After a deploy, all users
receive broad access or all tenants share a default policy. Logs show missing
bundle, empty config, or parse errors during startup. Cause. The service treats
security configuration as optional. Fix. Refuse readiness until policy is
loaded, validated, versioned, and non-empty.

**Deny happens after the side effect.** Symptom. Audit says a request was denied
but the email was sent, token minted, charge submitted, or file downloaded.
Cause. Authorization is placed after part of the workflow. Fix. Move the
enforcement point before the first irreversible action and add tests around
ordering.

**Cached allow outlives revocation.** Symptom. A user remains able to perform an
admin action after role removal. Cause. A local cache treats previous allow as
valid too long or lacks invalidation. Fix. Use short expiry for sensitive
allows, subscribe to revocation events, or require fresh checks for high-risk
actions.

**Default deny with no operator signal.** Symptom. Customers see generic errors
while operators cannot tell whether the cause is missing policy, identity sync,
clock skew, or a dependency outage. Cause. The fail-closed path returns denial
but emits no structured event. Fix. Log decision outcome, error class, policy
version, resource type, and correlation ID without sensitive values.

**Break-glass becomes routine.** Symptom. Many requests are approved through an
emergency role, and normal policy stops improving. Cause. The override is
easier than fixing policy. Fix. Require ticket links, short duration, separate
approval, reason capture, and review of every break-glass event.

**Deny rule blocks critical platform traffic.** Symptom. After default deny
network policy, pods cannot resolve DNS, report health, emit metrics, or reach
the policy service. Cause. The team denied traffic before enumerating platform
dependencies. Fix. Add explicit infrastructure flows first and test them in a
staging namespace.

**External error leaks internal state.** Symptom. A caller learns policy names,
group IDs, database table names, or key identifiers from deny responses. Cause.
The fail-closed path returns raw internal exceptions. Fix. Return a generic
denial with a correlation ID and keep detail in restricted logs.

**Report-only becomes permanent.** Symptom. Dashboards show that a new operation
would have been denied, but the operation still succeeds in production for
weeks. Cause. The team introduced policy evaluation in observe mode and never
made it the enforcement point. Fix. Put an expiry on report-only mode, require a
ticket for extension, and block the protected action at another layer until
enforcement is active.

**Safe default differs by caller.** Symptom. The web API denies a malformed
request, while the batch worker accepts the same action because its local helper
returns true on parse errors. Cause. Each caller implemented the failure mapping
alone. Fix. Move the mapping to a shared library or gateway contract and add
conformance tests for every caller.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Fail Securely | Fail Open | Retry Until Decision | Queue Pending Review | Degraded Read-Only Mode | Break-Glass Override |
|---|---|---|---|---|---|---|
| Confidentiality | Strong. Unknown denies | Weak. Faults can expose data | Strong if retries do not permit | Strong until review error | Medium. Public read set must be correct | Medium. Depends on override scope |
| Integrity | Strong. Writes stop | Weak. Bad writes can land | Strong if timeout ends in deny | Strong. Writes wait | Strong for writes, mixed for reads | Medium. Human error risk |
| Availability | Lower during faults | Higher during faults | Lower under long outages | Medium. User workflow can continue | Medium to high for harmless reads | High for chosen cases |
| Latency | Low when policy is local, higher when remote | Low | High during dependency faults | High for execution | Low for allowed degraded actions | High process cost |
| Coupling | Coupled to policy health | Looser at runtime, weaker security | Highly coupled | Coupled to review workflow | Coupled to data classification | Coupled to emergency process |
| Operability | Needs good deny telemetry | Incidents may be silent | Needs retry visibility | Needs queue dashboards | Needs clear mode signal | Needs audit and review |
| Cost | Medium | Low at first, high incident cost | Medium to high | High | Medium | High governance cost |
| Team topology | Good with self-service grants | Easy for feature teams, hard for security | Hard across teams | Good for regulated workflows | Good when platform owns modes | Risky if overused |
| Cognitive load | Medium. Unknown means deny | Low until incident | High. Many timing states | Medium. Pending state exists | High. Mode boundaries matter | High. Exceptional path |

Reading of the table. Fail Securely is the right default when a false allow is
more damaging than a false deny. Retry and queue variants are ways to reduce
availability pain without permitting the action. Degraded mode works when the
team can name a truly harmless subset. Break-glass is a controlled exception,
not the baseline.

## 13. Related and incompatible patterns

- **Least Privilege.** Composes directly. Least Privilege limits what an actor
  can do after an allow. Fail Securely defines what happens when no trustworthy
  allow exists.
- **Secure by Default.** Fail Securely is one expression of Secure by Default.
  A new route or account begins with no access until configured.
- **Defense in Depth.** Composes around it. If an application guard fails open,
  a database row policy, network policy, or object-store policy can still deny.
- **Zero Trust.** Composes at system scale. Zero Trust asks for explicit
  verification across requests and contexts. Fail Securely supplies the default
  when that verification is absent or inconclusive.
- **Complete Mediation.** A sibling principle from Saltzer and Schroeder.
  Complete Mediation says every access is checked. Fail Securely says an
  inconclusive check must not become a permit
  ([MIT copy of Saltzer and Schroeder, section I.A.3](https://web.mit.edu/Saltzer/www/publications/protection/Basic.html),
  verified 2026-08-02).
- **Circuit Breaker.** Composes with care. A circuit breaker can stop calls to a
  failing policy service, but the open circuit must return deny or degraded
  mode, not allow.
- **Bulkhead.** Composes operationally. Isolating the policy service or cache
  from noisy callers reduces false denies caused by unrelated load.
- **Graceful Degradation.** Partially overlaps. Degradation is acceptable when
  the degraded path does not grant the protected action. It conflicts when
  degradation means bypassing the control.
- **Fail Open.** Incompatible for the same protected action. It can be accepted
  only after explicit risk analysis and compensating controls.
- **Optimistic Authorization.** Conflicts for high-risk actions. Executing first
  and reconciling later is wrong for data release, credential minting, money
  movement, and privilege changes.

## 14. Refactoring path in and out

Introducing the pattern into code that does not have it.

1. List the protected actions. Include reads, writes, exports, sends, token
   issuance, admin operations, and network ingress or egress.
2. Find every enforcement point for those actions. Use route definitions,
   middleware, RPC interceptors, queue consumers, database policies, and gateway
   rules.
3. Write the decision contract as an enum or sum type. Include `allow`, `deny`,
   `not_found`, `stale_policy`, `malformed_input`, `timeout`, and `error`.
4. Change the enforcement point so only `allow` runs the protected action. Every
   other state returns deny, pending, or a named degraded mode.
5. Move authorization before side effects. If this requires splitting a method,
   use Extract Function and Separate Query from Modifier from the refactoring
   family.
6. Add a startup gate for policy and key material. The service should not report
   ready with missing or invalid security configuration.
7. Add negative tests for missing policy, unknown action, malformed identity,
   stale policy, timeout, and dependency error.
8. Add audit events for every non-allow outcome. Record policy version and error
   class, not secret values or sensitive attributes.
9. Roll out in report-only mode only if the protected action remains blocked by
   another layer. Report-only cannot be the sole guard.
10. Turn on enforcement and watch deny rate, false denies, and support volume.

For legacy systems, the practical first step is often a wrapper rather than a
large rewrite. Put a narrow enforcement function in front of one high-risk
action, return a typed decision, and make the old code call through it. Once the
pattern is proved on one action, widen it to the next action group. This avoids
the common failure where a team creates a beautiful authorization service but
leaves half the old entry points calling the database directly.

When the existing code has many boolean helpers such as `canRead`,
`isOwner`, `isAdmin`, and `hasFeature`, resist the urge to invert them one by
one. First collect the action vocabulary. Then make one function answer the
question, "May this principal perform this action on this resource in this
context?" A single action question is easier to deny by default than a scattered
set of partial predicates.

Removing or relaxing the pattern when it stops earning its place.

1. Identify the business case for change. Usually it is excessive false denies,
   emergency availability requirements, or a low-risk public resource.
2. Classify the action. If it releases private data, changes authority, moves
   money, or creates durable state, do not replace the pattern with fail open.
3. Add a lower-risk alternative first: local cached deny policy, queue pending
   review, degraded read-only mode, or break-glass.
4. If an action is intentionally public, add an explicit public allow rule and
   tests. Do not rely on missing policy to mean public.
5. Delete dead deny branches only after telemetry shows they no longer receive
   traffic. Use Remove Dead Code from the refactoring family.
6. Update dashboards and runbooks so operators no longer chase a denied state
   that the system cannot produce.

## 15. Testing and verification

This dimension is engineering judgement.

The highest-value tests are negative tests. A fail-secure implementation is not
proved by showing that valid users can act. It is proved by showing that every
ambiguous state refuses the protected action.

Test at four levels.

- **Unit tests for decision mapping.** Given each decision enum value, assert
  that only `allow` invokes the protected action. Use a spy for the action and
  verify zero calls for deny, timeout, missing policy, parse error, and unknown
  value.
- **Contract tests for policy engines.** For each resource type and action,
  include at least one allowed case and several denied cases. Add a case for a
  new or unknown action name.
- **Integration tests for dependency faults.** Force the policy service, key
  store, group lookup, or policy bundle fetch to fail. Assert that the endpoint
  denies and emits an audit event.
- **End-to-end tests for side-effect ordering.** Inject a denial and assert that
  no email, payment, token, queue message, file write, or database mutation
  occurs.

Test doubles that apply.

- A fake policy decision point that can return every enum value and throw every
  transport error.
- A spy protected action that records whether it was invoked.
- A fake clock to test cache expiry, token expiry, and policy staleness.
- A stub audit sink to assert that denied paths are visible internally.
- A property test over action names where unknown names must deny.

Verification should include configuration. For Kubernetes NetworkPolicy, create
a staging namespace with the default deny policy and run probes for required
DNS, metrics, health, and application flows. For PostgreSQL row security, test
with the application role rather than the table owner or a bypass role. For
OPA-style policy, test both the policy result and the host application's error
mapping.

Add mutation tests where possible. Change an allow rule to deny and confirm the
happy-path test fails. Delete a policy entry and confirm the unknown-action test
fails closed. Replace a policy-service response with malformed JSON and confirm
the protected action spy is not called. These tests are valuable because fail
open bugs often hide in code that looks like ordinary error handling.

For release verification, compare the authorization matrix with the shipped
surface. Every route, RPC method, queue message, scheduled job action, and admin
button should map to a policy action. The matrix should include owner, reviewer,
and expected default. A blank cell is not neutral. It is a denied action until
filled.

## Code examples

Three languages are shown because the pattern is mostly a control-flow contract,
not a framework technique. Python shows exception-to-deny mapping. Rust shows
closed decision matching with `Result`. Go shows the common `context` timeout
shape.

### Python

```python
from enum import Enum


class Decision(Enum):
    ALLOW = "allow"
    DENY = "deny"


class PolicyUnavailable(Exception):
    pass


def policy_decision(user: str, action: str) -> Decision:
    if user == "alice" and action == "read_invoice":
        return Decision.ALLOW
    if user == "offline":
        raise PolicyUnavailable("policy service unavailable")
    return Decision.DENY


def read_invoice(user: str, invoice_id: str) -> str:
    try:
        decision = policy_decision(user, "read_invoice")
    except PolicyUnavailable:
        decision = Decision.DENY

    if decision is not Decision.ALLOW:
        return "denied"

    return f"invoice:{invoice_id}"


if __name__ == "__main__":
    assert read_invoice("alice", "inv_1") == "invoice:inv_1"
    assert read_invoice("bob", "inv_1") == "denied"
    assert read_invoice("offline", "inv_1") == "denied"
    print("ok")
```

### Rust

```rust
#[derive(Clone, Copy, PartialEq, Eq)]
enum Decision {
    Allow,
    Deny,
}

#[derive(Debug)]
enum PolicyError {
    Timeout,
}

fn decide(user: &str, action: &str) -> Result<Decision, PolicyError> {
    if user == "alice" && action == "refund" {
        return Ok(Decision::Allow);
    }
    if user == "slow" {
        return Err(PolicyError::Timeout);
    }
    Ok(Decision::Deny)
}

fn refund(user: &str) -> &'static str {
    match decide(user, "refund") {
        Ok(Decision::Allow) => "refunded",
        Ok(Decision::Deny) | Err(_) => "denied",
    }
}

fn main() {
    assert_eq!(refund("alice"), "refunded");
    assert_eq!(refund("bob"), "denied");
    assert_eq!(refund("slow"), "denied");
    println!("ok");
}
```

### Go

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"time"
)

type Decision int

const (
	Deny Decision = iota
	Allow
)

func decide(ctx context.Context, user string) (Decision, error) {
	if user == "alice" {
		return Allow, nil
	}
	if user == "slow" {
		<-ctx.Done()
		return Deny, ctx.Err()
	}
	return Deny, nil
}

func publish(user string) string {
	ctx, cancel := context.WithTimeout(context.Background(), time.Millisecond)
	defer cancel()

	decision, err := decide(ctx, user)
	if err != nil && !errors.Is(err, context.Canceled) {
		return "denied"
	}
	if decision != Allow {
		return "denied"
	}
	return "published"
}

func main() {
	if publish("alice") != "published" {
		panic("alice should publish")
	}
	if publish("bob") != "denied" {
		panic("bob should be denied")
	}
	if publish("slow") != "denied" {
		panic("slow should be denied")
	}
	fmt.Println("ok")
}
```

## 16. Observability signals

This dimension is engineering judgement.

Fail Securely should be visible without disclosing the protected data. Record
the decision and enough context to debug, but not the secret, row contents,
token, full policy document, or private subject attributes.

Useful logs and span attributes.

- `decision`, with values such as `allow`, `deny`, `missing_policy`,
  `stale_policy`, `timeout`, `malformed_input`, and `evaluation_error`.
- `enforcement_point`, naming the route, interceptor, gateway rule, database
  policy, or queue worker.
- `protected_action`, using a stable action name rather than free-form text.
- `resource_type`, not the full sensitive resource value unless the log sink is
  approved for it.
- `policy_version`, `bundle_hash`, or `configuration_generation`.
- `principal_type` and a hashed or internal principal identifier where allowed.
- `correlation_id` shared with the external generic error response.

Useful metrics.

- Allow and deny counters by action, resource type, and policy version.
- Non-allow counters by reason, especially timeout, missing policy, and
  malformed input.
- Policy decision latency histogram.
- Policy bundle age gauge.
- Cache hit, miss, and stale-hit counters for cached policy decisions.
- Break-glass counter by action and approver group.
- Protected side-effect counter, compared with allow counter. The side-effect
  count must not exceed the allow count.

A healthy dashboard shows stable deny rates, low decision latency, current
policy versions, and a small number of missing-policy denies during planned
rollouts. A failing dashboard shows sudden missing-policy growth after deploy,
timeout denies during a dependency outage, allow counts with no matching policy
version, or protected side effects that outnumber allowed decisions.

Alerting should separate security incidents from availability incidents. A high
deny rate may mean an attack, a bad rollout, a broken identity sync, or a true
policy change. The alert should include the reason distribution so responders
know which runbook to open.

A useful operational invariant is this: every protected side effect must be
explainable by a prior allow event with the same correlation ID or transaction
ID. If the side effect exists without the allow event, either telemetry is
broken or the action bypassed the enforcement point. Both cases need attention.
The invariant is simple enough for batch reconciliation and strong enough to
catch many placement mistakes.

Another useful invariant is policy freshness. A service can continue to run
with a locally cached deny set longer than it can run with a locally cached
allow set. Dashboards should make that distinction visible. A stale-deny cache
is an availability issue. A stale-allow cache can be a security issue.

## 17. Security and privacy implications

This dimension is engineering judgement except where sources are cited.

The pattern closes a common attack path: make the guard confused, absent, late,
or unable to load policy, then proceed through the default branch. OWASP's
Secure Coding Practices checklist says access-control failure handling should
deny by default and that access-control failures should be logged
([OWASP Secure Coding Practices checklist](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/stable-en/02-checklist/05-checklist),
verified 2026-08-02). The security benefit is strongest when the protected
action is placed behind one enforcement point and the action cannot run before
the decision.

The attack surface moves rather than disappears.

- Attackers may try to cause policy-service outages and create denial of
  service. Rate limits, bulkheads, local deny caches, and clear SLOs matter.
- Attackers may look for endpoints that bypass the central enforcement point.
  Route inventory and negative tests matter.
- Attackers may exploit stale cached allows after revocation. Short expiry and
  revocation events matter.
- Attackers may target break-glass because it is designed to bypass normal
  denial under defined conditions. Strong authentication, two-person review,
  time limits, and noisy audit matter.
- Attackers may mine error messages for policy internals. External responses
  should stay generic while internal logs carry the detail.

Privacy improves when missing or failed policy cannot reveal data. It can also
be harmed by over-detailed audit events. A deny log that records full resource
IDs, query text, group names, location, device posture, and raw user attributes
can become a sensitive dataset. Treat deny telemetry as security data with
restricted access, retention limits, and redaction.

Fail Securely is silent on cryptographic strength, identity proofing, policy
quality, and role design. It does not make a bad allow rule good. It means that
no rule, broken rule, late rule, or unreadable rule does not become an allow.

## 18. References

1. Jerome H. Saltzer and Michael D. Schroeder. "The Protection of Information
   in Computer Systems." Proceedings of the IEEE, volume 63, number 9, 1975.
   Section I.A.3, Design Principles, Fail-safe defaults and Complete mediation.
   https://web.mit.edu/Saltzer/www/publications/protection/Basic.html
   Verified 2026-08-02.
2. OWASP Cheat Sheet Series. "Authorization Cheat Sheet." Sections "Deny by
   Default," "Validate the Permissions on Every Request," and "Exit Safely when
   Authorization Checks Fail."
   https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
   Verified 2026-08-02.
3. OWASP Foundation. "Secure Coding Practices Quick Reference Guide." Checklist
   sections Access Control, Error handling and logging, and Communication
   security.
   https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/stable-en/02-checklist/05-checklist
   Verified 2026-08-02.
4. Amazon Web Services. "How AWS enforcement code logic evaluates requests to
   allow or deny access." AWS Identity and Access Management User Guide.
   https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic_policy-eval-denyallow.html
   Verified 2026-08-02.
5. Kubernetes project. "Network Policies." Kubernetes Documentation, Default
   policies section.
   https://kubernetes.io/docs/concepts/services-networking/network-policies/
   Verified 2026-08-02.
6. PostgreSQL Global Development Group. "Row Security Policies." PostgreSQL 18
   Documentation, chapter 5.9.
   https://www.postgresql.org/docs/current/ddl-rowsecurity.html
   Verified 2026-08-02.
7. Open Policy Agent project. "Policy Language." Default Keyword section.
   https://www.openpolicyagent.org/docs/policy-language
   Verified 2026-08-02.
