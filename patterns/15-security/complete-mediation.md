---
name: Complete Mediation
slug: complete-mediation
family: 15-security
category: Security
aliases: [Every Request Authorization, Per Access Authorization, Continuous Authorization]
first_described: "Saltzer and Schroeder 1975"
maturity: canonical
related: [fail-securely, least-privilege, zero-trust, defense-in-depth, secure-by-default]
incompatible_with: [ambient-authority, cached-authorization-without-invalidation, client-side-authorization]
verified: 2026-08-02
---

# Complete Mediation

## 1. Name, aliases, and lineage

The canonical name is Complete Mediation. Jerome H. Saltzer and Michael D.
Schroeder named it as one of their protection design principles in "The
Protection of Information in Computer Systems," published in *Proceedings of
the IEEE*, volume 63, issue 9, September 1975, pages 1278 to 1308. The
web-readable copy hosted by the University of Virginia records the principle in
the design principles section and frames it as checking each access to each
object for authority ([Saltzer and Schroeder](https://www.cs.virginia.edu/~evans/cs551/saltzer/),
verified 2026-08-02). The Office of Justice Programs catalog page confirms the
paper title, authors, journal issue, date, and page range
([OJP NCJRS abstract](https://www.ojp.gov/ncjrs/virtual-library/abstracts/protection-information-computer-systems),
verified 2026-08-02).

The common modern aliases are **every request authorization**, **per access
authorization**, **authorization on every request**, and **continuous
authorization**. Those names come from application security, cloud identity,
and zero trust practice rather than from the 1975 paper. OWASP's Authorization
Cheat Sheet says permissions should be validated on every request, no matter
where the request came from, and warns that one missed check can break
confidentiality or integrity ([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html),
verified 2026-08-02). The OWASP Developer Guide gives the same operational
shape: force requests through access checks unless they are public, deny by
default, and log authorization events ([OWASP Developer Guide, Enforce Access Controls](https://devguide.owasp.org/en/04-design/02-web-app-checklist/07-access-controls/),
verified 2026-08-02).

Complete Mediation is a security design principle more than an object-oriented
pattern. It does have pattern shape: a subject tries to perform an operation on
an object, a policy enforcement point intercepts the operation, a policy
decision point evaluates authority from current request context, and the
operation proceeds only when the decision is allow. The lineage runs through
access control models, operating systems, web application middleware, API
gateways, service meshes, cloud IAM, and zero trust gateways.

The name can be misleading. "Complete" does not mean the policy language covers
every business condition or that the system is free of bypasses. It means every
protected access path is mediated by the protection mechanism. Engineering
judgement: the hard part is not writing a deny rule. The hard part is proving
that there is no second route to the same object that avoids the check.

## 2. Problem and context

A system contains objects that are not public. Users, services, jobs, or
processes need to act on those objects. The authority behind an action can
change while the system is running: a role is revoked, a session expires, a
device becomes non-compliant, a record changes owner, an account crosses a
spending limit, or a feature flag removes a path from public use. If code
checks authority once and then treats later accesses as safe, the system can
carry stale authority long after the reason for access has disappeared.

The common code smell is a protected object reachable through several paths.
One handler checks ownership before returning `GET /accounts/:id`. A batch
export reuses the same repository method without the check. A websocket
subscription authenticates at connection time, then streams events after the
user is removed from a tenant. A signed download URL survives after a document
is marked confidential. A local cache stores "is admin" for speed and does not
drop it when an administrator changes the user's role. Each defect is different
in code, yet all violate the same pattern: the access path is not mediated at
the point where the object is used.

Complete Mediation fits systems where authorization is part of the correctness
contract, not a separate decoration. The protected object can be a row, file,
secret, API method, cluster object, queue message, key, build step, user
session, model response, or infrastructure resource. The subject can be a
person, workload identity, service account, background worker, CLI client,
browser session, plug-in, or process. The operation can be read, write, list,
execute, assume role, decrypt, sign, deploy, export, subscribe, print, or
delete.

The context requires three facts.

- There is a stable place where every access path can be forced through a
  policy enforcement point.
- The enforcement point can form a request context rich enough for the policy.
  At minimum it needs subject, action, object, and environment facts.
- The system can tolerate the cost of repeated checks, or can cache decisions
  with correct invalidation when authority changes.

AWS IAM is an example at cloud service scale. AWS documentation says that when
a principal uses the console, API, or CLI, AWS authenticates the principal when
needed, processes request context, then evaluates policy types to decide allow
or deny ([AWS IAM policy evaluation logic](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html),
verified 2026-08-02). Kubernetes is an example at control-plane scale:
Kubernetes authorization happens in the API server, which evaluates request
attributes against policies and returns allow or deny
([Kubernetes authorization](https://kubernetes.io/docs/reference/access-authn-authz/authorization/),
verified 2026-08-02).

Engineering judgement: Complete Mediation is most valuable where a missed check
creates a durable loss: data disclosure, resource deletion, tenant escape,
fraud, privilege escalation, or a key operation that cannot be undone. It is
less valuable for purely local convenience features where the server repeats
the real authorization later.

## 3. Forces

Engineering judgement: this dimension weighs design pressure. The cited
sources anchor known mechanisms; the ranking of trade-offs is engineering
reasoning.

- **Latency.** Sacrificed. A check on every access adds computation, policy
  lookup, attribute gathering, and sometimes a remote decision call. Sidecar or
  in-process checks reduce that cost but do not remove it.
- **Coupling.** Mixed. Business handlers become less coupled to ad hoc role
  logic when authorization lives behind one authorizer. They become more
  coupled to a clean definition of subject, action, resource, tenant, and
  policy version.
- **Consistency.** Favoured. A single mediation path makes it harder for one
  endpoint to apply a newer rule while another endpoint keeps an old rule.
- **Operability.** Favoured when every decision produces traceable facts:
  subject, action, resource, policy version, result, reason, and latency.
  Sacrificed when the decision path is opaque or when deny logs are too noisy.
- **Cost.** Sacrificed at build time. Teams must model resources, map actions,
  add tests, migrate call sites, and maintain policy data. That work competes
  with feature delivery.
- **Team topology.** Favoured when platform teams own the enforcement component
  and product teams own policy inputs for their resources. Sacrificed when one
  central team becomes the bottleneck for every permission change.
- **Cognitive load.** Mixed. Developers learn one access pattern instead of
  many local checks. They also must reason about decision context, cache
  lifetime, fallback behavior, and policy conflict.
- **Availability.** Sacrificed if the policy decision point is remote and the
  enforcement point fails closed. Favoured if deny-by-default prevents damage
  during partial failures.
- **Freshness.** Favoured. Re-checking authority on each access narrows the
  window where revoked authority remains usable.

The pattern favours correctness, auditability, and privilege freshness over raw
path speed. A system that picks speed without a revocation model is not making
a performance trade. It is creating a stale-authority bug.

## 4. Applicability and non-applicability

Reach for Complete Mediation when the following conditions hold.

- Protected objects have more than one access path, such as HTTP handlers,
  background jobs, websocket streams, admin consoles, report exports, and CLI
  tools.
- Authority can change after authentication, for example role revocation,
  tenant removal, device-state changes, account lock, data ownership transfer,
  policy rollout, or emergency deny.
- The same operation can be attempted by humans and workloads, and both need
  one authorization model.
- Data belongs to tenants, accounts, projects, regions, labels, classifications,
  or owners, and the object identity matters as much as the route identity.
- Caching authorization decisions is tempting, but cached decisions can become
  wrong when policy, subject, object, or environment facts change.
- Auditors, incident responders, or customers need a record of why access was
  granted or denied.
- The system exposes object identifiers controlled by callers, so object-level
  authorization must happen after the identifier is parsed.

Do NOT reach for Complete Mediation in these cases.

- **The resource is public by design.** Public assets, open health probes, and
  published documentation do not need per-subject authorization. They still need
  rate limits, input validation, and operational controls, but not a subject
  authority check.
- **The check cannot see the object being protected.** A route-level guard that
  knows only "user is logged in" cannot mediate account, record, or tenant
  ownership. Add object lookup or move the check closer to the data access.
- **The operation is a local UI affordance.** Hiding a button is useful for
  clarity, but it cannot be the authoritative decision. OWASP says access
  checks must happen server-side, at a gateway, or in a serverless function
  ([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html),
  verified 2026-08-02).
- **The object is already protected by a lower layer with the same subject and
  action model.** Duplicating checks at every layer can create policy drift.
  Prefer one authoritative enforcement point and make upper layers call through
  it.
- **The policy data is too stale for the risk.** If identity and object facts
  replicate slowly, a per-request check can still allow revoked access. Fix the
  data freshness path before treating mediation as complete.
- **The team cannot define what counts as an access.** Logging in, seeing a
  list item, reading a field, subscribing to a stream, downloading a cached
  file, and invoking a model can all be access. If the team cannot name the
  boundary, it cannot mediate it.
- **The result must remain valid after release.** Once data is exported to a
  client, printed, copied to a data lake, or sent to another service, later
  mediation cannot take it back. Use data minimization, labels, contractual
  controls, encryption, and downstream policy as separate controls.
- **A broad allow exists to rescue broken flows.** An emergency allow-all rule
  may be needed during an incident, but it conflicts with the pattern if it
  becomes the normal answer to policy misses.
- **Latency budgets are lower than policy-evaluation cost and the resource has
  low value.** Engineering judgement: use a coarser control, rate limit, or
  post-action audit when the asset value does not pay for per-access checks.

The second list matters because Complete Mediation can be misused as ritual.
Putting a decorator on every handler does not help if the decorator cannot see
the object, cannot fail closed, or can be skipped by another path.

## 5. Structure

The pattern has seven participants.

- **Subject.** The caller whose authority is being tested. It can be a user,
  service account, workload identity, process, token subject, or delegated
  actor.
- **Object.** The protected thing. It must have an identity usable by policy:
  path, row id, ARN, namespace/name, resource URI, tenant id, document id, key
  id, or stream name.
- **Action.** The operation requested on the object. Action names need enough
  precision to separate list from read, read from export, update from approve,
  and decrypt from sign.
- **Request Context.** The facts used for the decision. It usually contains
  subject attributes, object attributes, action, tenant, route, network facts,
  authentication strength, time, device posture, and policy version.
- **Policy Enforcement Point.** The mandatory gate in the execution path. It
  collects context, asks for a decision, blocks on deny, and records the result.
- **Policy Decision Point.** The evaluator. It receives the request context and
  returns allow or deny with a reason. It may be a function, library, service,
  sidecar, gateway, database row-security engine, or kernel mechanism.
- **Protected Operation.** The code or subsystem that performs the real work
  only after allow.

The key relationship is dominance: every path to the protected operation must
pass through the enforcement point. If a repository method, queue consumer,
file server, cache layer, websocket sender, or admin job can reach the object
without the enforcement point, the structure is false. Saltzer and Schroeder
warned that the principle covers normal operation as well as initialization,
recovery, shutdown, and maintenance ([Saltzer and Schroeder](https://www.cs.virginia.edu/~evans/cs551/saltzer/),
verified 2026-08-02).

The policy decision point may be local or remote. Local checks improve latency
and resilience. Remote checks centralize policy and telemetry. The enforcement
point owns fail behavior either way. If the decision point is unavailable, the
enforcement point must choose deny, allow under a narrow break-glass rule, or
serve only data already known to be public.

## 6. ASCII structure diagram

```text
  +-----------+       access request        +-----------------------+
  | Subject   | --------------------------> | Policy Enforcement    |
  | user, svc |                             | Point                 |
  +-----------+                             +-----------+-----------+
                                                        |
                                                        | context
                                                        v
                                             +----------+-----------+
                                             | Policy Decision      |
                                             | Point                |
                                             +----------+-----------+
                                                        |
                                               allow or deny
                                                        |
                       deny response <------------------+
                                                        |
                                                        v
                                             +----------+-----------+
                                             | Protected Operation  |
                                             | read, write, export  |
                                             +----------+-----------+
                                                        |
                                                        v
                                             +----------+-----------+
                                             | Protected Object     |
                                             | row, file, key, API  |
                                             +----------------------+

  Required invariant:

  Every route to the protected object crosses the enforcement point.
  Bypass paths are design defects, even when the main request path is checked.
```

## 7. Dynamics

The runtime flow has two loops. The fast path is the request. The slow path is
policy and attribute change. Complete Mediation works only when both are
connected, because cached decisions and local attributes must expire or be
invalidated when the slow path changes authority.

```text
Subject        Enforcement       Decision Point      Operation       Object
  |                 |                  |                 |             |
  | request action  |                  |                 |             |
  | on object ----> |                  |                 |             |
  |                 | build context    |                 |             |
  |                 |----------------> |                 |             |
  |                 |                  | evaluate policy |             |
  |                 |                  | and attributes  |             |
  |                 | <----------------|                 |             |
  |                 | allow            |                 |             |
  |                 |-----------------------------------> |             |
  |                 |                  |                 | access ----> |
  |                 | <-----------------------------------|             |
  | <---------------| response         |                 |             |
  |                 |                  |                 |             |
  |                 | deny             |                 |             |
  | <---------------| 403 or failure   |                 |             |

Policy admin       Policy Store       Decision Cache      Enforcement
     |                  |                   |                  |
     | revoke role ---> |                   |                  |
     |                  | publish version   |                  |
     |                  |-----------------> | invalidate       |
     |                  |                   |----------------> |
```

The first request has six observable decisions.

1. Identify the subject from trusted authentication state.
2. Identify the object from server-side lookup, not from a trusted client claim.
3. Name the action at the level the business rule uses.
4. Assemble request context from trusted sources.
5. Evaluate policy against the current context.
6. Execute the protected operation only when the decision is allow.

The second flow is where many systems fail. A role change, account disable,
object owner change, emergency deny, or policy publication must reach caches
and long-lived sessions. Saltzer and Schroeder called cached authority results
suspect unless authority changes update them consistently
([Saltzer and Schroeder](https://www.cs.virginia.edu/~evans/cs551/saltzer/),
verified 2026-08-02).

## 8. Implementation variants

**Middleware or filter mediation.** A web framework route passes through one
authorization middleware before the handler. It works well for route-level
actions such as "can create invoice" or "can open admin route." It is weak for
object-level checks unless the middleware loads the object or the handler calls
a second object guard. OWASP names filters and middleware as examples of
technology that can support application-wide authorization checks
([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html),
verified 2026-08-02).

**Policy guard at repository or service boundary.** Every data access goes
through a domain service that takes subject, action, and resource id. This
variant is strong when background jobs, API handlers, and CLI commands all use
the same boundary. It fails when developers bypass the service with direct SQL,
direct object storage reads, or helper methods that return raw records.

**Database row-level security.** The database mediates access to rows using
session variables, database roles, policies, and views. It guards against bugs
above the database and is powerful for tenant isolation. It can be harder to
express workflow rules, approval state, and non-database attributes unless the
database receives trusted context for each request.

**Gateway or service mesh mediation.** A gateway, reverse proxy, or sidecar
intercepts traffic before it reaches the service. Istio authorization evaluates
request context in Envoy at runtime and returns allow or deny
([Istio security concepts](https://istio.io/latest/docs/concepts/security/),
verified 2026-08-02). OPA-Envoy places OPA next to Envoy and lets Envoy check
with OPA before forwarding a request to the application
([OPA-Envoy plugin](https://www.openpolicyagent.org/docs/envoy),
verified 2026-08-02). This variant protects services without changing
application code, but policy authors must account for path normalization,
method mapping, identity propagation, and traffic that does not pass through
the proxy.

**Control-plane mediation.** A central API server mediates operations over
cluster or cloud resources. Kubernetes uses API-server authorization after
authentication and before admission, based on request attributes such as user,
groups, API resource, namespace, and verb ([Kubernetes authorization](https://kubernetes.io/docs/reference/access-authn-authz/authorization/),
verified 2026-08-02). AWS IAM evaluates policies for AWS service requests
using request context, explicit allow, implicit deny, and explicit deny
precedence ([AWS IAM policy evaluation logic](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic_policy-eval-denyallow.html),
verified 2026-08-02). This variant gives one mediation plane for many resource
types, at the cost of policy complexity.

**Capability mediation.** A caller presents an unforgeable token that encodes
or references authority. Saltzer and Schroeder define a capability as an
unforgeable ticket used as proof of authority for a named object
([Saltzer and Schroeder](https://www.cs.virginia.edu/~evans/cs551/saltzer/),
verified 2026-08-02). Capability systems can be fast because possession of the
capability is the check. They still need Complete Mediation at the point where
the capability is minted, delegated, revoked, attenuated, or presented.

**Decision caching with invalidation.** The enforcement point caches allow or
deny decisions for a short time. This is a performance variant, not an escape
from the pattern. A cache key must include subject, action, object, policy
version, and relevant context. Cache entries must expire quickly or be
invalidated when policy, group membership, object ownership, or emergency deny
state changes.

**TypeScript example.** This handler checks the concrete document id before
returning content. The policy function receives subject, action, and object.

```typescript
type User = { id: string; tenant: string; roles: string[] };
type StoredDocument = { id: string; tenant: string; owner: string; body: string };
type Action = "document:read" | "document:edit";

const documents = new Map<string, StoredDocument>([
  ["d1", { id: "d1", tenant: "acme", owner: "u1", body: "quarter plan" }],
]);

function may(user: User, action: Action, doc: StoredDocument): boolean {
  if (user.tenant !== doc.tenant) return false;
  if (user.roles.includes("auditor") && action === "document:read") return true;
  return doc.owner === user.id;
}

function readDocument(user: User, id: string): string {
  const doc = documents.get(id);
  if (!doc) throw new Error("not found");
  if (!may(user, "document:read", doc)) throw new Error("forbidden");
  return doc.body;
}

console.log(readDocument({ id: "u2", tenant: "acme", roles: ["auditor"] }, "d1"));
```

**Python example.** This domain service makes the authorization call mandatory
for the repository operation.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Principal:
    user_id: str
    tenant_id: str
    scopes: set[str]

@dataclass(frozen=True)
class Account:
    account_id: str
    tenant_id: str
    balance: int

accounts = {"a1": Account("a1", "t1", 1200)}

def authorize(principal: Principal, action: str, account: Account) -> bool:
    return (
        principal.tenant_id == account.tenant_id
        and action in principal.scopes
    )

def read_balance(principal: Principal, account_id: str) -> int:
    account = accounts[account_id]
    if not authorize(principal, "account:read", account):
        raise PermissionError("forbidden")
    return account.balance

print(read_balance(Principal("u1", "t1", {"account:read"}), "a1"))
```

**Go example.** This version treats a policy miss and a denied decision as
different outcomes so operators can tell policy outage from forbidden access.

```go
package main

import (
	"errors"
	"fmt"
)

type Principal struct {
	ID     string
	Tenant string
	Roles  map[string]bool
}

type Report struct {
	ID     string
	Tenant string
	Owner  string
	Body   string
}

func allowed(p Principal, action string, r Report) (bool, error) {
	if action == "" {
		return false, errors.New("missing action")
	}
	if p.Tenant != r.Tenant {
		return false, nil
	}
	return p.Roles["report_reader"] || p.ID == r.Owner, nil
}

func openReport(p Principal, r Report) (string, error) {
	ok, err := allowed(p, "report:read", r)
	if err != nil {
		return "", err
	}
	if !ok {
		return "", errors.New("forbidden")
	}
	return r.Body, nil
}

func main() {
	p := Principal{ID: "u7", Tenant: "t1", Roles: map[string]bool{"report_reader": true}}
	r := Report{ID: "r1", Tenant: "t1", Owner: "u9", Body: "margin report"}
	body, err := openReport(p, r)
	fmt.Println(body, err)
}
```

The three examples are intentionally small. The pattern is not the if statement
itself. The pattern is the invariant that protected operations are unreachable
except through the check, and that the check sees the actual object involved.

## 9. Known production uses

**AWS IAM.** AWS IAM policy evaluation is a named production use of Complete
Mediation at cloud-service scale. AWS documentation says a principal making a
console, API, or CLI request sends a request to AWS, and AWS evaluates the
relevant policy types against request context to decide allow or deny
([AWS IAM policy evaluation logic](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html),
verified 2026-08-02). AWS also documents that the enforcement code evaluates
all policies applicable to the request context, denies by default, requires
explicit allow for access, and gives explicit deny precedence
([AWS IAM deny and allow evaluation](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic_policy-eval-denyallow.html),
verified 2026-08-02).

**Kubernetes API server authorization.** Kubernetes mediates API requests in
the API server after authentication. Its documentation says the API server
evaluates request attributes against all policies, may consult external
services, and allows or denies the request. It also says all parts of an API
request must be allowed and that deny is the default when all authorizers have
no opinion ([Kubernetes authorization](https://kubernetes.io/docs/reference/access-authn-authz/authorization/),
verified 2026-08-02). That is Complete Mediation because cluster objects are
not supposed to be changed through paths that skip the API server's
authorization phase.

**Istio authorization in Envoy.** Istio applies authorization policies to
workloads in the mesh. Its security concepts page says each Envoy proxy runs an
authorization engine that evaluates request context against current policies at
runtime and returns allow or deny. It also describes sidecar and perimeter
proxies as policy enforcement points ([Istio security concepts](https://istio.io/latest/docs/concepts/security/),
verified 2026-08-02). The production pattern is per-request mediation outside
the application process, controlled by mesh policy.

**OPA with Envoy external authorization.** OPA-Envoy is an official integration
for policy checks at the proxy layer. The OPA documentation says Envoy's
external authorization filter calls an authorization service to check incoming
requests, and that the OPA-Envoy plugin implements the Envoy External
Authorization API so policies can be enforced without modifying the
microservice ([OPA-Envoy plugin](https://www.openpolicyagent.org/docs/envoy),
verified 2026-08-02). This is not proof that every deployment is correct. It is
proof that the pattern is embodied in a named production-grade integration.

## 10. Consequences

Engineering judgement: these consequences are design outcomes that follow from
the structure.

Positive consequences.

- **Bypass paths become visible.** When every protected operation has one
  gateway, direct object access stands out in code review.
- **Revocation becomes meaningful.** Role removal, account lock, and object
  ownership changes can take effect on the next mediated access instead of
  waiting for session end.
- **Authorization logic becomes testable.** Policy decisions can be unit tested
  as subject-action-object cases and integration tested through the enforcement
  point.
- **Audit records gain shape.** A decision log can capture who tried what on
  which object, from where, under which policy version, and with what result.
- **Least Privilege becomes easier to maintain.** Narrow permissions have value
  only when each access asks whether the permission applies.
- **Security reviews become concrete.** Reviewers can trace all data paths to
  the enforcement point instead of hunting for scattered ad hoc checks.
- **Incident response has a control point.** Emergency deny rules, account
  disablement, and policy rollback can act through a shared decision path.

Negative consequences.

- **Every request pays a cost.** Context assembly, policy lookup, and decision
  evaluation consume CPU, memory, network budget, and engineering time.
- **The enforcement point becomes load-bearing.** A bug, outage, or deployment
  error in that component can block valid work or permit invalid work.
- **Policy drift can move to another layer.** Teams may still create duplicate
  rules in UI, gateway, service, and database layers unless ownership is clear.
- **The object model must be explicit.** Vague actions such as "manage" or
  object ids hidden inside blobs make mediation weak.
- **Caching is hard to make correct.** A stale allow decision can be worse than
  no cache because it carries the appearance of policy compliance.
- **Denied access can look like an outage.** Users and operators need clear
  errors, reason codes, and dashboards.
- **Bootstrapping and maintenance are dangerous.** Initialization, migrations,
  repair jobs, and backup restores often need special authority. Saltzer and
  Schroeder warned that the principle covers those lifecycle phases too
  ([Saltzer and Schroeder](https://www.cs.virginia.edu/~evans/cs551/saltzer/),
  verified 2026-08-02).

## 11. Failure modes and misuse

Engineering judgement: each item is written as an observable production triple.

- **Symptom.** A user can fetch another tenant's record by changing an id in a
  URL. **Cause.** The route checked authentication but did not check the
  resolved object's tenant or owner. **Fix.** Load the object before allow, pass
  subject, action, and object attributes to the policy, and add negative tests
  for cross-tenant ids.
- **Symptom.** An admin loses a role but retains admin access until logging out.
  **Cause.** The application stores role decisions in the session and never
  refreshes or invalidates them. **Fix.** Store only identity in the session,
  evaluate authorization per access, and invalidate decision caches on role
  changes.
- **Symptom.** API routes are protected, but CSV export, search index, or report
  jobs leak records. **Cause.** Background paths read the same objects through a
  repository that lacks mediation. **Fix.** Move authorization to the shared
  domain boundary or use separate job principals with explicit scoped policy.
- **Symptom.** Websocket clients keep receiving events after tenant removal.
  **Cause.** Authorization happened only at subscription creation. **Fix.**
  Re-check on each event send or bind subscription lifetime to policy version
  and tenant membership changes.
- **Symptom.** A gateway denies `/private`, yet `/public/../private` reaches the
  upstream. **Cause.** The enforcement point and upstream normalize paths
  differently. **Fix.** Authorize on the canonical path the upstream will serve,
  or normalize before both policy evaluation and routing. OPA's Envoy policy
  primer warns that parsed path handling can differ from upstream path handling
  in ways that policy authors must account for ([OPA Envoy policy primer](https://www.openpolicyagent.org/docs/envoy/primer),
  verified 2026-08-02).
- **Symptom.** Operators see a surge of HTTP 403 responses but cannot tell
  whether policy denied access or the decision service failed. **Cause.** The
  enforcement point collapses deny and error into one status without reason
  codes. **Fix.** Emit separate metrics for denied, indeterminate, timeout, and
  policy-error outcomes.
- **Symptom.** A direct object storage URL works after the app marks the file
  private. **Cause.** The application mediated metadata access but delegated
  file access to a token whose lifetime outlived the authorization state.
  **Fix.** Shorten token lifetime, scope tokens to one object and action, bind
  tokens to policy version where supported, or proxy downloads through the
  enforcement point.
- **Symptom.** A migration script repairs production data by connecting as a
  broad database owner. **Cause.** Maintenance paths are exempt from the normal
  model. **Fix.** Give maintenance jobs named principals, bounded actions, audit
  logs, and break-glass expiry.
- **Symptom.** The policy says "manager can approve expense," but managers can
  approve their own expenses. **Cause.** The action was mediated, but the object
  relationship needed by the rule was not present in context. **Fix.** Include
  requester, owner, approver, amount, state, and conflict-of-interest attributes
  in the decision input.
- **Symptom.** Unit tests pass for policy rules, but a new endpoint ships
  without any authorization call. **Cause.** Tests target the policy function
  but not the mandatory enforcement invariant. **Fix.** Add route inventory
  tests, static checks, or integration tests that fail when protected handlers
  lack the authorization wrapper.

The main misuse is treating Complete Mediation as "we have an auth library."
Authentication names the subject. Authorization decides whether that subject can
do this action to this object now. A login library is not Complete Mediation.

## 12. Trade-off matrix

<table>
  <thead>
    <tr>
      <th>Force</th>
      <th>Complete Mediation</th>
      <th>Session-Time Authorization</th>
      <th>Route Guard Only</th>
      <th>Object Capability</th>
      <th>Database Row-Level Security</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Latency</td>
      <td>Higher per access unless local or cached.</td>
      <td>Low after login.</td>
      <td>Low at route entry.</td>
      <td>Low at use when token verification is local.</td>
      <td>Often low near the data, but can add query cost.</td>
    </tr>
    <tr>
      <td>Coupling</td>
      <td>Couples callers to a shared subject-action-object model.</td>
      <td>Couples features to session claims.</td>
      <td>Couples policy to URL shape.</td>
      <td>Couples access to token minting and delegation rules.</td>
      <td>Couples policy to schema and database session context.</td>
    </tr>
    <tr>
      <td>Consistency</td>
      <td>High when every path shares one enforcement point.</td>
      <td>Weak after role or object changes.</td>
      <td>Medium for HTTP paths, weak for jobs and data exports.</td>
      <td>Strong for token-presented operations, weak after release.</td>
      <td>Strong for database rows, weaker for files and external APIs.</td>
    </tr>
    <tr>
      <td>Operability</td>
      <td>Good with reason codes and decision logs.</td>
      <td>Hard to explain stale session behavior.</td>
      <td>Simple dashboards, but blind below route level.</td>
      <td>Good if token provenance and expiry are logged.</td>
      <td>Good for query audit, harder across services.</td>
    </tr>
    <tr>
      <td>Cost</td>
      <td>Higher design and rollout cost.</td>
      <td>Lower implementation cost.</td>
      <td>Lower early cost, higher bug-hunt cost later.</td>
      <td>Higher design cost for revocation and delegation.</td>
      <td>Higher schema and database policy cost.</td>
    </tr>
    <tr>
      <td>Team topology</td>
      <td>Works when platform owns enforcement and teams own policy inputs.</td>
      <td>Works for small apps with one team.</td>
      <td>Works for route-owned product teams.</td>
      <td>Works for distributed systems with clear token minting authority.</td>
      <td>Works where database ownership is central and disciplined.</td>
    </tr>
    <tr>
      <td>Cognitive load</td>
      <td>Medium. One model, more context design.</td>
      <td>Low until revocation and object rules appear.</td>
      <td>Low for endpoints, high for hidden data paths.</td>
      <td>High for transfer, attenuation, and expiry.</td>
      <td>Medium for SQL users, high for application developers new to it.</td>
    </tr>
    <tr>
      <td>Freshness</td>
      <td>Best when decisions are uncached or invalidated.</td>
      <td>Poor until session refresh.</td>
      <td>Good at route entry, poor for long-lived flows.</td>
      <td>Bounded by token lifetime and revocation model.</td>
      <td>Good for database-backed facts.</td>
    </tr>
  </tbody>
</table>

Engineering judgement: Database row-level security can be a form of Complete
Mediation for database rows, but it is an alternative at the application
architecture level because it moves the enforcement point from service code to
the database.

## 13. Related and incompatible patterns

**Fail Securely** composes with Complete Mediation. When the policy decision
point times out, configuration is missing, or context cannot be built, the
enforcement point needs a defined failure result. OWASP recommends denying by
default and handling failed access-control checks safely
([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html),
verified 2026-08-02).

**Least Privilege** depends on Complete Mediation. A narrow grant has little
value if the system later uses an unchecked path to the object. Least Privilege
shrinks authority. Complete Mediation asks that authority on each protected
access.

**Zero Trust** generalizes the idea beyond one application. NIST SP 800-207
defines zero trust as a cybersecurity model that removes implicit trust and
uses risk-aware access decisions for enterprise resources
([NIST SP 800-207](https://csrc.nist.gov/pubs/sp/800/207/final),
verified 2026-08-02). Complete Mediation is one local design move inside that
larger model.

**Defense in Depth** composes with the pattern. The enforcement point may sit
at gateway, service, database, and storage layers. Engineering judgement:
multiple layers help only when they share a policy contract or guard different
failure classes. Duplicate unclear rules can create conflict rather than
security.

**Attribute-Based Access Control** is a policy model commonly used inside the
decision point. NIST SP 800-162 defines ABAC as determining authorization by
evaluating attributes of the subject, object, requested operation, and
environment against policy rules
([NIST SP 800-162](https://csrc.nist.gov/pubs/sp/800/162/final),
verified 2026-08-02). Complete Mediation says when to evaluate. ABAC says what
facts and rules can drive the evaluation.

**Reference Monitor** is the architectural ancestor that many readers expect.
The classic reference monitor idea is an always-invoked, tamper-resistant,
small enough to analyze mediation mechanism. Complete Mediation maps to the
"always invoked" part. Engineering judgement: most application code implements
a reference-monitor-like boundary without satisfying the stronger kernel-era
claims about tamper resistance and proof.

**Client-Side Authorization** conflicts with the pattern when it is decisive.
Client checks can improve user experience by hiding actions that will be denied,
but they cannot mediate access because a client can be modified or bypassed.

**Ambient Authority** conflicts with the pattern. If code can reach resources
through process-wide credentials without naming subject, action, and object, the
real access occurs outside the mediated path.

**Cached Authorization Without Invalidation** conflicts with the pattern. A
cache is allowed only when changes in authority reach the cache through expiry,
versioning, event invalidation, or a bounded risk decision.

## 14. Refactoring path in and out

To introduce Complete Mediation into existing code, use a staged path.

1. **Inventory protected objects.** Name the resource types, object identifiers,
   and actions. Include files, jobs, streams, exports, admin routes, and
   maintenance scripts. Cross reference the security family entries on
   Defense in Depth and Least Privilege when selecting protection layers.
2. **Find access paths.** Use route listings, SQL call sites, object storage
   clients, queue consumers, websocket senders, CLI commands, and cron jobs.
   The question is "who can touch this object," not "which controller is
   public."
3. **Create a policy decision interface.** Start with
   `allow(subject, action, object, context) -> decision`. Return reason,
   policy version, and decision latency where possible.
4. **Add a policy enforcement wrapper.** Put it at the narrowest shared
   boundary that dominates access. In many codebases this is a domain service
   rather than every controller.
5. **Move one resource type.** Pick a sensitive resource with clear ownership
   rules. Replace local role checks with calls to the shared authorizer.
6. **Add negative tests.** For every allow case, add a denied case for wrong
   tenant, wrong owner, missing role, expired subject, or wrong object state.
7. **Add bypass tests.** Route inventory, repository tests, or static checks
   should fail when protected operations are reachable without the enforcement
   call.
8. **Instrument decisions.** Log allow, deny, indeterminate, missing context,
   policy version, and latency. Avoid logging secrets or sensitive object
   contents.
9. **Migrate background paths.** Jobs and exports often carry the real gaps.
   Give each job a named principal and policy scope instead of broad process
   authority.
10. **Constrain caches.** Add policy version, subject version, object version,
    and expiry to decision-cache keys. Prefer short-lived cache entries until
    invalidation is proven.
11. **Remove direct access.** Delete or make private methods that bypass the
    enforcement point. Cross reference refactoring entries such as Extract
    Function, Move Function, Encapsulate Variable, and Replace Conditional with
    Polymorphism where they help isolate policy code.
12. **Roll out in report-only mode where risk allows.** Compare would-deny logs
    with real traffic before flipping enforcement for complex legacy flows.

To remove Complete Mediation when it stops earning its place, reverse the path
without creating silent broad access.

1. Prove the object is public, protected by a lower authoritative layer, or no
   longer present.
2. Remove policy rules for that resource type after traffic confirms they are
   unused.
3. Replace the enforcement wrapper with a simpler public or lower-layer call.
4. Keep audit logging if the operation remains sensitive for abuse or cost.
5. Delete stale policy tests and update the resource inventory.

Engineering judgement: the safest removal is often a move, not deletion. For
example, moving row mediation from service code to database row-level security
can reduce application code while preserving the invariant.

## 15. Testing and verification

Engineering judgement: testing must prove both policy correctness and placement
correctness. Many teams test the first and miss the second.

Test policy decisions as a table of subject-action-object cases. Include allow,
deny, missing attribute, stale object state, cross-tenant access, disabled
account, expired credential, and break-glass paths. For ABAC-style policies,
vary subject attributes, object attributes, operation, and environment facts,
matching the attribute categories named by NIST SP 800-162
([NIST SP 800-162](https://csrc.nist.gov/pubs/sp/800/162/final),
verified 2026-08-02).

Test enforcement placement with integration tests. A request that reaches the
handler through HTTP, a job, a CLI command, and a websocket should all produce
the same authorization result for the same subject and object. OWASP recommends
tests that validate permissions defined during design are enforced
([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html),
verified 2026-08-02). The Developer Guide also calls for unit and integration
tests that document and verify business rules and authorization criteria
([OWASP Developer Guide, Enforce Access Controls](https://devguide.owasp.org/en/04-design/02-web-app-checklist/07-access-controls/),
verified 2026-08-02).

Use the following test doubles carefully.

- **Fake policy decision point.** Good for handler tests. It can assert that the
  handler requested a decision with the expected subject, action, and object.
- **Real policy engine with fixture data.** Good for policy tests. It catches
  policy syntax, precedence, and missing-attribute behavior.
- **Denying policy double.** Good for proving the protected operation does not
  run after deny.
- **Unavailable decision point double.** Good for fail-secure tests. It should
  drive timeout, error, and indeterminate branches.
- **Audit sink double.** Good for proving decisions are logged without exposing
  sensitive content.

Property tests are useful when object ownership and tenant rules are regular.
Generate subjects and objects with varied tenants and assert that mismatched
tenants never allow access. Mutation tests are valuable for route guards: remove
or invert the authorization call and verify that tests fail. Static checks can
scan for direct use of raw repositories, object-storage clients, or SQL tables
from layers that should be mediated.

Harder tests appear around long-lived flows. Websocket streams, cached signed
URLs, and background jobs need revocation tests: grant access, start the flow,
remove authority, then verify the next access is denied or the flow is closed.
Policy-cache tests need version changes, expiry, and invalidation events.

Verification is not limited to tests. During rollout, compare report-only
decisions against existing behavior. Track false deny cases by route and
resource. Flip enforcement per resource type, not across the whole system at
once, unless the policy model is already proven in production.

## 16. Observability signals

Engineering judgement: Complete Mediation should be visible in production. A
silent authorizer becomes impossible to tune and dangerous to trust.

Log one structured authorization event per decision, with sampling only after
baseline behavior is known. Useful fields are decision id, request id, trace id,
subject id or stable pseudonym, subject type, tenant, action, resource type,
resource id or safe hash, policy version, decision result, reason code,
decision latency, cache hit, enforcement point name, and decision-point status.
Do not log secrets, raw tokens, private document contents, or sensitive field
values.

Metrics should separate at least these counters and histograms.

- `authz_decisions_total` by result: allow, deny, indeterminate, error,
  timeout.
- `authz_decision_latency_ms` by enforcement point and policy version.
- `authz_cache_hit_ratio` by resource type.
- `authz_policy_version_active` by service or proxy.
- `authz_missing_context_total` by missing field.
- `authz_denies_total` by action and reason.
- `authz_bypass_guard_failures_total` from static or runtime guardrails.

A healthy dashboard shows stable decision volume by route, low timeout rate,
bounded latency, expected deny ratios, current policy versions, and no missing
context spikes. A failing dashboard shows one of these shapes: deny spikes after
policy rollout, allow spikes after a default change, decision latency near the
request timeout, mixed policy versions across instances, high indeterminate
rate, or missing object attributes for a newly shipped endpoint.

Traces should place an `authz.check` span before the protected operation. Add
attributes for action, resource type, result, policy version, cache hit, and
decision latency. The span should be missing only for public resources. If a
protected handler has no `authz.check` span, the trace itself becomes evidence
of bypass.

Alerting should be narrow. Page for decision point outage, fail-open events,
policy version skew on sensitive services, and bypass detector hits. Ticket for
unexpected deny-rate changes, high latency, and missing context. Too many
access-denied alerts train operators to ignore the very signal they need during
an incident.

## 17. Security and privacy implications

Engineering judgement: this pattern closes one class of access-control failure
and opens operational risks around policy data, logs, and central services.

Complete Mediation closes bypass, stale-authority, and inconsistent-check
risks. It is the direct answer to insecure direct object reference defects
where callers change an object id and reach data they should not access. OWASP
links missed per-request checks to authorization bypass, horizontal privilege
escalation, vertical privilege escalation, and IDOR-style failures
([OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html),
verified 2026-08-02).

The pattern also supports revocation. If a user is removed from a tenant, a
token is disabled, or an object changes owner, the next mediated access can
deny. That is not automatic. The decision point needs current enough identity,
policy, and object facts. Decision caches need expiry or invalidation.
Long-lived streams need re-check points.

The main new attack surface is the enforcement and decision path. An attacker
who can alter policy, forge subject attributes, poison object attributes, skip
the enforcement point, or force a fail-open mode can turn the pattern into a
central bypass. Protect policy stores, policy publication, subject claim
mapping, service-to-service identity, and emergency override controls as
privileged assets. Use separation of privilege for policy changes that grant
broad access, and audit policy changes with the same care as data access.

Privacy implications are mixed. Decision logs help accountability, but they can
become a sensitive dataset: who tried to read which record, when, from where,
and with what outcome. Minimize logged object details, hash or redact resource
ids where needed, apply retention limits, and restrict access to authorization
logs. The log should be strong enough for incident response without becoming a
new surveillance database.

Complete Mediation is silent about cryptography, data minimization, consent,
purpose limitation, and downstream use after release. A user authorized to
download a file can still copy it. A service authorized to read a row can still
send it elsewhere unless another control mediates egress. Treat mediation as
one layer in a security architecture, not as the whole privacy story.

The pattern is also silent about policy correctness. It can reliably enforce a
bad rule. That means policy review, testing, change control, and observability
are part of the security posture. Engineering judgement: a simple, consistently
mediated rule is often safer than a clever policy language that few developers
can read.

## 18. References

- Jerome H. Saltzer and Michael D. Schroeder, "The Protection of Information in
  Computer Systems," *Proceedings of the IEEE*, volume 63, issue 9, September
  1975, pages 1278 to 1308. University of Virginia HTML copy,
  https://www.cs.virginia.edu/~evans/cs551/saltzer/, verified 2026-08-02.
- Office of Justice Programs, NCJRS Virtual Library, "Protection of Information
  in Computer Systems," catalog entry for Saltzer and Schroeder, *Proceedings
  of the IEEE*, volume 63, issue 9, September 1975, pages 1278 to 1308,
  https://www.ojp.gov/ncjrs/virtual-library/abstracts/protection-information-computer-systems,
  verified 2026-08-02.
- Amazon Web Services, AWS Identity and Access Management User Guide, "Policy
  evaluation logic,"
  https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html,
  verified 2026-08-02.
- Amazon Web Services, AWS Identity and Access Management User Guide, "How AWS
  enforcement code logic evaluates requests to allow or deny access,"
  https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic_policy-eval-denyallow.html,
  verified 2026-08-02.
- Kubernetes Documentation, "Authorization,"
  https://kubernetes.io/docs/reference/access-authn-authz/authorization/,
  verified 2026-08-02.
- Istio Documentation, "Security,"
  https://istio.io/latest/docs/concepts/security/, verified 2026-08-02.
- Open Policy Agent Documentation, "OPA-Envoy Plugin,"
  https://www.openpolicyagent.org/docs/envoy, verified 2026-08-02.
- Open Policy Agent Documentation, "Policy Primer via Examples,"
  https://www.openpolicyagent.org/docs/envoy/primer, verified 2026-08-02.
- OWASP Cheat Sheet Series, "Authorization Cheat Sheet,"
  https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html,
  verified 2026-08-02.
- OWASP Developer Guide, "Enforce Access Controls,"
  https://devguide.owasp.org/en/04-design/02-web-app-checklist/07-access-controls/,
  verified 2026-08-02.
- Vincent C. Hu, David Ferraiolo, Rick Kuhn, Adam Schnitzer, Kenneth Sandlin,
  Robert Miller, and Karen Scarfone, NIST Special Publication 800-162, "Guide
  to Attribute Based Access Control (ABAC) Definition and Considerations,"
  January 2014, https://csrc.nist.gov/pubs/sp/800/162/final, verified
  2026-08-02.
- Scott Rose, Oliver Borchert, Stu Mitchell, and Sean Connelly, NIST Special
  Publication 800-207, "Zero Trust Architecture," August 2020,
  https://csrc.nist.gov/pubs/sp/800/207/final, verified 2026-08-02.
