---
name: Separation of Duties
slug: separation-of-duties
family: 15-security
category: Security
aliases: [Segregation of Duties, SoD, Four Eyes, Two-Person Control, Dual Authorization]
first_described: "Clark and Wilson 1987"
maturity: canonical
related: [least-privilege, role-based-access-control, defense-in-depth, complete-mediation, zero-trust, audit-log]
incompatible_with: [shared-administrator-account, break-glass-without-review, self-approval]
verified: 2026-08-02
---

# Separation of Duties

## 1. Name, aliases, and lineage

The canonical name is Separation of Duties. Security, audit, accounting, and
identity teams also use Segregation of Duties, SoD, Four Eyes, Two-Person
Control, dual control, maker-checker, and dual authorization. This entry uses
Separation of Duties because that is the wording used by NIST SP 800-53 Rev. 5
control AC-5, which says organizations identify duties that require separation
and define access authorizations to support that separation
([NIST SP 800-53 Rev. 5, AC-5](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf),
verified 2026-08-02).

The software security lineage is older than modern cloud IAM. David D. Clark
and David R. Wilson published "A Comparison of Commercial and Military Computer
Security Policies" at the 1987 IEEE Symposium on Security and Privacy. DBLP
records the paper, the authors, the year, the DOI, and the proceedings pages
184-195 ([DBLP record for Clark and Wilson 1987](https://dblp.org/rec/conf/sp/ClarkW87),
verified 2026-08-02). Their work framed commercial integrity as a transaction
problem rather than only a secrecy problem. The entry does not quote the closed
paper text. The lineage claim here is limited to the verified bibliographic
record and to later standards that name the control directly.

Role-based access control became a common technical carrier for this pattern.
NIST's RBAC project says David Ferraiolo and Rick Kuhn formalized RBAC in 1992,
that the NIST model was adopted as ANSI INCITS 359-2004, and that the 2012
standard has two parts: an RBAC reference model and an administrative functional
specification ([NIST RBAC project](https://csrc.nist.gov/projects/role-based-access-control),
verified 2026-08-02). RBAC did not invent Separation of Duties. It gave system
builders a practical way to express mutually exclusive roles, bounded
delegation, and review duties at software scale.

The aliases carry different emphasis.

- **Segregation of Duties.** Common in finance, audit, and enterprise identity.
  It often appears in governance, risk, and compliance tools.
- **Four Eyes.** Common in review flows. One actor creates or changes, another
  actor approves.
- **Two-Person Control.** Common for high-risk operational actions such as key
  ceremonies, audit data deletion, backup destruction, and emergency access.
  NIST uses dual authorization as a control enhancement in several controls,
  including audit information protection and media sanitization
  ([NIST SP 800-53 Rev. 5, AU-9(5) and MP-6(7)](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf),
  verified 2026-08-02).
- **Maker-checker.** Common in banking and business workflow. One role prepares
  an instruction, another role approves or releases it.

The heart of the pattern is not a second click. It is a conflict rule: no single
subject may both prepare and complete a sensitive outcome, and no single subject
may both create the evidence and be the only party able to alter that evidence.

## 2. Problem and context

A system has operations where one trusted actor can cause damage and hide it.
The actor may be a person, service account, CI job, controller, administrator,
or vendor support session. The sensitive operation may be payment release,
production deployment, audit log deletion, role assignment, key rotation, data
export, backup destruction, policy change, or access approval. The danger is
not that the actor has no job to do. The danger is that the same actor can do
too many linked jobs in one chain.

The usual code smell looks mundane. A user creates a vendor, enters an invoice,
approves the invoice, changes the payment destination, releases payment, and
edits the audit note. A developer opens a pull request, approves the same pull
request through a bot account, and merges it to production. A platform engineer
creates an IAM role, attaches administrator permissions, assumes the role, and
changes the policy boundary that was supposed to constrain the role. A cluster
operator can create a Kubernetes ClusterRole that includes `secrets/list` and
then bind that role to their own account. Each step may have authentication and
authorization. The problem is the composition of those grants.

NIST AC-5 puts the software shape plainly: identify duties that require
separation, then define system access authorizations that support those
separations ([NIST SP 800-53 Rev. 5, AC-5](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf),
verified 2026-08-02). The discussion warns that SoD violations can span
systems and application domains, so policy has to consider the whole system,
not only one service boundary. That is why a pure application permission check
is often too narrow.

The pattern fits when the business action has at least two distinguishable
duties. Those duties may be initiate and approve, administer and audit,
develop and deploy, request and grant, configure and operate, sign and release,
or custody and reconciliation. If the duties are not named, the code cannot
enforce them. If the subjects are not distinct, the split is theater.

The context has four preconditions.

- The sensitive action can be decomposed into named duties.
- The system can identify the actor for each duty with enough confidence for
  the risk of the action.
- The enforcement point can compare actors, roles, groups, or attributes across
  steps in the same workflow.
- The organization accepts the added queueing cost when an action waits for a
  second role, a different service account, or a separate approval path.

Engineering judgement: Separation of Duties is strongest when it is modeled as
data and enforced at transition points. It is weakest when written as a policy
sentence that reviewers must remember under time pressure.

## 3. Forces

Engineering judgement: this dimension weighs operational pressures. The cited
standards and product docs name mechanisms; the trade-offs are design
reasoning.

- **Fraud and insider risk.** Favoured. The pattern changes a solo abuse path
  into a collusion path. It does not eliminate collusion. It raises the number
  of parties, the audit surface, and the chance that one party says no.
- **Error containment.** Favoured. A second role catches wrong account numbers,
  wrong namespaces, unintended production targets, stale runbooks, and risky
  policy changes before release.
- **Latency.** Sacrificed. A workflow that waits for approval, status checks,
  or separate credentials is slower than a single broad role. The cost is most
  visible during incidents, close deadlines, and small-team support rotations.
- **Coupling.** Mixed. Duties become explicit policy data, which lowers coupling
  between business logic and named people. The workflow becomes coupled to an
  identity source, approval state, and escalation rules.
- **Consistency.** Favoured when the same decision service is used across UI,
  API, CLI, and background jobs. Sacrificed when each product team implements a
  different "approver cannot be requester" check.
- **Operability.** Favoured for investigations because each phase has a named
  actor and timestamp. Sacrificed when approvals are invisible queues with no
  service-level target, stale ownership, or no override path.
- **Cost.** Sacrificed. The cost includes policy design, role mining, exception
  management, directory hygiene, audit review, and training.
- **Team topology.** Favoured when separate teams own different duties, such as
  development, release, platform, and security. Sacrificed in tiny teams where
  the same person carries many roles and compensating controls become the only
  practical option.
- **Cognitive load.** Sacrificed. A reader must reason about workflow state,
  prior actors, role membership, approval groups, and policy exceptions.
- **Availability.** Mixed. The pattern can block bad actions, but it can also
  block valid urgent work when no approver is available. Break-glass design and
  post-event review determine whether this is acceptable.

A design that says "every risky action needs two approvals" has not made the
trade. Low-risk actions become slow. High-risk actions may still be unsafe if
the two approvers come from the same compromised group. The force to manage is
the cost of delay against the cost of unreviewed authority.

## 4. Applicability and non-applicability

Reach for Separation of Duties when the following hold.

- A user can both create and approve an outcome that moves money, grants access,
  changes production, deletes evidence, exports regulated data, or alters audit
  scope.
- The sensitive action has a meaningful second duty. Examples include submit
  and approve, build and release, request and grant, operate and audit, rotate
  and verify, or propose and apply.
- The system can persist the identity of the actor for each duty and compare it
  at the next transition.
- A second actor has enough context to judge the request rather than rubber
  stamping it.
- Collusion is less likely than solo misuse for the risk being addressed.
- A policy engine, workflow engine, database constraint, repository rule, cloud
  IAM boundary, or admission controller can apply the rule on every path.
- The business can tolerate queueing, expiry, rejection, and escalation states.
- Evidence matters. Auditors, incident responders, or platform owners need to
  know who requested, who approved, who executed, and which policy allowed it.

Non-applicability list.

- **Single-person trusted prototypes.** If the system is a short-lived internal
  prototype with no money movement, production access, regulated data, or shared
  infrastructure, the queueing cost is likely higher than the control value.
- **Actions with no separable duty.** If the action is an atomic read of data
  already permitted to the actor, adding a second approver only hides an access
  control problem. Use Least Privilege or purpose limitation instead.
- **High-frequency hot paths.** Do not put human approval on request paths such
  as per-message queue handling, image transformation, or API reads. Use bounded
  service accounts, rate limits, and anomaly detection.
- **Teams where the approver cannot understand the change.** Approval without
  competence creates latency without control. Use automated checks, policy as
  code, or trained ownership first.
- **Break-glass paths with no post-event review.** Emergency access can violate
  normal SoD, but it must be time-boxed, logged, and reviewed. Otherwise it is a
  permanent bypass.
- **Data-driven routing that needs independent constraints.** If the conflict
  depends on account, project, region, or customer, simple role separation may
  be too coarse. Object-scoped dynamic SoD or ABAC may fit better.
- **Two accounts controlled by one person.** If the same person can act through
  two identities, the system has account separation, not duty separation.
- **Shared administrator accounts.** The pattern depends on accountability.
  Shared credentials erase the subject history needed for enforcement.
- **Pure notification flows.** Emailing a reviewer after an irreversible action
  is audit, not Separation of Duties.
- **Small teams with no viable second actor.** Use compensating controls:
  short-lived credentials, recorded sessions, immutable logs, delayed execution,
  automatic rollback, and external review.

## 5. Structure

The participants are named by security role rather than class name.

- **Duty Catalog.** A versioned map of duties that must be separated. It names
  actions such as `payment.prepare`, `payment.approve`, `role.create`,
  `role.bind`, `deploy.promote`, and `audit.delete`. It also names conflict
  pairs, such as `requester != approver` or `role_author != role_binder`.
- **Subject.** A human or workload identity. The subject has stable identity
  claims, group membership, role assignments, and optional attributes such as
  department, tenant, on-call status, or break-glass state.
- **Resource Scope.** The object or boundary in which the duty matters:
  payment batch, repository, branch, namespace, cloud account, secret path,
  environment, customer, region, or audit stream.
- **Workflow Record.** The durable state that carries prior actors and
  decisions. Without this record, dynamic SoD cannot compare who performed past
  steps.
- **Policy Decision Point.** The component that answers whether a subject may
  perform a duty on a resource in the current state. It may be an IAM engine,
  admission controller, workflow guard, repository rule, or application policy
  module.
- **Policy Enforcement Point.** The code path that calls the policy decision
  point before changing state. It must exist on UI, API, CLI, scheduled job,
  and admin paths.
- **Approver or Counterparty.** The separate actor who supplies the distinct
  duty. The approver may be a person, a team, a GitHub code owner, a Vault
  control group member, or another service with separate authority.
- **Audit Sink.** An append-only or restricted log that records request,
  decision, denial, approval, override, and execution. NIST AC-5 relates to
  audit protection controls including AU-9
  ([NIST SP 800-53 Rev. 5, AC-5 related controls](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf),
  verified 2026-08-02).

The relationship is simple. Business code asks to move a workflow from one
state to another. The enforcement point sends subject, duty, resource, and
workflow history to the policy decision point. The policy decision point checks
role permission and conflict rules. If the duty is allowed, state changes and an
audit event is written. If not, the system returns a denial that names the
missing duty or conflicting prior actor.

## 6. ASCII structure diagram

```text
 +----------------+        +--------------------+        +-------------+
 |    Subject     |        | Policy Enforcement |        |  Workflow   |
 | user or job    |------->| Point              |------->|  Record     |
 | roles, attrs   | duty   | UI, API, CLI, job  | state  | actors      |
 +----------------+        +----------+---------+        +------+------+ 
                                      |                         |
                                      | decision request        |
                                      v                         |
                         +------------+-------------+           |
                         | Policy Decision Point    |<----------+
                         | role allow, SoD conflict |
                         +------------+-------------+
                                      |
                                      | reads
                                      v
                +---------------------+----------------------+
                |                  Duty Catalog              |
                | duties, conflict pairs, resource scopes    |
                +---------------------+----------------------+
                                      |
                                      | records
                                      v
                         +------------+-------------+
                         |        Audit Sink        |
                         | request, allow, deny     |
                         +--------------------------+
```

The diagram separates the policy decision from the business endpoint. In small
systems both may live in one module. The boundary still matters because tests
and audits need to call the decision logic without driving the whole UI.

## 7. Dynamics

The runtime flow depends on whether the pattern is static or dynamic. Static
SoD rejects conflicting role assignments before the workflow starts. Dynamic
SoD allows the same person to hold broad roles but blocks a conflicting action
inside one workflow instance or resource scope.

```text
Requester        API            Policy PDP       Workflow        Approver
    |             |                 |                |               |
    |-- submit -->|                 |                |               |
    |             |-- can submit -->|                |               |
    |             |<-- allow -------|                |               |
    |             |-- save draft ------------------->|               |
    |             |-- audit submit ----------------->|               |
    |<-- pending -|                 |                |               |
    |             |                 |                |               |
    |             |<----------------------------- approve ----------|
    |             |-- can approve ->|                |               |
    |             |                 |-- read actors ->               |
    |             |                 |<- requester id -               |
    |             |<-- allow if approver != requester --------------|
    |             |-- mark approved ---------------->|               |
    |             |-- audit approve ---------------->|               |
    |             |                 |                |<-- done ------|
```

The central dynamic check is not "does the user have approve?" It is "does the
user have approve for this resource, and did this same user already perform a
conflicting duty on this workflow?" That second clause is the pattern.

The denial path must be explicit. A useful denial says:

- the requested duty,
- the conflicting prior duty,
- the prior actor,
- the resource scope,
- the policy version,
- whether another actor may complete the work.

Do not hide this behind a generic forbidden response for internal operators.
External APIs may need a terse response to avoid leaking workflow state, but
internal audit and support flows need the real reason.

## 8. Implementation variants

**Static mutually exclusive roles.** A directory or IAM system refuses to assign
the same subject to two conflicting roles. This works for broad conflicts such
as "audit administrator cannot also be audit log editor." It is simple to
reason about and catches errors early. It is too rigid when one person may
legitimately prepare one payment and approve a different payment.

**Dynamic actor conflict per workflow.** The system records who performed each
duty and denies a later duty by the same subject in the same workflow scope.
This fits pull requests, expense approvals, payment batches, change requests,
secret reads with approval, and deployment promotion. It needs durable workflow
state and policy checks on every transition.

**Object-scoped SoD.** The conflict is scoped to an object or domain. A person
may approve payments for cost center A after preparing payments for cost center
B, but cannot approve the same batch. This is more usable than global static
SoD, but the scope must be modeled correctly.

**N-person approval.** A request requires N approvals from allowed groups.
HashiCorp Vault Enterprise control groups support extra authorization factors
before a request can complete, including group factors and approval counts
([Vault control groups](https://developer.hashicorp.com/vault/docs/enterprise/control-groups),
verified 2026-08-02). N-person approval fits destructive or sensitive actions.
It can fail when all approvers are drawn from one compromised team.

**Dual service accounts.** One workload can write requests, another workload can
apply approved requests. This is common in CI/CD. The build job produces an
artifact and provenance. The deploy job has production authority but accepts
only artifacts that passed policy.

**Bounded delegation.** A platform owner delegates role creation but blocks the
delegate from creating roles above a boundary. AWS IAM permissions boundaries
set the maximum permissions an identity-based policy can grant, and AWS docs
describe using boundaries to delegate permission management tasks
([AWS IAM permissions boundaries](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html),
verified 2026-08-02). This is not approval by itself. It is a guard that stops
the delegated administrator from minting larger authority.

**Repository review rules.** GitHub branch protection can require approving
reviews before merge, code owner approval, and approval of the most recent
reviewable push by someone other than the person who pushed it
([GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches),
verified 2026-08-02). GitHub CODEOWNERS maps paths to owners and can require
owner approval before merge when paired with branch protection
([GitHub CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners),
verified 2026-08-02).

**Admission-time anti-escalation.** Kubernetes RBAC prevents users from
escalating privileges by editing roles or role bindings. The docs say a user can
create or update a role only if they already have the permissions in that role
or have the explicit `escalate` verb, and can create or update a role binding
only if they already hold the referenced permissions or have the explicit
`bind` verb ([Kubernetes RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/),
verified 2026-08-02). That is a separation between "can edit role objects" and
"can grant arbitrary authority."

**TypeScript example.** This small policy module models dynamic SoD for a change
request. It is idiomatic TypeScript because the duty and decision types are
closed unions.

```typescript
type Duty = "submit" | "approve" | "release";

type DutyEvent = {
  duty: Duty;
  actor: string;
};

type Change = {
  id: string;
  events: DutyEvent[];
};

type Decision =
  | { ok: true }
  | { ok: false; reason: string };

const conflicts: Record<Duty, Duty[]> = {
  submit: [],
  approve: ["submit"],
  release: ["approve"],
};

function canPerform(change: Change, actor: string, duty: Duty): Decision {
  for (const prior of change.events) {
    if (prior.actor === actor && conflicts[duty].includes(prior.duty)) {
      return {
        ok: false,
        reason: `${actor} already performed ${prior.duty} on ${change.id}`,
      };
    }
  }
  return { ok: true };
}

const change: Change = {
  id: "chg-42",
  events: [{ duty: "submit", actor: "ana" }],
};

console.log(canPerform(change, "ana", "approve"));
console.log(canPerform(change, "bo", "approve"));
```

**Python example.** This version uses ordinary data classes and raises on the
forbidden transition. It is idiomatic for service-layer tests.

```python
from dataclasses import dataclass, field


CONFLICTS = {
    "submit": set(),
    "approve": {"submit"},
    "release": {"approve"},
}


@dataclass(frozen=True)
class Event:
    duty: str
    actor: str


@dataclass
class Request:
    key: str
    events: list[Event] = field(default_factory=list)

    def perform(self, actor: str, duty: str) -> None:
        for event in self.events:
            if event.actor == actor and event.duty in CONFLICTS[duty]:
                raise PermissionError(
                    f"{actor} cannot {duty} after {event.duty} on {self.key}"
                )
        self.events.append(Event(duty=duty, actor=actor))


req = Request("pay-100")
req.perform("mira", "submit")
try:
    req.perform("mira", "approve")
except PermissionError as exc:
    print(exc)
req.perform("noor", "approve")
print([(event.duty, event.actor) for event in req.events])
```

**Go example.** This version keeps the policy pure and returns an error. It is
idiomatic Go because the workflow service can call the pure function before
writing state.

```go
package main

import (
	"errors"
	"fmt"
)

type Event struct {
	Duty  string
	Actor string
}

type Request struct {
	ID     string
	Events []Event
}

var conflicts = map[string]map[string]bool{
	"submit":  {},
	"approve": {"submit": true},
	"release": {"approve": true},
}

func CanPerform(req Request, actor string, duty string) error {
	for _, event := range req.Events {
		if event.Actor == actor && conflicts[duty][event.Duty] {
			return errors.New(actor + " already performed " + event.Duty)
		}
	}
	return nil
}

func main() {
	req := Request{
		ID:     "deploy-7",
		Events: []Event{{Duty: "approve", Actor: "lee"}},
	}
	fmt.Println(CanPerform(req, "lee", "release"))
	fmt.Println(CanPerform(req, "rai", "release"))
}
```

## 9. Known production uses

**GitHub protected branches and CODEOWNERS.** GitHub lets repository
administrators require pull request reviews before merging to a protected
branch. The docs say required reviews can come from people with write access or
from a designated code owner, and they describe an option requiring that the
most recent reviewable push be approved by someone other than the person who
pushed it ([GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches),
verified 2026-08-02). CODEOWNERS can assign owners for repository paths, and
branch protection can require approval from those owners
([GitHub CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners),
verified 2026-08-02). This is production SoD for source changes: author and
reviewer are separate duties, and path ownership narrows who may approve.

**Kubernetes RBAC.** Kubernetes RBAC has API-level anti-escalation checks for
roles and bindings. A user cannot create a role containing permissions they do
not already hold unless they have the explicit `escalate` verb, and cannot bind
a role they cannot already exercise unless they have the explicit `bind` verb
([Kubernetes RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/),
verified 2026-08-02). Kubernetes also documents running built-in controllers
with separate service accounts when `kube-controller-manager` uses
`--use-service-account-credentials`, with corresponding roles per controller
([Kubernetes RBAC, controller roles](https://kubernetes.io/docs/reference/access-authn-authz/rbac/),
verified 2026-08-02). This is production SoD for cluster administration:
editing RBAC objects and granting new authority are not the same duty.

**HashiCorp Vault Enterprise control groups.** Vault Enterprise control groups
add extra authorization factors before a request is completed. Vault returns a
limited-duration wrapping token, authorizers satisfy the configured factors,
then the token can be unwrapped to process the original request
([Vault control groups](https://developer.hashicorp.com/vault/docs/enterprise/control-groups),
verified 2026-08-02). The docs show policy examples where read or write on a
secret path is granted only after approval by members of configured identity
groups. This is production SoD for secrets access: possession of a token with a
policy is not always enough for the sensitive operation.

**AWS IAM permissions boundaries.** AWS IAM permissions boundaries set a maximum
permission set for users or roles and can be used to delegate user or role
creation while constraining what the delegate may grant
([AWS IAM permissions boundaries](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html),
verified 2026-08-02). AWS's example separates the administrator who defines the
boundary from the delegate who creates users under that boundary. This is
production SoD for identity administration: the delegate can do account work,
but cannot exceed or alter the boundary that limits the delegated work.

## 10. Consequences

Engineering judgement: the exact weight of each consequence depends on team
size, incident cost, regulatory scope, and the quality of the identity system.

Positive consequences.

- A single compromised account is less likely to complete a sensitive business
  outcome.
- Workflows produce better evidence because request, approval, release, and
  override are distinct events.
- Review responsibility moves from informal chat into enforceable policy.
- Production operations can grant narrow duties without handing one team every
  administrative power.
- Policy exceptions become visible. Each break-glass action or self-approval
  denial can be counted.
- Teams can reason about toxic permission combinations instead of reviewing
  every permission in isolation.
- Auditors and incident responders can reconstruct who did what and where the
  guard accepted or denied the action.

Negative consequences.

- Queueing delays appear wherever a second actor must approve.
- Ownership data goes stale. A path owner who left the team, an empty group, or
  a retired service account can stop valid work.
- Users may route around the control through shared accounts, out-of-band
  database edits, copied tokens, or emergency roles.
- More policy state means more test cases and more policy migration work.
- Collusion remains possible. The pattern converts solo abuse into multi-party
  abuse, not impossibility.
- Broad administrator bypass can erase the control unless admin paths are also
  governed.
- Overbroad SoD creates approval fatigue. Reviewers who see too many low-risk
  requests stop reading them.
- Privacy risk rises when audit events store detailed user behavior. The audit
  design must minimize data while keeping enough evidence for review.

## 11. Failure modes and misuse

Engineering judgement: each item below is a symptom, cause, fix triple because
the useful signal in production is observable behavior, not an abstract label.

**Symptom.** A user receives an approval request for their own change, or the
system lets them approve it.
**Cause.** The policy checks role membership but not prior actors on the same
workflow.
**Fix.** Persist actor history and add a conflict rule such as
`approver != requester` for the workflow scope.

**Symptom.** Two different accounts satisfy requester and approver, but logs
show both accounts are used from the same employee workstation and password
vault entry.
**Cause.** The system separated identities but not accountable subjects.
**Fix.** Bind duties to person identities from the identity provider, block
shared accounts, and record session provenance.

**Symptom.** Production deploys stall because every approver group contains
former employees or people in another time zone.
**Cause.** Ownership and group membership are stale.
**Fix.** Add group health checks, owner expiry, on-call fallback, and dashboards
for pending approval age.

**Symptom.** High-risk requests pass review in seconds with identical approval
comments.
**Cause.** Approval fatigue or rubber stamping.
**Fix.** Move low-risk requests to automated checks, keep human review for
high-risk deltas, and require structured evidence for approval.

**Symptom.** A break-glass role becomes the normal way to do release work.
**Cause.** The normal SoD path is too slow or broken, and emergency use has no
expiry or review.
**Fix.** Time-box emergency grants, require ticket links, record sessions, alert
on use, and hold weekly post-event review until the normal path is repaired.

**Symptom.** A database administrator can delete or rewrite the approval table
after approving a payment.
**Cause.** The audit and workflow stores share the same administrative duty as
the action being controlled.
**Fix.** Split workflow administration, audit administration, and business
approval. Use append-only storage or restricted audit write paths.

**Symptom.** A service account both creates infrastructure and grants itself the
runtime role it wants.
**Cause.** Provisioning and runtime duties are collapsed into one broad
automation identity.
**Fix.** Split build, provision, and operate identities. Use boundaries or
admission checks so automation cannot mint new authority outside policy.

**Symptom.** Users can bypass the UI approval flow by calling an internal API or
running a CLI command.
**Cause.** The SoD check lives only in the UI.
**Fix.** Move enforcement to the command handler, API boundary, database
transition, or policy middleware used by every entry point.

**Symptom.** The policy works for one application, but a linked downstream
system accepts the same actor for the conflicting duty.
**Cause.** The conflict spans application domains, but the policy is local.
**Fix.** Include cross-system actors in the workflow record, or use a shared
decision service for the business process.

**Symptom.** A role admin creates a new role with forbidden permissions, then
binds it to themselves.
**Cause.** Role editing and role binding are not separated, or escalation verbs
are too broad.
**Fix.** Require that role creators already hold granted permissions or have an
explicit escalation authority, mirroring the Kubernetes RBAC anti-escalation
model ([Kubernetes RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/),
verified 2026-08-02).

## 12. Trade-off matrix

| Force | Separation of Duties | Least Privilege | Dual Authorization | ABAC | Immutable Audit Log |
|---|---|---|---|---|---|
| Main goal | Split conflicting duties across subjects | Minimize each subject's authority | Require multiple approvals for one action | Evaluate attributes at request time | Preserve evidence after action |
| Fraud resistance | Strong against solo misuse, weak against collusion | Limits damage by one subject | Strong for selected actions | Depends on policy attributes | Detects after the fact |
| Latency | Medium to high when humans approve | Low after policy is tuned | High for guarded actions | Low to medium | Low on request path |
| Coupling | Coupled to workflow history and identity | Coupled to resource permissions | Coupled to approval workflow | Coupled to attribute sources | Coupled to log pipeline |
| Consistency | High with shared PDP | High with reusable roles | Medium, often action-specific | High if attributes are governed | High for evidence, not prevention |
| Operability | Good when denials name conflicts | Good when policy simulation exists | Can create queues | Debugging can be hard | Good for investigation |
| Team fit | Good for regulated and platform teams | Good for all teams | Good for rare high-risk work | Good for large variable policy sets | Good where proof matters |
| Main cost | Queueing and stale ownership | Policy discovery and tuning | Approver availability | Attribute quality | Storage, access, privacy review |
| Failure pattern | Rubber stamp or bypass path | Overbroad wildcard grants | Approval fatigue | Conflicting attributes | Logs exist but no one reviews |

These alternatives are not mutually exclusive. A mature production system often
uses Least Privilege to narrow each duty, SoD to split conflicting duties, ABAC
to scope the decision, dual authorization for rare destructive actions, and
immutable audit logs to preserve evidence.

## 13. Related and incompatible patterns

**Least Privilege** composes with Separation of Duties. Least Privilege asks how
small each role can be. Separation of Duties asks which small roles cannot be
combined in one subject or one workflow instance.

**Role-Based Access Control** is a common implementation carrier. RBAC maps job
functions to roles and permissions; SoD adds conflict constraints over those
roles or over duty execution. NIST's RBAC project describes RBAC as reducing the
cost of security administration and handling complexities from mutually
exclusive roles or role hierarchies through RBAC software
([NIST RBAC project](https://csrc.nist.gov/projects/role-based-access-control),
verified 2026-08-02).

**Attribute-Based Access Control** can replace coarse static SoD when the rule
depends on resource, tenant, amount, geography, time, device, or workflow
state. ABAC is more expressive but harder to explain to reviewers.

**Complete Mediation** supports this pattern. Every entry point must consult
the policy decision point. If one batch job, CLI command, or admin route skips
the check, SoD becomes a UI convention.

**Defense in Depth** contains SoD as one layer. SoD should sit beside policy
boundaries, status checks, audit logs, signed artifacts, backup controls, and
monitoring.

**Zero Trust** aligns with SoD when each request is evaluated using identity,
resource, and context rather than network location. Zero Trust does not create
conflict rules by itself.

**Immutable Audit Log** is related but different. Audit records help detect and
investigate misuse. SoD blocks selected misuse before completion.

Incompatible patterns and practices.

- **Shared Administrator Account.** It erases the accountable subject.
- **Self-Approval.** It is the exact conflict the pattern exists to block.
- **Break-Glass Without Review.** Emergency access may be needed, but lack of
  expiry and post-event review turns emergency authority into ordinary bypass.
- **Ambient Authority.** If every process inherits broad authority from its
  environment, duties cannot be split at the action level.
- **Policy Hidden in UI Widgets.** UI-only guards conflict with Complete
  Mediation and fail as soon as another path exists.

## 14. Refactoring path in and out

Engineering judgement: introduce this pattern by isolating one high-risk
workflow. Do not begin with an enterprise role redesign unless the current
system already has clean identity, ownership, and audit data.

Refactoring in.

1. Pick one irreversible or high-value action: merge to main, release to
   production, approve payment, rotate key, grant admin, delete audit data, or
   export customer records.
2. Name the duties in business language. Example: `invoice.create`,
   `invoice.approve`, `payment.release`.
3. Identify toxic combinations. Example: creator cannot approve the same
   invoice, approver cannot release their own approval, audit admin cannot
   delete audit entries for their own actions.
4. Add actor history to the workflow record. Store subject id, duty, resource
   scope, timestamp, policy version, and decision id.
5. Extract authorization logic into a policy decision function or service.
   Cross reference Extract Function and Extract Class from the refactoring
   family when moving conditionals out of command handlers.
6. Place enforcement at the state transition, not the button. The command must
   fail if called from UI, API, CLI, job, or support console.
7. Write denial tests before rollout. Include self-approval, second actor
   approval, stale approval after content change, admin bypass, and duplicate
   approval.
8. Roll out in report-only mode if the blast radius is high. Compare what would
   have been denied with real operations.
9. Turn on enforcement for the smallest scope that pays for the work.
10. Add observability for denial count, pending age, override use, and missing
    owner.

Refactoring out.

1. Confirm the protected action still has material risk. If the action became
   reversible, low value, automated, or obsolete, SoD may be excess process.
2. Measure queue time, denial quality, rubber-stamp rate, and incident value.
3. Replace human approval with automated policy where the reviewer only checks
   facts a machine can check.
4. Merge roles only when the merged role cannot complete a sensitive outcome
   alone, or when a compensating control such as delayed execution and immutable
   audit covers the risk.
5. Delete unused duties from the catalog and migrate old workflow records to a
   read-only historical policy version.
6. Keep the audit trail for past decisions according to retention policy.

Refactoring warning: deleting SoD is often more sensitive than adding it. A
removal changes who can complete outcomes alone. Treat the policy migration as
a security change with review by the owners of the protected resource.

## 15. Testing and verification

Engineering judgement: test the policy as a pure decision first, then test each
entry point that can trigger the guarded transition.

Unit tests should cover:

- A requester cannot approve the same resource.
- A different actor with the correct role can approve.
- An actor without the role cannot approve even when they are different from the
  requester.
- A user who prepared resource A may approve resource B if the policy is
  object-scoped.
- A stale approval is invalid after the content being approved changes.
- A break-glass actor can act only inside the time box and emits the required
  audit event.
- A policy migration keeps old workflow records interpretable under their
  original policy version.
- Empty approver groups fail closed with an operator-visible error.

Integration tests should cover each path that reaches the transition: web UI,
public API, admin API, CLI, scheduled job, webhook, migration script, and
support console. The common bug is a correct UI check and a missing internal
API check.

Property tests fit well. Generate workflow histories with random actors,
duties, and resource scopes, then assert that no actor can complete a forbidden
combination inside the same scope. This catches mistakes such as comparing user
display names instead of stable subject ids.

Policy simulation is useful before enforcement. Run real historical events
through the new policy and count would-deny cases. Each would-deny case needs a
classification: true misuse, old process that must change, missing data, or
policy bug.

Test doubles should be boring. Use a fake identity provider with stable subject
ids, groups, and attributes. Use a fake clock for expiry. Use an in-memory
workflow store for unit tests and a real database transaction in integration
tests to catch race conditions.

Concurrency tests matter. Two approvers may act at the same time, or one actor
may approve while another changes the request body. Guard the transition with
an optimistic version, row lock, compare-and-swap, or workflow engine token so
the approved object is the same object that was reviewed.

Verification of the code samples for this entry was run with `node`,
`python3`, and `go run` on 2026-08-20 in the repository environment.

## 16. Observability signals

Engineering judgement: observability should show whether the control is active,
usable, and resisting bypass. A dashboard that only counts approvals is not
enough.

Log one structured event for each policy decision:

- `decision_id`
- `policy_version`
- `subject_id`
- `subject_type`
- `duty`
- `resource_type`
- `resource_id`
- `workflow_id`
- `prior_conflicting_duty`
- `prior_actor_id`
- `decision`, with values such as allow, deny, pending, expired, override
- `reason_code`
- `entry_point`, such as ui, api, cli, job, support
- `request_hash` or content version for reviewed material

Trace attributes should include the policy decision id and the workflow id so
an incident responder can connect the application request to the policy event.
Avoid putting secret values, customer content, or raw policy documents in
traces.

Healthy signals:

- Most protected actions have a matching request event and approval event.
- Denials are low but nonzero after rollout.
- Pending approval age stays within the team's operating target.
- Approver groups have active members.
- Break-glass use is rare and reviewed within the promised time.
- UI, API, CLI, and jobs produce policy decision events with the same reason
  codes.
- Approved content hash matches released content hash.

Failing signals:

- Zero denials across high-risk workflows, which may mean the policy is not
  being called.
- Sudden spike in self-approval denials after a product change, which may mean a
  route bypassed the normal requester field.
- High approval count from one person across unrelated domains.
- Many requests expiring due to missing owners.
- Break-glass use rising week over week.
- Policy decisions missing from CLI or support-console traffic.
- Audit write failures following deny or override decisions.

Alerts should be sparse and sharp: self-approval allowed, policy service
unavailable on a protected transition, break-glass grant created, approver group
empty, audit sink write failed, or content changed after approval.

## 17. Security and privacy implications

Engineering judgement: the pattern closes solo authority paths but opens
workflow, identity, and audit surfaces that need their own controls.

Security benefits:

- A stolen requester credential cannot complete the whole protected workflow
  unless the attacker also compromises an eligible approver.
- A malicious administrator has fewer paths to create authority and use it in
  one motion when role creation and role binding are separated.
- A build or deploy compromise is easier to contain when artifact production and
  production release run under different identities.
- Audit data is more trustworthy when audit administration is separated from the
  duties being audited.

Security risks:

- Approver accounts become higher-value targets. Protect them with MFA,
  phishing-resistant authentication where warranted, device posture, and short
  sessions.
- Notification channels can become approval channels by accident. A compromised
  chat integration must not be able to approve unless the risk decision accepts
  that channel as an identity proof.
- Group compromise defeats the pattern. If every approver is in one broad admin
  group, the attacker attacks that group.
- Policy data becomes sensitive. The duty catalog reveals which actions are
  high value and which groups can approve them.
- Race conditions can release content that differs from what was approved.
- Service accounts may collapse duties if automation identities are too broad.

Privacy implications:

- Workflow records contain behavior data about employees, contractors, and
  sometimes customers. Store the minimum actor and decision data needed for
  accountability and retention.
- Do not expose prior actor names to users who lack a need to see them. A public
  API can return "approval required by another authorized actor" while internal
  audit sees the exact conflict.
- Retention must be tied to audit need. Keeping every approval forever may
  create avoidable privacy and discovery risk.
- Reports should aggregate where possible. A manager may need queue health by
  team, while an investigator needs subject-level history for a specific case.

The pattern is silent on encryption, transport security, input validation, and
secure storage. Those controls still belong elsewhere. Separation of Duties
only answers who may perform conflicting duties and how the system proves it.

## 18. References

- Joint Task Force, *Security and Privacy Controls for Information Systems and
  Organizations*, NIST Special Publication 800-53 Revision 5, September 2020,
  control AC-5 and related controls, https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf,
  verified 2026-08-02.
- David D. Clark and David R. Wilson, "A Comparison of Commercial and Military
  Computer Security Policies," IEEE Symposium on Security and Privacy 1987,
  pages 184-195, DOI 10.1109/SP.1987.10001, bibliographic record at
  https://dblp.org/rec/conf/sp/ClarkW87, verified 2026-08-02.
- National Institute of Standards and Technology, "Role Based Access Control
  RBAC," project page, https://csrc.nist.gov/projects/role-based-access-control,
  verified 2026-08-02.
- GitHub Docs, "About protected branches,"
  https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches,
  verified 2026-08-02.
- GitHub Docs, "About code owners,"
  https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners,
  verified 2026-08-02.
- Kubernetes Documentation, "Using RBAC Authorization,"
  https://kubernetes.io/docs/reference/access-authn-authz/rbac/,
  verified 2026-08-02.
- HashiCorp Developer, "Use control groups for authorization,"
  https://developer.hashicorp.com/vault/docs/enterprise/control-groups,
  verified 2026-08-02.
- AWS Identity and Access Management User Guide, "Permissions boundaries for IAM
  entities,"
  https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html,
  verified 2026-08-02.
