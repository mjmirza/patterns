---
name: Least Privilege
slug: least-privilege
family: 15-security
category: Security
aliases: [Principle of Least Privilege, POLP, Least Authority, Minimum Necessary Access]
first_described: "Saltzer and Schroeder 1975"
maturity: canonical
related: [zero-trust, role-based-access-control, capability-based-security, privilege-separation, defense-in-depth, secrets-management]
incompatible_with: [ambient-authority, shared-administrator-account, wildcard-permission]
verified: 2026-08-02
---

# Least Privilege

## 1. Name, aliases, and lineage

The canonical name is Least Privilege. Security, operating-system, cloud, and
identity teams also call it the Principle of Least Privilege, POLP, least
authority, or minimum necessary access. This entry uses Least Privilege because
that is the NIST glossary term and the wording used by Saltzer and Schroeder in
their protection design principles ([NIST CSRC glossary, least privilege](https://csrc.nist.gov/glossary/term/least_privilege),
verified 2026-08-02; [Saltzer and Schroeder, "The Protection of Information in
Computer Systems"](https://www.cs.virginia.edu/~evans/cs551/saltzer/),
verified 2026-08-02).

The lineage is canonical security engineering rather than object-oriented
catalog history. Jerome H. Saltzer and Michael D. Schroeder presented Least
Privilege as one of eight design principles in their 1975 *Proceedings of the
IEEE* paper, "The Protection of Information in Computer Systems." The paper
describes the principle as programs and users operating with the smallest set
of privileges needed for the job, with the goal of limiting damage from errors
and narrowing the audit set when misuse is suspected ([Saltzer and Schroeder](https://www.cs.virginia.edu/~evans/cs551/saltzer/),
verified 2026-08-02).

NIST's glossary gives the modern standards form: a system restricts user, or
process-on-user, privileges to the minimum needed for assigned tasks, and a
security architecture grants each entity the minimum authorizations and system
resources needed for its function ([NIST CSRC glossary, least privilege](https://csrc.nist.gov/glossary/term/least_privilege),
verified 2026-08-02). NIST SP 800-207 places access decisions in the zero
trust frame by saying that no implicit trust is granted from network location
or asset ownership, and that authentication and authorization happen before a
session to an enterprise resource is established ([NIST SP 800-207](https://csrc.nist.gov/pubs/sp/800/207/final),
verified 2026-08-02).

The term is sometimes stretched until it means "make access safer." That is too
soft. Least Privilege is a design pattern for shrinking authority at the point
where work is done. It asks: what exact subject performs this exact operation
on this exact resource under this exact condition, and what authority can be
removed without breaking that operation?

## 2. Problem and context

A system needs trusted actions to happen, but the code, user, service account,
container, or job that performs those actions can also fail, be tricked, or be
taken over. The common failure is not that access control is absent. The common
failure is that access is wider than the operation needs. A report service has
write access because read-only setup took more time. A batch job can delete
every bucket because the first policy used `*`. A Kubernetes controller can
read all Secrets because a cluster-level binding was faster than a namespace
RoleBinding. A human administrator uses one broad role for daily work because
role switching feels annoying.

The pattern fits wherever a subject crosses a trust boundary. The subject can
be human, workload, process, thread, plug-in, function, build job, token, SSH
session, database role, browser extension, or mobile app. The protected object
can be a file, table, key, socket, device, API method, cluster resource, cloud
resource, or user record. The action can be read, write, execute, list,
impersonate, decrypt, sign, deploy, attach policy, create workload, or assume
role.

The context has three parts.

- There is a policy enforcement point that can distinguish subjects, actions,
  resources, and conditions.
- The team can learn what authority the work requires, either from design,
  tests, logs, policy simulation, or controlled rollout.
- The cost of a failed or captured subject is high enough that the added
  policy work pays for itself.

Least Privilege is not a one-time hardening pass. It is a lifecycle. Access is
granted, used, observed, reduced, expired, and reviewed. Cloud providers now
ship tools around that loop. AWS IAM recommends granting only permissions
needed for a task and describes Access Analyzer features that validate
policies, generate policies from CloudTrail activity, and expose last-accessed
information ([AWS IAM policies and permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html),
verified 2026-08-02). Google Cloud IAM recommends limited predefined or custom
roles, separate service accounts for components with different permissions, and
smallest-scope role grants ([Google Cloud, Use IAM securely](https://docs.cloud.google.com/iam/docs/using-iam-securely?authuser=01&hl=en),
verified 2026-08-02).

The pattern is also an admission that defects remain. Engineering judgement:
Least Privilege does not promise that a service cannot be compromised. It
changes the shape of the incident. A compromised image resizer with one input
bucket and one output bucket is a different incident from a compromised worker
that can read every bucket, mint tokens, and alter audit policy.

## 3. Forces

Engineering judgement: this dimension weighs operational pressures. The
citations name known mechanisms; the trade-offs are design reasoning.

- **Blast radius.** Favoured. Less authority means fewer objects and actions
  are reachable after a mistake, confused deputy attack, stolen token, or code
  execution bug.
- **Delivery speed.** Sacrificed at first. A broad role is faster to attach
  than a narrow role. The pattern moves work from incident response into policy
  design, tests, and rollout.
- **Availability.** Mixed. Narrow access can block valid work when the policy
  misses an action. Broad access avoids permission errors, but it hides
  privilege mistakes until damage occurs.
- **Latency.** Usually close to neutral. Most authorization checks already sit
  on the request path. Dynamic privilege elevation, token exchange, or policy
  decision calls can add latency if placed in a hot loop.
- **Coupling.** Mixed. Code becomes less coupled to broad administrator
  accounts and more coupled to named actions, resource names, and policy
  conditions. That coupling is visible and reviewable.
- **Consistency.** Favoured when policies are generated from reusable roles or
  modules. Sacrificed when every team hand-writes slightly different narrow
  grants.
- **Operability.** Favoured if decisions emit logs and access denials are clear.
  Sacrificed if operators see only a generic 403 without subject, action,
  resource, and matched policy.
- **Cost.** Sacrificed through identity inventory, policy reviews, tooling, and
  occasional break-fix work. Favoured when reduced access prevents broad data
  exposure or destructive recovery.
- **Team topology.** Favoured when platform teams provide policy templates and
  application teams own their workload permissions. Sacrificed when central
  security review becomes a blocking queue for every small access change.
- **Cognitive load.** Sacrificed. Developers must learn the authorization model,
  inherited grants, implicit actions, and escalation paths. Kubernetes warns
  that workload creation in a namespace can imply access to mounted Secrets and
  other resources, which is not obvious from a single verb grant ([Kubernetes
  RBAC good practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/),
  verified 2026-08-02).

The force the pattern favours most is containment. The force it sacrifices most
often is convenience.

## 4. Applicability and non-applicability

Reach for Least Privilege when these conditions hold.

- **Human daily administration uses a broad account.** Split daily read,
  support, deploy, billing, and emergency powers. Keep high-risk powers
  time-bound and auditable.
- **A workload has wildcard or administrator rights.** Replace `*` actions and
  account-wide resources with named API actions, resources, and conditions.
- **A service has different internal tasks with different rights.** Give each
  task its own principal or token. Google Cloud IAM recommends separate service
  accounts for application components that require different permissions
  ([Google Cloud, Use IAM securely](https://docs.cloud.google.com/iam/docs/using-iam-securely?authuser=01&hl=en),
  verified 2026-08-02).
- **A plug-in, extension, script, or user-supplied job runs inside a trusted
  host.** Run the extension with a narrowed capability object, sandbox profile,
  worker role, or subprocess domain.
- **A system supports inherited scopes.** Grant at the smallest resource scope
  that still covers the work. Google Cloud notes that allow policies on child
  resources inherit from parents, and recommends granting roles at the smallest
  needed scope ([Google Cloud, Use IAM securely](https://docs.cloud.google.com/iam/docs/using-iam-securely?authuser=01&hl=en),
  verified 2026-08-02).
- **Permission usage can be observed.** AWS IAM Access Analyzer can use
  CloudTrail activity to generate a policy template, and IAM exposes
  last-accessed information for refinement ([AWS IAM policies and permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html),
  verified 2026-08-02).
- **The protected action has a high abuse cost.** Examples include deleting
  data, changing policy, reading secrets, signing artifacts, creating workloads,
  assuming identities, changing network routes, and decrypting records.

Non-applicability list.

- **The system cannot enforce separate permissions.** If the runtime sees only
  one shared account and no resource-level authorization, Least Privilege cannot
  be applied inside that boundary. First add a policy enforcement point or
  split the boundary.
- **The operation is an indivisible platform primitive.** If an API grants
  `manage_database` and offers no narrower read, write, or schema verbs, a
  narrow business policy cannot be represented. Use compensating controls such
  as approval, audit, sandboxing, or an intermediate service.
- **Emergency response would be slowed by missing break-glass access.** Do not
  remove emergency power. Make it rare, time-bound, logged, reviewed, and
  protected by stronger authentication.
- **The policy churn exceeds the risk.** Engineering judgement: for a throwaway
  local prototype with no sensitive data, fine-grained IAM may cost more than
  the work. Use a separate account or machine instead of pretending the
  prototype is hardened.
- **Permissions are still unknown during discovery.** Start with a bounded
  exploratory role in an isolated environment, record used actions, then reduce
  before production. AWS describes this staged move from managed policies
  toward reduced customer policies after an observation period ([AWS, Prepare
  for least-privilege permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/getting-started-reduce-permissions.html),
  verified 2026-08-02).
- **A narrow grant would create hidden privilege through another path.** A user
  who can create pods that run as a privileged service account may gain that
  service account's API access. Kubernetes documents that workload creation can
  imply access to other namespace resources and service account powers
  ([Kubernetes RBAC good practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/),
  verified 2026-08-02).
- **The real need is separation of privilege.** If two independent approvals
  must be present, use Separation of Privilege or two-person control. Least
  Privilege shrinks one subject's authority; it does not require two subjects.
- **The real need is data minimization.** Least Privilege controls who can act.
  It does not by itself decide whether the data should exist, how long it
  should be kept, or which fields should be collected.

## 5. Structure

Least Privilege has six participants.

- **Subject.** The entity asking to act. It may be a user, process, workload,
  service account, token, role session, function, container, or build job.
- **Task.** The bounded unit of work the subject is meant to perform. A task
  should be named in business terms, such as "publish invoice event" or
  "render thumbnail", before it is translated into API actions.
- **Resource.** The object or collection acted on: file, table, bucket, topic,
  namespace, key, route, user record, secret, device, or endpoint.
- **Privilege set.** The exact actions and resources the subject may use. It
  can be an ACL entry, IAM policy, RBAC Role, Linux capability set, database
  grant, object capability, or sandbox profile.
- **Policy decision point.** The logic that decides whether a request is
  allowed. It may be embedded in the database, API server, kernel, service
  mesh, cloud control plane, or application.
- **Policy enforcement point.** The component that stops or permits the action
  at runtime. In many systems the decision and enforcement point live together;
  the split still helps design review.
- **Observer.** Logs, traces, audit records, analyzers, and dashboards that show
  which privileges were used, unused, denied, or escalated.

The key relationship is that a subject should receive authority through a task
role, not through organizational status. "Backend service" is too broad.
"Invoice event publisher for tenant A" is reviewable. "Developer" is too broad.
"Read staging logs for service X until Friday" is reviewable.

The pattern is strongest when the task boundary is stable. If a task keeps
growing until it includes every operation in a subsystem, the role becomes an
administrator role under a nicer name.

## 6. ASCII structure diagram

```text
      +================+        request         +====================+
      |    Subject     | ....................> | Enforcement Point  |
      | user, process  |                        | API, kernel, DB    |
      +================+                        +==========+=========+
              |                                           |
              | holds                                     | asks
              v                                           v
      +================+    compares task,      +====================+
      | Privilege Set  |    action, resource    | Decision Point     |
      | role, token,   | <....................> | policy engine      |
      | ACL, capability|                        +==========+=========+
      +================+                                   |
              ^                                           |
              | scoped to                                 | emits
              |                                           v
      +================+                         +===================+
      |      Task      |                         | Observer          |
      | bounded work   |                         | audit, metrics    |
      +========+=======+                         +===================+
               |
               | acts on
               v
      +================+
      |    Resource    |
      | file, API, key |
      +================+
```

## 7. Dynamics

The runtime flow starts before the request. A role or capability is issued for a
known task. The subject calls the resource through an enforcement point. The
decision point evaluates subject, action, resource, and conditions. The
observer records both allowed and denied decisions so the role can later be
reduced or corrected.

```text
Issuer        Subject       Enforcement       Decision       Resource      Observer
  |              |                |               |              |             |
  |== grant task role =========>|               |              |             |
  |              |                |               |              |             |
  |              |== action ====>|               |              |             |
  |              |                |== authorize =>|              |             |
  |              |                |<== allow =====|              |             |
  |              |                |== perform ==================>|             |
  |              |                |<== result ===================|             |
  |              |                |== audit allow ===========================>|
  |              |                |               |              |             |
  |              |== extra action|               |              |             |
  |              |==============>|               |              |             |
  |              |                |== authorize =>|              |             |
  |              |                |<== deny ======|              |             |
  |              |<== 403 =======|               |              |             |
  |              |                |== audit deny ============================>|
```

A healthy loop does not stop at deny. The team reads the denial. If the action
belongs to the task, the policy is corrected with a focused grant. If the
action is drift, dead code, probing, or a confused deputy path, the denial is
kept and the caller is fixed.

For time-bound elevation, the flow has two extra events. The subject requests a
higher role with a reason, and the issuer later revokes it automatically. NIST
SP 800-207's zero trust framing fits that model because authorization is not
implicit from network location or asset ownership before a resource session
([NIST SP 800-207](https://csrc.nist.gov/pubs/sp/800/207/final), verified
2026-08-02).

## 8. Implementation variants

**Role-based access control.** Users or workloads receive roles, and roles hold
permissions. Kubernetes RBAC uses Roles and RoleBindings for namespace-scoped
grants and ClusterRoles and ClusterRoleBindings for cluster-scoped grants; its
good-practices guide recommends namespace-level grants where possible and
warns against wildcard permissions ([Kubernetes RBAC good practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/),
verified 2026-08-02). RBAC reads well for humans and auditors. It can become
coarse when roles are built around job titles rather than tasks.

**Attribute-based or condition-based access control.** Policies include facts
such as tenant, environment, device posture, time, network, resource tag, or
request path. AWS IAM conditions can restrict when a statement applies, such as
requiring TLS or access through a specific service path ([AWS IAM policies and
permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html),
verified 2026-08-02). Conditions reduce role count, but they raise testing
burden because a grant may change with context.

**Capability-based authority.** The caller receives an unforgeable reference
that carries the authority to use an object. Saltzer and Schroeder define a
capability as an unforgeable ticket proving authority for a named object
([Saltzer and Schroeder](https://www.cs.virginia.edu/~evans/cs551/saltzer/),
verified 2026-08-02). In application code, a capability may be a narrow
interface or closure. The caller cannot perform actions absent from the object
it was handed.

**Operating-system privilege splitting.** Linux capabilities divide traditional
superuser power into per-thread units and file capability sets. The manual page
states that the goal is to divide superuser power so compromise of a program
with one or more capabilities causes less damage than compromise of the same
program running as root ([Linux capabilities(7)](https://man7.org/linux/man-pages/man7/capabilities.7.html),
verified 2026-08-02). This variant is powerful for daemons, containers, and
system tools. It is hard to review when broad capabilities such as
`CAP_SYS_ADMIN` appear.

**Privilege separation.** A small privileged parent keeps dangerous authority,
while a larger unprivileged child handles untrusted input. Provos, Friedl, and
Honeyman describe this design for OpenSSH: an unprivileged child asks a
privileged parent to perform privileged operations, and compromise of the child
does not give control of the parent ([Provos, Friedl, Honeyman, "Preventing
Privilege Escalation"](https://www.usenix.org/legacy/event/sec03/tech/full_papers/provos_et_al/provos_et_al_html/),
verified 2026-08-02). This variant pays IPC and protocol cost to shrink the
trusted computing base.

**Time-bound privilege elevation.** The subject starts with low authority and
requests a temporary grant for a narrow operation. Google Cloud recommends
conditional role bindings that can expire and temporary higher access in its
IAM guidance ([Google Cloud, Use IAM securely](https://docs.cloud.google.com/iam/docs/using-iam-securely?authuser=01&hl=en),
verified 2026-08-02). This works for rare administration tasks. It requires
good approval UX or users will seek standing broad access.

**Generated least-privilege policies.** The system observes prior activity and
proposes a narrower policy. AWS IAM Access Analyzer can generate a policy
template from CloudTrail activity for a user or role over a selected time range
([AWS IAM Access Analyzer policy generation](https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-policy-generation.html),
verified 2026-08-02). Google Cloud role recommendations help apply the
principle by finding permissions a principal actually needs ([Google Cloud,
review and apply role recommendations](https://docs.cloud.google.com/policy-intelligence/docs/review-apply-role-recommendations),
verified 2026-08-02). Generated policies are a starting point, not proof,
because observation windows miss rare but valid paths.

## 9. Known production uses

**AWS Identity and Access Management.** AWS IAM documentation names least
privilege as policy advice: grant only the permissions required for a task,
start with minimum permissions, use conditions, validate policies with IAM
Access Analyzer, generate policies from CloudTrail activity, and use
last-accessed information to refine grants ([AWS IAM policies and permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html),
verified 2026-08-02). AWS also tells users to move from broad AWS managed
policies toward reduced customer policies after an observation period ([AWS,
Prepare for least-privilege permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/getting-started-reduce-permissions.html),
verified 2026-08-02).

**Kubernetes RBAC.** Kubernetes documents RBAC as a security control for making
cluster users and workloads have only the access required for their roles. Its
least-privilege guidance recommends minimal RBAC rights, namespace RoleBindings
where possible, avoiding wildcard permissions, limiting `cluster-admin`, and
avoiding the `system:masters` group because that group bypasses RBAC checks
([Kubernetes RBAC good practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/),
verified 2026-08-02).

**Google Cloud IAM.** Google Cloud IAM guidance says that in production
environments basic roles should not be granted unless no alternative exists,
and recommends limited predefined or custom roles, separate service accounts
for components with different permissions, smallest-scope grants, and caution
around service-account impersonation ([Google Cloud, Use IAM securely](https://docs.cloud.google.com/iam/docs/using-iam-securely?authuser=01&hl=en),
verified 2026-08-02). Google Cloud Policy Intelligence documents role
recommendations that help principals have only permissions they need ([Google
Cloud, review and apply role recommendations](https://docs.cloud.google.com/policy-intelligence/docs/review-apply-role-recommendations),
verified 2026-08-02).

**Linux capabilities.** Linux implements capabilities as a way to split
traditional root power into units that can be independently enabled and
disabled per thread. The manual page lists capability sets, file capabilities,
and the goal of reducing damage when a capable program is compromised
([Linux capabilities(7)](https://man7.org/linux/man-pages/man7/capabilities.7.html),
verified 2026-08-02).

**OpenSSH privilege separation.** Provos, Friedl, and Honeyman present OpenSSH
as a service whose privileges can be separated, with an unprivileged child
asking a privileged parent to perform restricted operations. The paper reports
that the design confines an adversary who controls the child to that protection
domain ([Provos, Friedl, Honeyman](https://www.usenix.org/legacy/event/sec03/tech/full_papers/provos_et_al/provos_et_al_html/),
verified 2026-08-02).

## 10. Consequences

Engineering judgement: these consequences follow from applying the pattern in
production systems. The cited systems show common mechanisms, but the weight of
each cost depends on the organization.

Positive consequences.

- Compromise has a smaller blast radius. A stolen token can do what the token
  permits, not everything the platform can do.
- Audit scope shrinks. When a dangerous action occurs, fewer subjects have the
  matching right.
- Configuration drift becomes visible. Unused roles, wildcard permissions, and
  broad parent-scope grants can be found and removed.
- Sensitive data paths become clearer. Access to Secrets, keys, logs, exports,
  and production data must be named.
- Delegation becomes safer. Teams can own deployment, support, or operations
  tasks without receiving unrelated powers.
- Incident response improves. Operators can revoke a narrow role without
  disabling every workload that shares an administrator account.
- Design discussions become concrete. "Can this service write invoices?" is a
  better review question than "Is this service trusted?"

Negative consequences.

- Initial delivery slows when permissions are unknown.
- Access-denied errors can interrupt valid work if rollout lacks simulation,
  shadow logging, or fast correction.
- Policy count grows. Fine-grained roles, custom policies, service accounts,
  and conditions need ownership.
- Debugging can become indirect. The code path may be correct while the policy
  path is wrong.
- Hidden transitive authority remains hard. Impersonation, workload creation,
  token mounting, and inherited parent grants can defeat a narrow-looking role.
- Emergency work needs a separate path. Removing all broad access without a
  break-glass design creates operational risk.
- Teams may create "temporary" broad roles that never expire if the approved
  path is painful.

The main consequence is cultural. Least Privilege turns access from a setup
detail into part of the program's contract.

## 11. Failure modes and misuse

Engineering judgement: each item below is written as an observable production
triple.

**Production-only denials.** Symptom: a workload receives 403 errors only in
production. Cause: the policy was reduced from staging traffic and missed a
production-only action or resource. Fix: add policy simulation, replay
production audit logs in a test account, then grant the exact missing action.

**Cross-tenant read.** Symptom: a token stolen from one service can read
unrelated tenant data. Cause: the role is scoped to account or project rather
than tenant, bucket prefix, table row policy, or resource tag. Fix: add
resource scoping or split the service principal by tenant class and data
domain.

**Wildcard creep.** Symptom: every denial is fixed by adding another wildcard.
Cause: the team treats permissions as support tickets, not as a task model.
Fix: name the task, list required actions, and reject fixes that do not map to
the task.

**Secret extraction through workload creation.** Symptom: a user with no Secret
read role still extracts secrets. Cause: the user can create workloads that
mount service accounts or volumes with broader rights. Fix: treat workload
creation as privilege-bearing. Separate namespaces, restrict service account
use, and apply pod security controls.

**Read role with write effects.** Symptom: a read-only support role changes
system state. Cause: the platform has read actions that trigger exports, jobs,
caches, or side effects. Fix: classify actions by observed effect, not by API
name, and move side effects behind write permissions.

**Routine break-glass use.** Symptom: a break-glass account is used for routine
work. Cause: daily roles are too weak or higher-access approval is too slow.
Fix: build a fast time-bound approval path, alert on break-glass use, and
review each session.

**Custom role sprawl.** Symptom: custom roles multiply until nobody can review
them. Cause: each team hand-writes one-off roles with overlapping permissions.
Fix: create role templates by task, add ownership metadata, and retire roles
with no recent use.

**Pipeline overreach.** Symptom: a CI job can alter production infrastructure.
Cause: build, test, release, and deploy steps share one credential. Fix: split
pipeline identities by stage and require promotion identity for production
changes.

**No emergency path.** Symptom: an admin loses access during an incident. Cause:
Least Privilege was applied without an emergency model. Fix: add protected
emergency identities, hardware-backed authentication, session recording, and
automatic expiry.

**Opaque denials.** Symptom: denial logs contain no useful fields. Cause: the
enforcement point logs only status code or route. Fix: log subject, action,
resource, decision, matched policy id, and correlation id.

**Hidden inheritance.** Symptom: a narrow role later becomes broad without
review. Cause: inherited parent-scope grants or group membership changed
outside the role file. Fix: audit effective permissions, not only direct policy
documents.

**Local data copies.** Symptom: developers copy production data to local
machines for debugging. Cause: runtime roles are narrow, but data export policy
is broad or informal. Fix: add controlled support queries, redaction, approval,
and short-lived data access grants.

Misuse often comes from confusing Least Privilege with low privilege. A subject
with low privilege that cannot perform its task is broken. A subject with high
privilege for one narrow, approved task may still follow the pattern if the
grant is scoped, observed, and removed when the task ends.

## 12. Trade-off matrix

**Blast radius.** Least Privilege shrinks authority on each subject. Defense in
Depth adds layers but may leave broad inner roles. Separation of Privilege
requires multiple authorities for selected actions. Zero Trust continuously
evaluates access to resources. Capability-Based Security hands out narrow
object references.

**Delivery speed.** Least Privilege is slower while permissions are learned.
Defense in Depth is often incremental and easier to add. Separation of
Privilege is slower for workflows needing approval or protocol split. Zero
Trust is slower when identity, device, and policy systems are immature.
Capability-Based Security is fast in code and harder across service
boundaries.

**Availability.** Least Privilege risks false denials. Defense in Depth has
layers that can fail independently. Separation of Privilege risks approval or
parent-process bottlenecks. Zero Trust risks policy engine dependency.
Capability-Based Security risks lost or poorly propagated capabilities.

**Coupling.** Least Privilege couples work to explicit actions and resources.
Defense in Depth couples less to exact permissions. Separation of Privilege
couples callers to a privileged broker or approver. Zero Trust couples requests
to identity and posture signals. Capability-Based Security couples callers to
authority-bearing objects.

**Operability.** Least Privilege is strong when denials and usage are logged.
Defense in Depth can be noisy because many controls emit events. Separation of
Privilege is clear for privileged operations and less clear for child activity.
Zero Trust needs mature decision logs. Capability-Based Security is harder to
inspect if capabilities are in memory only.

**Cognitive load.** Least Privilege is high because teams must understand
effective permissions. Defense in Depth is medium because teams reason about
layers. Separation of Privilege is medium to high because teams reason about
split protocols. Zero Trust is high because teams reason about identity,
device, session, and resource. Capability-Based Security is medium in code and
high for distributed revocation.

**Best fit.** Least Privilege fits routine containment of users and workloads.
Defense in Depth fits reducing reliance on any single control. Separation of
Privilege fits high-risk actions needing independent conditions. Zero Trust
fits per-request enterprise resource access. Capability-Based Security fits
fine-grained in-process or object authority.

These alternatives compose more often than they replace each other. A zero
trust deployment without Least Privilege still grants too much after the user
is verified. Least Privilege without defense in depth relies too much on policy
correctness. Capability-based code can be the implementation technique inside a
least-privilege service.

## 13. Related and incompatible patterns

**Zero Trust** composes with Least Privilege. NIST SP 800-207 describes zero
trust as moving defense from static network perimeters toward users, assets,
and resources, with authentication and authorization before sessions ([NIST SP
800-207](https://csrc.nist.gov/pubs/sp/800/207/final), verified 2026-08-02).
Least Privilege supplies the "how much authority" answer after the subject is
known.

**Role-Based Access Control** is a common implementation. It maps subjects to
roles and roles to permissions. It conflicts when roles are job-title buckets
that gather unrelated powers.

**Capability-Based Security** can implement Least Privilege by passing only the
authority an object needs. It is a replacement for global ambient authority
inside a codebase.

**Privilege Separation** composes when a process must parse untrusted input and
also perform privileged operations. OpenSSH privilege separation is the named
example in the USENIX paper cited above.

**Defense in Depth** composes. Least Privilege narrows one subject. Defense in
Depth adds independent controls such as network policy, input validation,
sandboxing, rate limits, and monitoring.

**Complete Mediation** is a sibling principle from Saltzer and Schroeder. Least
Privilege says the grant should be small. Complete Mediation says each access
should be checked.

**Separation of Duties** and **Separation of Privilege** compose for high-risk
actions. Least Privilege may still allow one subject to perform a task alone.
The separation patterns require multiple roles, keys, or approvals.

**Secrets Management** composes because credentials should carry narrow,
rotatable authority. A vault full of administrator tokens is secret storage,
not Least Privilege.

**Ambient Authority** conflicts. If code can reach global credentials, process
environment secrets, or singleton clients with broad powers, review of a
function's true authority becomes guesswork.

**Shared Administrator Account** conflicts because accountability and scope are
lost. Every user receives every power, and audit cannot map action to person.

**Wildcard Permission** conflicts when used as a standing grant. It can be
acceptable in a short isolated discovery phase, but not as a stable permission
model.

## 14. Refactoring path in and out

Refactoring in.

1. **Inventory subjects.** List humans, service accounts, workloads, CI jobs,
   functions, database users, and break-glass identities. Remove identities that
   no longer map to a real owner.
2. **Name tasks.** For each subject, write the task in business language. If
   one subject has several unrelated tasks, split the subject.
3. **Record current effective permissions.** Include inherited groups,
   parent-scope grants, resource policies, impersonation rights, and service
   account use.
4. **Observe used permissions.** Use audit logs, access analyzers, integration
   tests, and production traffic samples. AWS and Google Cloud both document
   tools that infer or recommend narrower roles from activity ([AWS IAM
   policies and permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html),
   verified 2026-08-02; [Google Cloud, review and apply role recommendations](https://docs.cloud.google.com/policy-intelligence/docs/review-apply-role-recommendations),
   verified 2026-08-02).
5. **Create a candidate narrow role.** Prefer resource scope, action scope, and
   conditions over broad project or account grants.
6. **Run in shadow where possible.** Log would-deny decisions before enforcing.
   If the platform lacks shadow policy, test in staging with production-like
   actions.
7. **Cut one task at a time.** Attach the narrow role to one subject or one
   environment. Keep rollback ready.
8. **Remove the broad role.** A narrow role layered on top of an administrator
   role buys nothing.
9. **Add review cadence.** Retire unused permissions, expired grants, empty
   roles, and ownerless identities.

Refactoring out.

1. **Detect policy cost exceeding value.** Signals include frequent false
   denials, many near-duplicate roles, slow incident response, and inability to
   explain effective permissions.
2. **Merge roles by task, not by team politics.** If two roles always change
   together and protect the same resource class, merge them.
3. **Replace custom roles with maintained predefined roles where they fit.**
   The predefined role may be broader, so document the accepted risk.
4. **Move checks into a broker service.** If clients need many small grants to
   perform one business operation, a service with a narrow API may express the
   boundary better.
5. **Keep audit and expiry.** Removing fine-grained policy should not remove
   observability or break-glass controls.

Relevant refactorings from the refactoring family include Extract Function,
Extract Class, Replace Conditional with Polymorphism when different tasks are
mixed in one module, and Introduce Parameter Object when subject, action,
resource, and conditions are passed loosely.

## 15. Testing and verification

Engineering judgement: test Least Privilege as a contract with positive and
negative cases. A role with only happy-path tests is often wider than needed.

Test layers.

- **Policy unit tests.** Given subject, action, resource, and context, assert
  allow or deny. Use table tests with both expected grants and forbidden
  actions.
- **Integration tests with real credentials.** Run the service under its
  production-shaped role in a test account. Avoid running tests under a
  developer administrator account.
- **Negative permission tests.** Prove the service cannot list peer tenant
  data, delete outside its prefix, impersonate another service account, read
  secrets it does not need, or alter policy.
- **Escalation tests.** In Kubernetes, test whether a role that can create
  workloads can mount stronger service accounts or sensitive volumes. Kubernetes
  documents several RBAC escalation areas, including Secrets listing, workload
  creation, persistent volumes, and node proxy access ([Kubernetes RBAC good
  practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/),
  verified 2026-08-02).
- **Replay tests.** Feed audit-log actions from the last release into the
  candidate policy. Expect known actions to pass and new broad actions to fail
  review.
- **Expiry tests.** For time-bound grants, assert that access stops after the
  window and that renewal requires a fresh request.
- **Break-glass tests.** Verify emergency access works, logs the session, and
  triggers review. Do this before an incident.

Test doubles should preserve the policy shape. A fake storage client that
ignores resource names will miss cross-tenant access bugs. A better double
checks the same action and resource strings as the real policy, even if it
stores data in memory.

What became easier: proving that a component cannot perform unrelated actions.
What became harder: diagnosing whether a failure is business logic, credentials,
resource naming, inherited policy, or conditional context.

## 16. Observability signals

Engineering judgement: observability is the difference between narrow access
and blind denial. A least-privilege system should make access visible without
logging sensitive data.

Log for every authorization decision.

- Subject id, subject type, and session id.
- Action and resource, in canonical form.
- Decision, allow or deny.
- Policy id, role id, or rule id that matched.
- Condition fields used in the decision, such as tenant, environment, expiry,
  device posture, or request path.
- Caller service, build id, and deployment version.
- Correlation id linking the application request to the audit event.

Metrics.

- Deny rate by service, action, resource class, and policy id.
- Allows for high-risk actions such as delete, policy edit, impersonate,
  decrypt, sign, create workload, and read secret.
- Unused permissions by role over the review window.
- Subjects with wildcard actions or account-wide resources.
- Privilege elevation requests, approvals, duration, and post-expiry attempts.
- Break-glass activations and session length.
- Effective permission count by subject over time.

Healthy dashboards show low false-denial rates, no routine break-glass use,
shrinking unused permissions, few wildcard grants, and high-risk actions tied to
expected services. Failing dashboards show rising 403s after deploy, frequent
manual role edits, long-lived higher-access sessions, broad roles attached to new
workloads, or access to Secrets by services that do not own them.

Alert on behavior that changes authority, not every denied typo. Good alerts
include new wildcard grant, new policy editor, service account impersonation by
a new subject, namespace-level workload creation by an untrusted team, root or
administrator credential use, and deletion of audit policy.

## 17. Security and privacy implications

Least Privilege closes attack surface by reducing the useful authority of a
captured subject. It is directly relevant to confidentiality, integrity, and
availability. Confidentiality improves when read access is limited by resource,
tenant, field, or purpose. Integrity improves when write, delete, policy edit,
and impersonation rights are scarce. Availability improves when accidental or
malicious destructive actions cannot reach unrelated systems.

The pattern also exposes hidden privacy questions. A support engineer may need
to diagnose one account, not export all customer records. A model training job
may need a redacted dataset, not raw production logs. A billing report may need
aggregate totals, not payment details. Least Privilege forces those distinctions
into policy, service design, or query interface.

It is silent on several concerns. It does not validate input. It does not
encrypt data. It does not prove the policy is correct. It does not remove the
need for patching, dependency review, backup, rate limiting, or anomaly
detection. It also does not stop misuse by a subject that legitimately has the
needed power for the moment of misuse. A payroll admin with approved payroll
write access can still enter a bad payroll change. That risk needs workflow
approval, reconciliation, or separation of duties.

The main new attack surface is the access-control system itself. Policy editors
become high-value targets. Role recommendation tools can be misunderstood.
Condition logic can be bypassed if resource tags or identity attributes are
wrong. Token exchange services, privilege brokers, and approval systems must
therefore run with their own narrow roles, strong audit, and tested recovery.

## 18. References

- Jerome H. Saltzer and Michael D. Schroeder, "The Protection of Information
  in Computer Systems," *Proceedings of the IEEE*, volume 63, issue 9, 1975,
  section I.A.3, "Design Principles." Web copy at
  https://www.cs.virginia.edu/~evans/cs551/saltzer/, verified 2026-08-02.
- NIST Computer Security Resource Center, "least privilege," glossary entry,
  sources include CNSSI 4009-2015, NIST SP 800-12 Rev. 1, NIST SP 800-53 Rev.
  5, and NIST SP 800-171r3. https://csrc.nist.gov/glossary/term/least_privilege,
  verified 2026-08-02.
- Scott Rose, Oliver Borchert, Stu Mitchell, and Sean Connelly, NIST Special
  Publication 800-207, *Zero Trust Architecture*, final publication, August
  2020. https://csrc.nist.gov/pubs/sp/800/207/final, verified 2026-08-02.
- Amazon Web Services, AWS Identity and Access Management User Guide,
  "Policies and permissions in AWS Identity and Access Management."
  https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html,
  verified 2026-08-02.
- Amazon Web Services, AWS Identity and Access Management User Guide, "Prepare
  for least-privilege permissions."
  https://docs.aws.amazon.com/IAM/latest/UserGuide/getting-started-reduce-permissions.html,
  verified 2026-08-02.
- Amazon Web Services, AWS Identity and Access Management User Guide, "IAM
  Access Analyzer policy generation."
  https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-policy-generation.html,
  verified 2026-08-02.
- Kubernetes Documentation, "Role Based Access Control Good Practices."
  https://kubernetes.io/docs/concepts/security/rbac-good-practices/, verified
  2026-08-02.
- Google Cloud Documentation, Identity and Access Management, "Use IAM
  securely." https://docs.cloud.google.com/iam/docs/using-iam-securely?authuser=01&hl=en,
  verified 2026-08-02.
- Google Cloud Documentation, Policy Intelligence, "Review and apply role
  recommendations for projects, folders, and organizations."
  https://docs.cloud.google.com/policy-intelligence/docs/review-apply-role-recommendations,
  verified 2026-08-02.
- Michael Kerrisk, Linux man-pages project, "capabilities(7), overview of Linux
  capabilities." https://man7.org/linux/man-pages/man7/capabilities.7.html,
  verified 2026-08-02.
- Niels Provos, Markus Friedl, and Peter Honeyman, "Preventing Privilege
  Escalation," 12th USENIX Security Symposium, 2003, sections 2 through 5.
  https://www.usenix.org/legacy/event/sec03/tech/full_papers/provos_et_al/provos_et_al_html/,
  verified 2026-08-02.

## Code examples

The examples use the same small model in three languages. A report task receives
only the repository interface it needs. It can read invoices but cannot delete
them because no delete method is present on the object handed to it.

### TypeScript

```typescript
type Invoice = { id: string; customer: string; cents: number };

interface InvoiceReader {
  findInvoice(id: string): Invoice | undefined;
}

class InMemoryInvoices implements InvoiceReader {
  private rows = new Map<string, Invoice>([
    ["inv-1", { id: "inv-1", customer: "Ada", cents: 4200 }],
  ]);

  findInvoice(id: string): Invoice | undefined {
    return this.rows.get(id);
  }

  deleteInvoice(id: string): void {
    this.rows.delete(id);
  }
}

function renderReceipt(reader: InvoiceReader, id: string): string {
  const invoice = reader.findInvoice(id);
  if (!invoice) return "missing";
  return `${invoice.customer}:${invoice.cents}`;
}

const store = new InMemoryInvoices();
console.log(renderReceipt(store, "inv-1"));
```

### Python

```python
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Invoice:
    id: str
    customer: str
    cents: int


class InvoiceReader(Protocol):
    def find_invoice(self, invoice_id: str) -> Invoice | None:
        ...


class InMemoryInvoices:
    def __init__(self) -> None:
        self._rows = {"inv-1": Invoice("inv-1", "Ada", 4200)}

    def find_invoice(self, invoice_id: str) -> Invoice | None:
        return self._rows.get(invoice_id)

    def delete_invoice(self, invoice_id: str) -> None:
        del self._rows[invoice_id]


def render_receipt(reader: InvoiceReader, invoice_id: str) -> str:
    invoice = reader.find_invoice(invoice_id)
    if invoice is None:
        return "missing"
    return f"{invoice.customer}:{invoice.cents}"


if __name__ == "__main__":
    print(render_receipt(InMemoryInvoices(), "inv-1"))
```

### Go

```go
package main

import "fmt"

type Invoice struct {
	ID       string
	Customer string
	Cents    int
}

type InvoiceReader interface {
	FindInvoice(id string) (Invoice, bool)
}

type InMemoryInvoices struct {
	rows map[string]Invoice
}

func NewInvoices() *InMemoryInvoices {
	return &InMemoryInvoices{
		rows: map[string]Invoice{
			"inv-1": {ID: "inv-1", Customer: "Ada", Cents: 4200},
		},
	}
}

func (s *InMemoryInvoices) FindInvoice(id string) (Invoice, bool) {
	invoice, ok := s.rows[id]
	return invoice, ok
}

func (s *InMemoryInvoices) DeleteInvoice(id string) {
	delete(s.rows, id)
}

func RenderReceipt(reader InvoiceReader, id string) string {
	invoice, ok := reader.FindInvoice(id)
	if !ok {
		return "missing"
	}
	return fmt.Sprintf("%s:%d", invoice.Customer, invoice.Cents)
}

func main() {
	fmt.Println(RenderReceipt(NewInvoices(), "inv-1"))
}
```

In each language, the concrete store has more authority than the report task.
The task receives a narrowed view. This is not a replacement for platform IAM,
but it prevents accidental calls in code and makes tests state the authority
contract.
