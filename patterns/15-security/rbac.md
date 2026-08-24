---
name: Role-Based Access Control
slug: rbac
family: 15-security
category: Security
aliases: [RBAC, Role Based Access Control, Role-Based Security]
first_described: "Ferraiolo and Kuhn 1992"
maturity: canonical
related: [least-privilege, separation-of-duties, zero-trust, federated-identity, complete-mediation, gatekeeper]
incompatible_with: [ambient-authority, per-user-permission-sprawl, hardcoded-authorization]
verified: 2026-08-02
---

# Role-Based Access Control

## 1. Name, aliases, and lineage

The canonical name is Role-Based Access Control, usually shortened to RBAC.
NIST also records the unhyphenated form Role Based Access Control and the alias
role based security on its RBAC project page
([NIST CSRC RBAC project](https://csrc.nist.gov/projects/role-based-access-control),
verified 2026-08-02). This entry uses RBAC for the model and role-based access
control for the architectural style.

The modern formal lineage starts with David Ferraiolo and Richard Kuhn's 1992
paper, "Role-Based Access Controls", presented at the 15th National Computer
Security Conference. NIST lists the paper as published on October 13, 1992, in
the conference proceedings, pages 554 to 563, and describes it as a paper that
defined RBAC as a non-discretionary access control approach for commercial and
civilian systems
([NIST CSRC, "Role-Based Access Controls"](https://csrc.nist.gov/pubs/conference/1992/10/13/rolebased-access-controls/final),
verified 2026-08-02). The NIST FAQ says that the 1992 model gave formal rules
for role assignment, role authorization, and transaction authorization, and
framed all user activity after login as transactions mediated through active
roles
([NIST CSRC RBAC FAQ](https://csrc.nist.gov/Projects/role-based-access-control/faqs),
verified 2026-08-02).

The next major lineage step is the 1996 framework by Ravi Sandhu, Edward Coyne,
Hal Feinstein, and Charles Youman. NIST describes that framework as dividing
RBAC into RBAC0 for users, roles, and permissions, RBAC1 for hierarchies, RBAC2
for constraints, and RBAC3 for the combined form
([NIST CSRC RBAC FAQ](https://csrc.nist.gov/Projects/role-based-access-control/faqs),
verified 2026-08-02). In 2000, Sandhu, Ferraiolo, and Kuhn proposed a unified
NIST RBAC model for standardization, and NIST records that ANSI/INCITS adopted
the model as ANSI INCITS 359-2004, then revised it as INCITS 359-2012
([NIST CSRC RBAC project](https://csrc.nist.gov/projects/role-based-access-control),
verified 2026-08-02).

The vocabulary is often blurred in product docs. A GitLab project role, a
Kubernetes Role, an Azure role definition, a PostgreSQL role, and an AWS IAM
role all use role wording, but they do not share one identical semantics. Some
roles are assignable permission bundles, some are assumable identities, some
can be nested, some attach to scopes, and some include policy conditions. The
pattern in this entry is the common authorization architecture: permissions are
bound to roles, subjects are bound to roles, and runtime decisions ask whether
the subject has an active role whose permissions cover the requested operation
on the requested resource.

## 2. Problem and context

A system has many people, services, jobs, and automated agents, and each one
needs different authority over many objects. Direct user-to-permission grants
start readable, then collapse under change. A support engineer needs read
access to customer records but not exports. A release manager needs deployment
rights but not billing rights. A batch job needs to write one table but not
change schema. A tenant administrator needs power inside one tenant, not across
the whole service. If each subject receives raw permissions one by one, every
joiner, mover, incident, audit, and feature launch becomes a manual policy
diff.

RBAC introduces an intermediate object, the role. The role names a job function
or system duty and carries the permission set for that function. Users and
workloads receive roles. Code and policy checks ask about actions on resources.
The operator changes memberships when people move, and changes role definitions
when the job changes. NIST's RBAC background says that security administration
with RBAC is based on determining which operations people in particular jobs
must perform, then assigning employees to the proper roles
([NIST CSRC RBAC project](https://csrc.nist.gov/projects/role-based-access-control),
verified 2026-08-02).

The context that makes RBAC fit has four parts.

- There are repeated job functions or service duties. If every subject is a
  one-off exception, roles become disguised user permissions.
- The protected operations can be named and checked. A role that cannot be
  mapped to concrete actions is only a label.
- Role membership changes more often than the meaning of the role. NIST notes
  that roles tend to be more stable than users and permissions in an
  organization
  ([NIST CSRC RBAC FAQ](https://csrc.nist.gov/Projects/role-based-access-control/faqs),
  verified 2026-08-02).
- The system has a policy enforcement point on every protected operation. RBAC
  does not help when code bypasses authorization checks or talks straight to a
  datastore under a shared account.

Engineering judgement: RBAC is strongest in administrative systems, cloud
control planes, databases, source code platforms, workflow tools, and enterprise
applications where job functions repeat. It is weaker in collaborative apps
where access is based on a subject's relationship to one object, such as "the
doctor assigned to this patient" or "the owner of this document". In those
cases RBAC can still contribute broad job permissions, but it needs object
relationships, attributes, or policy conditions beside it.

## 3. Forces

Engineering judgement: this dimension weighs design pressure. Citations in this
section name known mechanisms; the balance described here is a design reading.

- **Coupling.** Favoured. Business code asks for `invoice.approve` or
  `pods/list`; it does not need to know every user or group that might receive
  that authority. The price is coupling to stable action names and resource
  scopes.
- **Consistency.** Favoured when roles are centrally defined, versioned, and
  reused. Sacrificed when teams clone roles and make local exceptions until
  "support-reader" means a different thing in every service.
- **Latency.** Usually close to neutral when roles are materialized in a token,
  session, database row, or cache. It becomes a cost when every request calls a
  remote policy service, expands nested groups, or walks a deep role hierarchy.
- **Operability.** Favoured because auditors can review named roles and
  memberships. Sacrificed when denial logs omit the subject, requested action,
  resource, active roles, and rule that caused the decision.
- **Cost.** Favoured over time because role assignment scales better than raw
  grants per user. Sacrificed early through role design, migration, lifecycle
  tooling, and cleanup of legacy grants.
- **Team topology.** Favoured when platform or security teams own role schema
  and guardrails while product teams own resource-specific permissions.
  Sacrificed when every new permission waits on a central board that lacks
  product context.
- **Cognitive load.** Sacrificed. Developers must understand inherited roles,
  additive grants, deny rules where present, active session roles, and scope.
  Azure RBAC, for example, evaluates role assignments at resource scope and
  treats multiple role assignments as additive unless deny assignments or
  conditions change the result
  ([Microsoft Learn, Azure RBAC overview](https://learn.microsoft.com/en-us/azure/role-based-access-control/overview),
  verified 2026-08-02).
- **Least privilege.** Mixed. RBAC can encode least privilege at job-function
  level, but coarse roles become standing power. Google Cloud states that IAM
  roles are collections of permissions and offers basic, predefined, and custom
  roles, with custom roles intended for finer permission sets
  ([Google Cloud IAM roles overview](https://docs.cloud.google.com/iam/docs/roles-overview?authuser=0),
  verified 2026-08-02).
- **Change safety.** Favoured when role definitions have tests and staged
  rollout. Sacrificed because one mistaken edit to a shared role can grant or
  remove access for thousands of subjects at once.

The pattern favours administrative scale and auditability. It sacrifices local
simplicity and some precision when a decision depends on attributes that do not
belong in a role.

## 4. Applicability and non-applicability

Reach for RBAC when these conditions hold.

- **The organization has repeatable duties.** "Project maintainer", "billing
  viewer", "cluster operator", and "invoice approver" are role candidates
  because many subjects can perform the same set of actions.
- **Permission review is a recurring requirement.** Reviewers can understand a
  role-to-user and role-to-permission table faster than thousands of raw
  exceptions.
- **Subjects move between jobs.** Membership changes let a transfer remove old
  power and add new power without editing application code.
- **The platform already exposes roles.** Kubernetes has Role, ClusterRole,
  RoleBinding, and ClusterRoleBinding objects in its RBAC authorizer
  ([Kubernetes RBAC authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/),
  verified 2026-08-02). PostgreSQL manages access through roles that can own
  objects, receive privileges, and receive membership in other roles
  ([PostgreSQL 16, Chapter 22, Database Roles](https://www.postgresql.org/docs/16/user-manag.html),
  verified 2026-08-02).
- **The model needs hierarchy.** RBAC1 and hierarchical RBAC allow senior roles
  to include junior role permissions, although local product semantics decide
  whether hierarchy is a gain or a trap
  ([NIST CSRC RBAC FAQ](https://csrc.nist.gov/Projects/role-based-access-control/faqs),
  verified 2026-08-02).
- **The model needs separation of duty.** NIST's FAQ says the RBAC standard
  covers static and dynamic separation of duty relations
  ([NIST CSRC RBAC FAQ](https://csrc.nist.gov/Projects/role-based-access-control/faqs),
  verified 2026-08-02). Use that when one person must not both request and
  approve the same risk.
- **The subject set includes both humans and services.** The same pattern can
  authorize users, service accounts, background jobs, and role sessions, as long
  as each subject identity is distinct.

Non-applicability list.

- **Object ownership is the main rule.** If access is "the record owner can edit
  the record", model ownership or ACLs. A role named `owner` without an object
  link becomes wrong as soon as the subject owns one resource but not another.
- **Relationship-based access drives the decision.** "Attending physician for
  this patient" or "manager of this employee" depends on a subject-object
  relationship. NIST's FAQ discusses such constraints as access-time rules that
  may sit beside RBAC, not as pure role membership
  ([NIST CSRC RBAC FAQ](https://csrc.nist.gov/Projects/role-based-access-control/faqs),
  verified 2026-08-02).
- **Context changes the answer per request.** Time, device posture, network
  zone, risk score, data classification, and consent state fit ABAC or policy
  conditions better than role proliferation. NIST SP 800-162 defines ABAC as
  authorization based on attributes of the subject, object, operation, and
  environment
  ([NIST SP 800-162](https://csrc.nist.gov/pubs/sp/800/162/upd2/final),
  verified 2026-08-02).
- **There are too few subjects.** For a small internal tool with three users and
  two actions, a direct allowlist may be clearer. Add RBAC when review,
  onboarding, or object count makes the allowlist painful.
- **Every subject needs a custom bundle.** That is per-user permission sprawl
  with role names attached. Use policy templates, ABAC, or a request workflow
  rather than minting one role per person.
- **The platform has no reliable identity.** RBAC depends on a trustworthy
  subject identifier. If requests arrive with only an unsigned header or a
  shared API key, fix authentication first.
- **Authorization can be bypassed.** RBAC must sit on every protected path. A
  service that checks the UI but exposes an unchecked export endpoint has not
  implemented RBAC.
- **Denied access must hide resource existence.** RBAC can deny an action, but
  list and lookup paths often leak whether an object exists. Use object-level
  filtering and response shaping when existence is sensitive.
- **Regulators require explicit per-object grants.** Some workflows demand
  record-level consent, warrant, case assignment, or chain-of-custody evidence.
  RBAC can be one layer, but not the whole authorization record.

## 5. Structure

RBAC has eight participants.

- **Subject.** A user, service account, workload, job, process, role session, or
  external principal making a request.
- **Role.** A named function or duty that groups permissions. The role should
  be stable enough to document and review.
- **Permission.** A permitted action over a resource type, resource instance, or
  resource scope. Examples include `repository.read`, `invoice.approve`,
  `pods/list`, and `SELECT` on a table.
- **Resource.** The protected object. A resource can be a row, table, project,
  namespace, secret, bucket, key, tenant, API route, or deployment target.
- **Assignment.** The relation binding subjects to roles. It may be direct,
  inherited through a group, scoped to a tenant, or time-bound.
- **Role hierarchy.** An optional relation in which one role includes another
  role's permissions. NIST describes hierarchical RBAC as adding role hierarchy
  relations above core RBAC
  ([NIST CSRC RBAC FAQ](https://csrc.nist.gov/Projects/role-based-access-control/faqs),
  verified 2026-08-02).
- **Constraint.** A rule that restricts assignment or activation. Static
  separation of duty blocks conflicting memberships; dynamic separation of duty
  blocks conflicting active roles in the same session
  ([NIST CSRC RBAC FAQ](https://csrc.nist.gov/Projects/role-based-access-control/faqs),
  verified 2026-08-02).
- **Policy enforcement point.** The code path or platform component that checks
  the request before the protected action runs. In web systems this is often
  middleware or a guard. In databases it is the database authorization engine.
  In Kubernetes it is the API server's authorizer.

Relationships. A subject is assigned one or more roles. A role contains one or
more permissions. A permission names an action and resource scope. A role may
inherit from another role. A session may activate only a subset of assigned
roles. The enforcement point evaluates the subject, active roles, requested
action, resource, scope, hierarchy, and constraints before allowing the action.

The key design rule is that permissions bind to roles, not directly to users,
for ordinary access. The NIST FAQ distinguishes RBAC from traditional groups by
stating that RBAC routes permissions through roles rather than directly through
users, and supports sessions that activate a subset of roles
([NIST CSRC RBAC FAQ](https://csrc.nist.gov/Projects/role-based-access-control/faqs),
verified 2026-08-02).

## 6. ASCII structure diagram

```text
 +------------+       assigned        +-----------+
 |  Subject   |---------------------->|   Role    |
 | user/job   |                       | duty name |
 +------------+                       +-----------+
       |                                    |
       | starts session                     | contains
       v                                    v
 +------------+       activates       +-------------+
 |  Session   |---------------------->| Permission  |
 | active set |                       | action+res  |
 +------------+                       +-------------+
       |                                    |
       | request                            | applies to
       v                                    v
 +----------------------+            +-------------+
 | Policy Enforcement   |----------->|  Resource   |
 | Point                | decision   | object/scope|
 +----------------------+            +-------------+
       ^
       |
       | checks
       |
 +----------------------+
 | Constraints          |
 | SSD, DSD, conditions |
 +----------------------+

 SSD means static separation of duty.
 DSD means dynamic separation of duty.
```

## 7. Dynamics

At runtime, RBAC is a decision loop. The subject authenticates, receives or
selects active roles, sends a request, and the enforcement point decides whether
any active role grants the requested operation at the requested scope after
hierarchy and constraints are applied.

```text
Subject        Identity       Session        Enforcement      Resource
  |              |              |                |                |
  |-- login ---->|              |                |                |
  |<-- identity -|              |                |                |
  |                             |                |                |
  |-- activate roles ---------->|                |                |
  |                             |-- check SSD/DSD|                |
  |<-- active role set ---------|                |                |
  |                             |                |                |
  |-- request action on resource -------------> |                |
  |                             |                |-- load roles --|
  |                             |                |-- expand tree -|
  |                             |                |-- match perm --|
  |                             |                |-- constraints -|
  |                             |                |                |
  |<-- allow or deny -------------------------- |                |
  |                             |                |                |
  |-- if allowed, action ---------------------->|--------------->|
  |<-- result ----------------------------------|<---------------|
```

The main dynamic risk is stale authority. A user can change teams, a service
can stop needing a permission, or a role can grow until old grants mean more
than the reviewer thinks. The runtime answer may be correct for the current
tables and still wrong for the business. That is why RBAC needs lifecycle work:
assignment expiry, role review, permission diff review, and logs that explain
why a decision was made.

Scope changes the flow. Kubernetes distinguishes namespace RoleBindings from
ClusterRoleBindings. A RoleBinding grants role permissions inside one namespace,
while a ClusterRoleBinding grants the referenced ClusterRole across the cluster
([Kubernetes RBAC authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/),
verified 2026-08-02). Azure RBAC attaches role definitions to principals at a
particular scope and evaluates role assignments that apply to the requested
resource
([Microsoft Learn, Azure RBAC overview](https://learn.microsoft.com/en-us/azure/role-based-access-control/overview),
verified 2026-08-02). A correct evaluator must therefore treat scope as part of
the permission, not metadata.

## 8. Implementation variants

**Flat RBAC.** Roles do not inherit from other roles. The evaluator expands only
direct assignments. This is the easiest form to test and explain. It fits small
products and critical systems where inherited power would hide too much.

**Hierarchical RBAC.** Roles inherit permissions from other roles. It reduces
duplication when `maintainer` should include `developer` and `developer` should
include `reporter`. It can also hide excess access when a high-level role
inherits an old low-level permission nobody remembers. NIST identifies
hierarchical RBAC as a separate component from core RBAC
([NIST CSRC RBAC FAQ](https://csrc.nist.gov/Projects/role-based-access-control/faqs),
verified 2026-08-02).

**Constrained RBAC.** Assignment and activation rules block toxic combinations.
Static separation of duty prevents one subject from being assigned conflicting
roles. Dynamic separation of duty allows assignment to both roles but prevents
activating both at once. Use this when organizational control matters as much
as individual access.

**Scoped RBAC.** A role assignment applies only under a resource scope such as
tenant, project, namespace, subscription, folder, group, or database. Azure
RBAC's role assignment includes role definition, security principal, and scope
([Microsoft Learn, Azure RBAC overview](https://learn.microsoft.com/en-us/azure/role-based-access-control/overview),
verified 2026-08-02). Kubernetes RoleBinding and ClusterRoleBinding represent
the same scoped design at namespace and cluster level
([Kubernetes RBAC authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/),
verified 2026-08-02).

**Additive RBAC with deny overlay.** Pure RBAC usually treats grants as
additive. Azure RBAC says overlapping role assignments add together, then deny
assignments, actions excluded by `NotActions`, data exclusions, and conditions
can narrow the result
([Microsoft Learn, Azure RBAC overview](https://learn.microsoft.com/en-us/azure/role-based-access-control/overview),
verified 2026-08-02). The gain is practical control over broad roles. The cost
is harder explanation, because "has role X" no longer means "allowed".

**Permission matrix in application code.** The app stores roles and
permissions in tables or config and the guard checks them. This is common in
SaaS apps. It is fast to start, but the app team must build migration,
observability, review, and admin tooling.

**Policy engine backed RBAC.** Roles become facts in a policy engine, and the
engine evaluates role membership beside attributes or relationships. OASIS
defines an XACML 3.0 profile for core and hierarchical RBAC
([OASIS XACML 3.0 RBAC profile](https://docs.oasis-open.org/xacml/3.0/xacml-3.0-rbac-v1-spec-en.html),
verified 2026-08-02). This gives a standard policy vocabulary, but brings
policy language complexity.

**Database-native RBAC.** The database enforces roles and privileges itself.
PostgreSQL states that roles can own database objects, receive privileges, and
receive membership in other roles
([PostgreSQL 16, Chapter 22, Database Roles](https://www.postgresql.org/docs/16/user-manag.html),
verified 2026-08-02). This protects access even when multiple apps connect to
the same database. It does not replace application checks for business actions
that the database cannot see.

**Token-embedded roles.** Authentication creates a token or session containing
role names. The gain is low-latency local checks. The cost is revocation lag:
role removal may not take effect until the token expires unless the system also
checks a server-side version or revocation list.

## 9. Known production uses

**Kubernetes RBAC authorization.** Kubernetes documents an RBAC authorizer with
Role and ClusterRole objects to define permissions, and RoleBinding and
ClusterRoleBinding objects to grant those permissions to users, groups, or
service accounts. The docs state that RoleBinding grants permissions inside a
namespace and ClusterRoleBinding grants cluster-wide access
([Kubernetes RBAC authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/),
verified 2026-08-02).

**Microsoft Azure RBAC.** Azure RBAC grants access by role assignments that
attach a role definition to a user, group, service principal, or managed
identity at a scope. Azure's docs describe the evaluation flow, including token
acquisition, retrieval of role and deny assignments, action matching, and
condition checks
([Microsoft Learn, Azure RBAC overview](https://learn.microsoft.com/en-us/azure/role-based-access-control/overview),
verified 2026-08-02).

**PostgreSQL database roles.** PostgreSQL manages database access permissions
using roles. Its documentation states that roles can act as users or groups,
own database objects, receive privileges on objects, and receive membership in
other roles
([PostgreSQL 16, Chapter 22, Database Roles](https://www.postgresql.org/docs/16/user-manag.html),
verified 2026-08-02).

**GitLab project and group roles.** GitLab documents default roles and custom
roles for projects and groups. Its permissions page says roles define a user's
permissions in a group or project, and its custom roles page says custom roles
are based on an existing default role with selected custom permissions
([GitLab roles and permissions](https://docs.gitlab.com/user/permissions/),
verified 2026-08-02; [GitLab custom roles](https://docs.gitlab.com/user/custom_roles/),
verified 2026-08-02).

**AWS IAM role-based access control.** AWS IAM documentation describes IAM roles
as identities with permission policies that can be assumed by those who need
them, and AWS IAM FAQs state that RBAC can be implemented by defining IAM roles
with permissions aligned to job functions and granting individuals access to
assume those roles
([AWS IAM roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html),
verified 2026-08-02; [AWS IAM FAQs](https://aws.amazon.com/iam/faqs/),
verified 2026-08-02).

## 10. Consequences

Engineering judgement: this section describes typical outcomes. The named
products in dimension 9 prove the pattern is widely implemented, but the
following trade-offs must be checked against each codebase.

Positive.

- Access review becomes role-centered. A reviewer can ask whether a user should
  hold `project-maintainer` instead of reading every raw permission.
- Onboarding and transfer are faster because the assignment changes while the
  role definition stays stable.
- Permission naming improves. A good RBAC system forces teams to name actions
  and resources before they grant them.
- Least privilege becomes more repeatable because one corrected role improves
  every subject assigned to it.
- Audits become easier because role membership, role definition, and permission
  checks create a trail.
- Separation of duty becomes representable in the access model rather than in
  training material.
- Application code can use one authorization API across many features.

Negative.

- Role explosion is common. Teams create a new role for every exception until
  the system has as many roles as users.
- Coarse roles accumulate power. A role that begins as read-only may become
  "read plus export plus impersonate plus bypass" after years of ticket-driven
  edits.
- Inherited roles hide authority. A senior role may receive a dangerous
  permission through a junior role name nobody reviews.
- Denials become harder to debug when roles come from identity provider groups,
  app tables, scopes, token claims, and policy conditions at once.
- Central roles can slow product delivery if every permission addition requires
  a distant team to understand local feature semantics.
- Moving from direct grants to RBAC can break workflows that depended on
  undocumented access.
- Roles can encode organizational structure too literally. Reorganizations then
  become authorization migrations.

## 11. Failure modes and misuse

Engineering judgement: these are implementation and operations failures with
observable symptoms.

**Role explosion.** Symptom. The admin UI shows hundreds of near-duplicate
roles such as `analyst2`, `analyst-read-new`, and `analyst-temp`, and nobody can
say which one is current. Cause. Exceptions were solved by minting roles
instead of changing policy shape. Fix. Merge roles by job duty, add scope or
attribute conditions for real variation, and retire unused roles after audit.

**Privilege accretion.** Symptom. A user with an ordinary role can perform an
action that surprises the role owner, such as exporting all customer data.
Cause. Permissions were added to unblock tickets but never reviewed as a whole.
Fix. Treat role definitions as reviewed code, require diff approval for high
risk actions, and run periodic role recertification.

**Direct grants bypass the role model.** Symptom. Removing a role does not
remove access, and denial logs show an allow from a user-specific exception.
Cause. The system permits raw subject-to-permission grants beside RBAC. Fix.
Block direct grants for ordinary access, migrate exceptions into scoped roles,
and alert on any raw grant outside break-glass procedures.

**Stale token roles.** Symptom. A user removed from a role can keep acting for
minutes or hours, usually until a token or session expires. Cause. Role names or
permissions were embedded in a bearer token without a revocation check. Fix.
Shorten token lifetime for high-risk roles, store a policy version in the
token, and reject tokens whose version is older than the subject's membership
version.

**Scope confusion.** Symptom. A project administrator can administer another
project, or a namespace operator can read cluster resources. Cause. The
evaluator ignored scope, treated a global role as local, or expanded hierarchy
before checking resource boundary. Fix. Include scope in every assignment and
permission check, and add tests where the same role name appears in two scopes.

**Hidden hierarchy grant.** Symptom. A role gains a permission even though the
role definition file does not list it. Cause. The permission came through an
inherited parent role. Fix. Show expanded permissions in review tools and make
role hierarchy shallow.

**Fail-open authorization.** Symptom. When the role store is down, requests
that should be denied are allowed. Cause. The enforcement point treats lookup
failure as empty error handling or uses a stale allow cache without expiry. Fix.
Fail closed for protected actions, cache only signed or versioned policy data,
and expose an operational mode for emergency read-only recovery.

**UI-only enforcement.** Symptom. Buttons disappear in the browser, but direct
API calls still work. Cause. RBAC was implemented as presentation logic, not as
server-side enforcement. Fix. Put the check on the server or database path and
use UI checks only as a convenience layer.

**Role names used as business truth.** Symptom. Code branches on
`if role == "manager"` for pricing, routing, or workflow state, and a role
rename breaks unrelated features. Cause. Authorization roles were reused as
domain model facts. Fix. Keep role checks limited to authorization and model
business state separately.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | RBAC | ABAC | ACL | ReBAC | Capability-Based Security | Hardcoded Guards |
|---|---|---|---|---|---|---|
| Coupling | Low to users, medium to action names | Medium to attributes and policy schema | High to object lists | Medium to graph relations | Low when capabilities are explicit | High to code branches |
| Consistency | Good with shared roles | Good with shared policy engine | Poor at scale | Good for relationship domains | Good inside small authority boundaries | Poor across services |
| Latency | Low with cached roles | Medium if policy calls are remote | Low per object, high for large lists | Medium due to graph traversal | Low when token is local | Low |
| Operability | Strong role reviews | Strong if policy traces are readable | Weak when lists sprawl | Strong if graph explains paths | Harder for auditors unfamiliar with it | Weak |
| Cost | Medium setup, lower admin cost later | Higher policy design cost | Low setup, high cleanup cost | Higher graph modeling cost | Medium design cost | Low setup, high defect cost |
| Team topology | Good with platform role schema | Good with central policy platform | Poor in shared objects | Good for collaboration products | Good for platform APIs | Poor when logic forks |
| Cognitive load | Medium | High | Low early, high later | High | Medium to high | Low early, high later |
| Least privilege | Good for job duties | Strong for context-rich policy | Strong per object, weak in review | Strong for object relationships | Strong by construction | Usually weak |
| Change safety | Shared role edits can be broad | Policy edits can be broad | Object edits are local | Graph changes can be broad | Capability issuance is explicit | Code releases required |

Reading of the table. RBAC wins where access follows job duties and where human
review matters. ABAC wins where attributes, time, environment, or data labels
drive the answer. ACLs win for simple per-object sharing. ReBAC wins when graph
relationships such as owner, member, parent, or viewer are the main rule.
Capability-based security wins when authority can be handed as an explicit
object or token. Hardcoded guards win only for trivial systems and become debt
when duties change.

## 13. Related and incompatible patterns

- **Least Privilege.** RBAC is one way to express least privilege. A small,
  reviewed role grants less power than a broad administrator role, but RBAC
  does not guarantee least privilege by itself.
- **Separation of Duties.** RBAC composes with static and dynamic separation of
  duty constraints. Use it when one subject must not hold or activate two
  conflicting powers.
- **Complete Mediation.** RBAC needs mediation on every protected action. If one
  endpoint bypasses the enforcement point, the role model is advisory.
- **Gatekeeper.** A gatekeeper component is a common enforcement point for RBAC.
  It centralizes checks and produces consistent decision logs.
- **Federated Identity.** Identity providers often supply groups or claims that
  map into roles. Keep the mapping explicit; do not treat every external group
  as an application role without review.
- **Zero Trust.** Zero Trust architecture keeps authorization close to each
  request. RBAC can supply one decision input, but device state, risk, network,
  and resource sensitivity may also matter.
- **ABAC.** ABAC can replace or extend RBAC. NIST SP 800-162 defines ABAC in
  terms of subject, object, operation, and environment attributes
  ([NIST SP 800-162](https://csrc.nist.gov/pubs/sp/800/162/upd2/final),
  verified 2026-08-02). Use ABAC when role names would multiply to encode
  context.
- **ACL.** ACLs can replace RBAC for per-object sharing. They conflict when a
  product promises all access through roles but then leaves invisible ACL grants
  on individual objects.
- **Capability-Based Security.** Capabilities replace role lookup with
  possession of an authority-bearing reference or token. This conflicts with
  RBAC when ambient role membership is expected to be the only source of power.
- **Hardcoded Authorization.** Hardcoded checks such as `if user.email in ...`
  conflict with RBAC because they hide policy in code and bypass audit tooling.

## 14. Refactoring path in and out

Introducing RBAC into code that does not have it.

1. Inventory protected operations. Name actions in verb-resource form, such as
   `invoice.read`, `invoice.approve`, and `invoice.refund`.
2. Find current checks. Include UI gates, route guards, database grants, batch
   jobs, admin scripts, and background workers.
3. Extract a single authorization function that receives subject, action,
   resource, and scope. At first it can call the old checks.
4. Replace direct user checks with permission checks. This is a narrow
   refactoring step: move from "is Alice" or "is admin" to "has action on
   resource".
5. Define initial roles from real job duties. Avoid one role per existing user.
   Start with read, write, administer, and domain-specific approval roles only
   where the business recognizes those duties.
6. Create assignment storage with scope. A role without scope becomes global by
   accident.
7. Add migration tooling that can show each subject's old effective access and
   new effective access. Do not cut over without comparing them.
8. Run dual evaluation. The old check makes the production decision while the
   new RBAC path logs would-allow and would-deny results.
9. Fix mismatches by changing roles or old checks, not by adding user-specific
   grants.
10. Flip enforcement one route or resource class at a time. Keep rollback clear.
11. Delete old checks after the RBAC path has logs, tests, and operational
   owners.

Named refactorings from the refactoring family often apply: Extract Function
for repeated authorization checks, Replace Conditional with Polymorphism when
resources own their permission mapping, Introduce Parameter Object for the
authorization request, Move Method when checks belong in a policy module, and
Inline Function when legacy wrappers stop adding value.

Removing RBAC when it no longer earns its place.

1. Confirm the access model has become object-specific, relationship-specific,
   or attribute-specific enough that roles are now labels around another model.
2. Add a new policy interface that can evaluate the target model beside RBAC.
3. Log both decisions for a release window and classify mismatches.
4. Move broad job permissions that still matter into platform roles, and move
   object-specific grants into ACLs, ReBAC, ABAC, or capabilities.
5. Freeze new role creation while migration runs.
6. Expire unused roles and remove assignments with no matching permission use.
7. Delete role checks only after no production decision depends on them.

## 15. Testing and verification

Engineering judgement: RBAC tests should prove both policy data and enforcement
placement. A correct role table is not enough if one route bypasses it.

Tests that become easier.

- **Permission matrix tests.** For each role, assert expected allow and deny
  decisions for representative actions and scopes.
- **Assignment tests.** A subject with one role receives its permissions, and a
  subject without that role does not.
- **Hierarchy tests.** A child or parent role relationship expands exactly once,
  terminates on cycles, and does not cross scope by accident.
- **Separation tests.** Conflicting roles cannot be assigned together for static
  separation of duty, or cannot be active in one session for dynamic separation
  of duty.
- **Regression tests for high-risk actions.** Deleting data, changing roles,
  impersonating users, exporting records, and reading secrets need explicit
  denial tests for ordinary roles.

Tests that become harder.

- The effective decision may come from several sources: direct assignment,
  identity provider group mapping, inherited role, scope inheritance, cached
  token claim, deny rule, or condition.
- Negative tests multiply. Every new role and resource needs a denial case, not
  only a happy path.
- UI tests can lie. A hidden button is not proof that the API denies the action.

Verification techniques.

- **Golden matrix.** Store a small table of roles, assignments, actions,
  resources, and expected decisions. Run it in unit tests and policy migration
  tests.
- **Property test.** For any subject, removing a role must not add access.
  Adding a role must not remove access unless a documented deny or dynamic
  constraint applies.
- **Scope isolation test.** The same role in tenant A must not grant access in
  tenant B.
- **Route coverage test.** Every protected route or command declares an action
  name and calls the authorization function.
- **Differential test during migration.** Compare legacy checks with RBAC
  checks and fail the rollout if high-risk mismatches appear.
- **Admin workflow test.** Create a role, assign it, observe allow, remove it,
  observe deny, and verify audit events for each step.

## 16. Observability signals

Engineering judgement: RBAC should be observable as a decision system, not only
as a set of tables.

Log or trace every protected decision at a rate suitable for the endpoint. The
event should include subject identifier, subject type, action, resource type,
resource scope, active roles, decision, reason code, policy version, request
identifier, and whether the decision came from cache. Do not log sensitive
resource values unless the audit policy permits them.

Useful metrics.

- Authorization decision count by action, role, resource type, scope, and
  allow-deny result.
- Deny rate by action and role. A spike after deployment often means a missing
  permission or a changed action name.
- Role assignment count by role and scope. Fast growth in one role points to
  role misuse or onboarding automation drift.
- Number of subjects with administrator or wildcard roles.
- Number of roles with no assignments, and assignments with no recent use.
- Policy evaluation latency, cache hit rate, and role expansion depth.
- Role definition changes by risk level.
- Break-glass activations, duration, and reviewer.

A healthy dashboard shows stable decision volume, low unexplained deny spikes,
few wildcard roles, no unused high-risk roles, shallow hierarchy, and policy
version rollout tied to deployment or change tickets. A failing dashboard shows
denials clustered on one new action, administrator assignment growth, role
definition churn, high cache staleness, or a long tail of roles with one user
each.

Audit logs should answer four questions without a database archaeology session:
who had the role, what the role meant at that time, which request used it, and
who changed the assignment or definition. Store role definitions with versions
so an old decision can be replayed against the policy that existed when the
request happened.

## 17. Security and privacy implications

RBAC closes one large attack surface: broad direct grants to individual
subjects. It replaces them with named, reviewable bundles. That helps audits,
offboarding, incident response, and least-privilege work. It also opens or
exposes several risks.

**Privilege escalation through role administration.** Any permission that can
create roles, edit roles, bind roles, or assume roles is high risk. A subject
with `role.assign` may be able to grant itself the power it lacks. Protect role
administration with separation of duty, approval, high-risk logging, and
break-glass limits.

**Confused deputy through assumable roles.** AWS IAM roles can be assumed and
return temporary security credentials for a role session
([AWS IAM roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html),
verified 2026-08-02). That is useful delegation, but it means trust policy and
caller identity become part of the authorization boundary. Model who can assume
which role as carefully as what the role can do.

**Overbroad inherited roles.** Role hierarchy can grant power far from the line
where a reviewer is looking. Keep hierarchy shallow, display expanded
permissions, and block cycles.

**Token disclosure.** If role names or permissions sit inside bearer tokens,
token theft becomes permission theft until expiration or revocation. Use short
lifetimes for sensitive roles and bind tokens to device or session context
where the platform supports it.

**Privacy leakage through role names.** A role such as
`vip-medical-reviewer-eu` may reveal customer class, business function, region,
or regulated data category in logs and tokens. Treat role names and audit logs
as access data. Limit retention and reader roles for authorization telemetry.

**Enumeration leaks.** Denied requests can reveal whether a resource exists if
the system returns different errors for "not found" and "forbidden". Pair RBAC
with object filtering and consistent response rules for sensitive resources.

**Policy supply chain.** Roles defined in YAML, Terraform, SQL migrations, or
admin APIs are production code. Review them, test them, scan for wildcards, and
require ownership metadata.

Where RBAC is silent. It does not authenticate users, classify data, encrypt
records, prevent SQL injection, sanitize output, or decide whether data should
be collected. It is an authorization pattern. It composes with those controls
but does not replace them.

## 18. References

1. David Ferraiolo and Richard Kuhn. "Role-Based Access Controls." Proceedings
   of the 15th National Computer Security Conference, 1992, pages 554 to 563.
   NIST publication page:
   https://csrc.nist.gov/pubs/conference/1992/10/13/rolebased-access-controls/final
   Verified 2026-08-02. Source for the first formal RBAC lineage.
2. NIST Computer Security Resource Center. "Role Based Access Control RBAC",
   project page.
   https://csrc.nist.gov/projects/role-based-access-control
   Verified 2026-08-02. Source for aliases, standard history, background, and
   primary references.
3. NIST Computer Security Resource Center. "Role Based Access Control RBAC",
   FAQ.
   https://csrc.nist.gov/Projects/role-based-access-control/faqs
   Verified 2026-08-02. Source for the three RBAC rules, RBAC0 through RBAC3,
   session activation, hierarchy, and separation-of-duty model components.
4. ANSI INCITS 359-2012. *Information Technology, Role-Based Access Control*.
   May 29, 2012. Cited through NIST's RBAC project page because the public
   standards page was verified there:
   https://csrc.nist.gov/projects/role-based-access-control
   Verified 2026-08-02.
5. Kubernetes documentation. "Using RBAC Authorization."
   https://kubernetes.io/docs/reference/access-authn-authz/rbac/
   Verified 2026-08-02. Source for Role, ClusterRole, RoleBinding, and
   ClusterRoleBinding production use and scope behavior.
6. Microsoft Learn. "What is Azure role-based access control (Azure RBAC)?"
   https://learn.microsoft.com/en-us/azure/role-based-access-control/overview
   Verified 2026-08-02. Source for Azure role assignments, scopes, additive
   evaluation, deny assignments, and conditions.
7. PostgreSQL Global Development Group. *PostgreSQL 16 Documentation*,
   Chapter 22, "Database Roles."
   https://www.postgresql.org/docs/16/user-manag.html
   Verified 2026-08-02. Source for database role production use.
8. GitLab documentation. "Roles and permissions."
   https://docs.gitlab.com/user/permissions/
   Verified 2026-08-02. Source for GitLab project and group role production
   use.
9. GitLab documentation. "Custom roles."
   https://docs.gitlab.com/user/custom_roles/
   Verified 2026-08-02. Source for GitLab custom role behavior.
10. AWS documentation. "IAM roles."
    https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html
    Verified 2026-08-02. Source for assumable IAM role behavior and temporary
    credentials.
11. AWS. "AWS Identity and Access Management FAQs."
    https://aws.amazon.com/iam/faqs/
    Verified 2026-08-02. Source for AWS's RBAC explanation using IAM roles.
12. Google Cloud documentation. "Roles and permissions."
    https://docs.cloud.google.com/iam/docs/roles-overview?authuser=0
    Verified 2026-08-02. Source for Google Cloud IAM role types and role as a
    permission collection.
13. Vincent C. Hu, David Ferraiolo, Richard Kuhn, Adam Schnitzer, Kenneth
    Sandlin, Robert Miller, Karen Scarfone. NIST SP 800-162, *Guide to
    Attribute Based Access Control (ABAC) Definition and Considerations*,
    January 2014, updated 2019.
    https://csrc.nist.gov/pubs/sp/800/162/upd2/final
    Verified 2026-08-02. Source for the ABAC comparison.
14. OASIS XACML Technical Committee. *XACML v3.0 Core and Hierarchical Role
    Based Access Control (RBAC) Profile Version 1.0*, Committee Specification
    02, edited by Erik Rissanen, October 23, 2014.
    https://docs.oasis-open.org/xacml/3.0/xacml-3.0-rbac-v1-spec-en.html
    Verified 2026-08-02. Source for the XACML RBAC profile variant.

## Code examples

Three languages are used because they show different deployment shapes.
TypeScript shows an application guard with scoped assignments. Python shows a
small policy object that is easy to unit test. Go shows a service-side
evaluator with explicit structs and no framework dependency. Java, Rust, and
Swift are omitted to keep the examples focused on common RBAC host environments
for web services and control-plane code.

### TypeScript

```typescript
type Action = "invoice:read" | "invoice:approve" | "invoice:refund";

type Permission = {
  action: Action;
  scope: string;
};

type Role = {
  name: string;
  permissions: Permission[];
};

type Assignment = {
  subject: string;
  role: string;
  scope: string;
};

const roles: Record<string, Role> = {
  viewer: {
    name: "viewer",
    permissions: [{ action: "invoice:read", scope: "tenant" }],
  },
  approver: {
    name: "approver",
    permissions: [
      { action: "invoice:read", scope: "tenant" },
      { action: "invoice:approve", scope: "tenant" },
    ],
  },
};

const assignments: Assignment[] = [
  { subject: "sara", role: "approver", scope: "tenant-a" },
  { subject: "li", role: "viewer", scope: "tenant-b" },
];

function can(subject: string, action: Action, tenant: string): boolean {
  return assignments
    .filter((item) => item.subject === subject && item.scope === tenant)
    .some((item) =>
      roles[item.role].permissions.some(
        (permission) =>
          permission.action === action && permission.scope === "tenant",
      ),
    );
}

console.log(can("sara", "invoice:approve", "tenant-a"));
console.log(can("li", "invoice:approve", "tenant-b"));
```

### Python

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Permission:
    action: str
    scope: str


@dataclass(frozen=True)
class Role:
    name: str
    permissions: frozenset[Permission]


@dataclass(frozen=True)
class Assignment:
    subject: str
    role: str
    scope: str


class Rbac:
    def __init__(self, roles: dict[str, Role], assignments: list[Assignment]):
        self.roles = roles
        self.assignments = assignments

    def can(self, subject: str, action: str, scope: str) -> bool:
        for assignment in self.assignments:
            if assignment.subject != subject or assignment.scope != scope:
                continue
            role = self.roles[assignment.role]
            if Permission(action, "tenant") in role.permissions:
                return True
        return False


roles = {
    "viewer": Role("viewer", frozenset({Permission("invoice:read", "tenant")})),
    "approver": Role(
        "approver",
        frozenset(
            {
                Permission("invoice:read", "tenant"),
                Permission("invoice:approve", "tenant"),
            }
        ),
    ),
}

rbac = Rbac(
    roles,
    [
        Assignment("sara", "approver", "tenant-a"),
        Assignment("li", "viewer", "tenant-b"),
    ],
)

print(rbac.can("sara", "invoice:approve", "tenant-a"))
print(rbac.can("li", "invoice:approve", "tenant-b"))
```

### Go

```go
package main

import "fmt"

type Permission struct {
	Action string
	Scope  string
}

type Role struct {
	Name        string
	Permissions []Permission
}

type Assignment struct {
	Subject string
	Role    string
	Scope   string
}

type Rbac struct {
	Roles       map[string]Role
	Assignments []Assignment
}

func (r Rbac) Can(subject, action, scope string) bool {
	for _, assignment := range r.Assignments {
		if assignment.Subject != subject || assignment.Scope != scope {
			continue
		}
		role := r.Roles[assignment.Role]
		for _, permission := range role.Permissions {
			if permission.Action == action && permission.Scope == "tenant" {
				return true
			}
		}
	}
	return false
}

func main() {
	roles := map[string]Role{
		"viewer": {
			Name: "viewer",
			Permissions: []Permission{
				{Action: "invoice:read", Scope: "tenant"},
			},
		},
		"approver": {
			Name: "approver",
			Permissions: []Permission{
				{Action: "invoice:read", Scope: "tenant"},
				{Action: "invoice:approve", Scope: "tenant"},
			},
		},
	}

	rbac := Rbac{
		Roles: roles,
		Assignments: []Assignment{
			{Subject: "sara", Role: "approver", Scope: "tenant-a"},
			{Subject: "li", Role: "viewer", Scope: "tenant-b"},
		},
	}

	fmt.Println(rbac.Can("sara", "invoice:approve", "tenant-a"))
	fmt.Println(rbac.Can("li", "invoice:approve", "tenant-b"))
}
```
