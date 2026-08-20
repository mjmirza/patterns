---
name: Attribute-Based Access Control
slug: abac
family: 15-security
category: Authorization
aliases: [ABAC, Attribute Based Access Control, Policy-Based Access Control]
first_described: "NIST SP 800-162 2014"
maturity: established
related: [rbac, policy-enforcement-point, policy-decision-point, zero-trust-architecture, federated-identity]
incompatible_with: [hard-coded-authorization, ambient-authority]
verified: 2026-08-02
---

# Attribute-Based Access Control

## 1. Name, aliases, and lineage

The canonical name is Attribute-Based Access Control, usually shortened to
ABAC. The spelling without the hyphen, Attribute Based Access Control, appears
in NIST SP 800-162, *Guide to Attribute Based Access Control (ABAC) Definition
and Considerations*, by Vincent Hu, David Ferraiolo, Richard Kuhn, Adam
Schnitzer, Kenneth Sandlin, Robert Miller, and Karen Scarfone. NIST published
that special publication in January 2014 and lists an update history through
August 2, 2019. The NIST abstract defines ABAC as a logical access control
methodology where authorization is decided by evaluating subject, object,
operation, and sometimes environment attributes against policy, rules, or
relationships that describe allowed operations, URL
https://csrc.nist.gov/pubs/sp/800/162/upd2/final, verified 2026-08-02.

The closest older standard lineage is XACML. OASIS approved eXtensible Access
Control Markup Language Version 3.0 as an OASIS Standard on January 22, 2013.
Its model separates policy enforcement, policy decision, attributes, policies,
combining algorithms, obligations, and advice. The XACML core specification
names subject, resource, action, and environment attribute categories and
defines request attributes, decisions, and attribute evaluation rules. OASIS,
*eXtensible Access Control Markup Language (XACML) Version 3.0*, edited by Erik
Rissanen, sections 2, 3, 5.44 through 5.48, 7.2, 7.3, and 9, URL
https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-en.html, verified
2026-08-02.

ABAC is also called policy-based access control when the speaker wants to stress
the separated policy layer rather than the attribute model. That alias is
useful, but imprecise. RBAC can be policy-based, and relationship-based access
control can be policy-based too. In this entry ABAC means decisions whose rules
read attributes from the principal, the resource, the requested action, and the
request context.

Judgement. Treat ABAC as an authorization architecture pattern, not as a single
library pattern. A small function can implement an ABAC rule, but the pattern is
the whole decision flow: collect trusted attributes, evaluate them with policy,
return a decision, and enforce that decision at the resource boundary.

## 2. Problem and context

Authorization starts simple. A user has a role, a resource has an owner, and the
application checks whether the role or owner permits the action. That model
works while the number of products, regions, tenants, labels, data classes, and
workflow states stays small. It begins to fail when access depends on many facts
that change outside the role table.

The problem usually arrives as a pile of special cases. A user in the finance
department may read finance reports, but only reports for their region. A
contractor may update tickets, but not tickets marked confidential. A support
engineer may open a customer record during an active incident, but only from a
managed device and only after a ticket number is present. A service account may
copy an object when the resource tag matches the session tag, unless the object
has a higher classification. None of these decisions is naturally a new role.
If every combination becomes a role, the role catalog turns into a matrix of
department, region, project, data class, employment type, duty status, and
network state.

ABAC exists for the context where authorization depends on facts already present
in identity, resource metadata, request metadata, and environment telemetry.
AWS IAM documents ABAC as a strategy that defines permissions based on
attributes, represented in AWS as tags on IAM resources and AWS resources. AWS
also describes policies that compare a principal tag with a resource tag, URL
https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction_attribute-based-access-control.html,
verified 2026-08-02. Google Cloud IAM Conditions says conditions can define and
enforce conditional, attribute-based access control for Google Cloud resources,
with attributes such as resource type, resource name, tags, timestamp, and
destination IP address, URL
https://docs.cloud.google.com/iam/docs/conditions-overview?hl=en, verified
2026-08-02. Microsoft Learn describes Azure ABAC as access based on attributes
associated with security principals, resources, and the request environment,
implemented through role assignment conditions for Azure RBAC, URL
https://learn.microsoft.com/en-us/azure/role-based-access-control/conditions-overview,
verified 2026-08-02.

The key context is not "many permissions." RBAC handles many permissions well
when they cluster by job function. The key context is "many changing facts that
belong to different owners." Identity owns employment type and department.
Storage owns object tags. Networking owns private link state. The workflow
system owns incident status. ABAC lets a policy combine those facts without
copying them all into a role assignment table.

ABAC is most useful when the system has an enforceable attribute vocabulary.
Without that vocabulary, it becomes a string comparison engine over untrusted
metadata. A tag named `project` means little unless there is a creator, allowed
value set, owner, propagation path, and audit trail. NIST SP 800-162 discusses
ABAC in terms of attributes for subjects, objects, operations, and environment
conditions, which is the minimum inventory a design needs before the first rule
is written, URL https://csrc.nist.gov/pubs/sp/800/162/upd2/final, verified
2026-08-02.

## 3. Forces

Judgement. This section weighs engineering pressures that appear in ABAC
systems. The sources cited elsewhere define the models and products, but the
choice among forces depends on the system.

- **Expressiveness.** Favoured. ABAC can represent policies that combine
  identity facts, resource labels, action names, time, network facts, device
  facts, and workflow state. This is the main reason to adopt it.
- **Coupling.** Favoured at the application boundary. Application code asks for
  a decision instead of hard-coding every authorization branch. Coupling moves
  to the attribute schema and policy language.
- **Consistency.** Mixed. Central policy evaluation can make decisions uniform
  across services. Consistency falls when services compute the same attribute in
  different ways or use stale copies.
- **Latency.** Sacrificed. A decision may need attribute lookup, policy parsing,
  policy matching, and sometimes a network call to a decision service. Local
  caching helps, but stale attributes can change the answer.
- **Operability.** Sacrificed unless designed. A deny can be caused by a
  missing attribute, stale identity claim, resource tag typo, policy precedence
  rule, combining algorithm, or enforcement bug. Operators need decision traces,
  policy identifiers, and attribute snapshots.
- **Cost.** Mixed. ABAC can reduce policy count and role count, as AWS and Azure
  both describe for tag and condition based access. It can also create new cost
  in policy tooling, schema ownership, attribute pipelines, and audit review.
- **Team topology.** Favoured when platform teams own the decision engine and
  domain teams own attributes with clear contracts. Sacrificed when no team owns
  the cross-service attribute vocabulary.
- **Cognitive load.** Sacrificed. A role named `BillingAdmin` is easy to read.
  A policy combining department, classification, project tag, device posture,
  and clock time requires readers to know the policy language and the source of
  every attribute.
- **Change speed.** Favoured for resource growth. When new resources carry the
  right attributes, existing policy can cover them without a new role or rule
  per resource. Sacrificed for schema changes, because a renamed attribute can
  break many policies at once.
- **Auditability.** Mixed. A decision log can explain ABAC in detail. A static
  permissions review is harder because access is a function of runtime facts,
  not a fixed list of grants.

ABAC pays for expressiveness with a policy and data governance burden. The
pattern is worthwhile when that burden is lower than managing the equivalent
role or access-control-list explosion.

## 4. Applicability and non-applicability

Reach for ABAC when these conditions hold.

- Access depends on attributes of the subject, resource, action, and request
  context, not only on group membership or ownership.
- Resource creation is frequent, and new resources can be tagged or labelled at
  creation time.
- Access rules must follow business facts such as project, data class, region,
  tenancy, employment status, duty status, or network path.
- The platform can provide a trusted decision point or a small in-process policy
  engine, with decision logs and test fixtures.
- The organization has owners for attribute schema, allowed values, attribute
  issuance, and resource metadata quality.
- Several services need the same authorization logic, and duplicating branches
  in every service has already caused drift.
- Federation is in place or planned, and identity attributes can be transmitted
  as signed claims or session tags.
- Policy authors need to express conditional denies, break-glass exceptions, or
  contextual restrictions that RBAC alone cannot represent cleanly.

Non-applicability. Do NOT reach for ABAC in these cases.

- **The rule is a stable job function.** Use RBAC when `Admin`, `Editor`, and
  `Viewer` cover the model and the resource set is small. ABAC adds a policy
  language and attribute governance without earning them.
- **The resource count is tiny and hand-owned.** Use an ACL or ownership check
  for a small set of named resources. Attribute policy will hide a simple rule.
- **Attributes are user-controlled strings.** Do not authorize directly on data
  the principal can edit. A user profile field named `department` is not a
  security attribute unless an authority issues it and protects it.
- **No team owns metadata quality.** ABAC fails closed or fails open depending
  on local defaults when tags are missing. Both outcomes become noisy if
  resource metadata is incomplete.
- **Decisions must be explained to nontechnical reviewers without tooling.** A
  role assignment report is easier to review than a policy over dynamic facts.
  ABAC can be audited, but only with decision replay and attribute snapshots.
- **Low-latency hot paths cannot afford policy evaluation.** A storage engine
  or packet path may need precomputed capabilities or a local table. ABAC can
  still mint those grants offline, but should not sit in the hot loop.
- **The policy language is too powerful for the authoring model.** If policy
  authors can write arbitrary code or unbounded expressions, authorization
  becomes a runtime failure source. Prefer a constrained rule format.
- **The main relationship is graph-shaped.** Use relationship-based access
  control when the answer depends on paths such as owner, parent, member, and
  delegate. ABAC can reference relationship attributes, but it is not a graph
  traversal model.
- **The application cannot enforce at every resource boundary.** ABAC decisions
  are advisory until a policy enforcement point gates the actual operation.
  Hidden bypass paths defeat the pattern.
- **Attribute changes must revoke access instantly across offline clients.** A
  cached token with embedded attributes may outlive the fact it represents.
  Short tokens, revocation, or online checks are required.

## 5. Structure

ABAC has six core participants.

- **Policy Enforcement Point.** The code at the resource boundary. It intercepts
  the attempted operation, builds an authorization request, asks for a decision,
  and blocks or permits the operation. XACML uses the term policy enforcement
  point and describes base, deny-biased, and permit-biased PEP behavior in
  section 7.2, URL
  https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-en.html,
  verified 2026-08-02.
- **Policy Decision Point.** The evaluator. It receives the request attributes,
  locates applicable policy, evaluates expressions, applies combining rules,
  and returns permit, deny, not applicable, or an error-shaped outcome. XACML
  section 5.47 describes the response element and section 5.48 describes the
  result element, URL
  https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-en.html,
  verified 2026-08-02.
- **Attribute Authorities.** Systems trusted to issue attributes. Examples are
  an identity provider for department and employment type, a device service for
  managed-device posture, a storage service for resource tags, and a workflow
  system for incident state.
- **Attribute Bag.** The normalized set of facts used for one decision. XACML
  section 7.3.2 uses the term bag for a collection of same-typed values, and
  section 7.3.3 covers multivalued attributes, URL
  https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-en.html,
  verified 2026-08-02.
- **Policy Store.** The versioned policy source. It may be a file, database,
  cloud policy store, Git repository, or configuration service. Amazon Verified
  Permissions documents a policy store as a concept for managing policies, URL
  https://docs.aws.amazon.com/verifiedpermissions/latest/userguide/terminology.html,
  verified 2026-08-02.
- **Decision Log.** The audit record for one evaluation. It should contain the
  principal identifier, action, resource identifier, policy version, result,
  matched policy identifiers, and enough attribute values to explain the
  decision within privacy limits.

Relationships. The enforcement point must sit before the resource operation.
The decision point must receive attributes from trusted authorities or from a
verified request context. The policy store must version policy, because a
decision is meaningful only with the policy version that produced it. The
decision log must not become a second sensitive data store by recording
unbounded resource contents or personal data.

## 6. ASCII structure diagram

```text
  +------------------+      authz request       +------------------+
  | Application PEP  |------------------------->|       PDP        |
  | resource gate    |                          | policy evaluator |
  +--------+---------+                          +---+----------+---+
           |                                        |          |
           | permit or deny                         | reads    | reads
           v                                        v          v
  +------------------+                      +------------+ +------------+
  | Protected        |                      | Policy     | | Attribute  |
  | resource action  |                      | store      | | authorities|
  +------------------+                      +------------+ +------------+
           ^
           |
           | decision event
           |
  +------------------+
  | Decision log     |
  | result, attrs,   |
  | policy version   |
  +------------------+

  PEP. Policy Enforcement Point.
  PDP. Policy Decision Point.
```

## 7. Dynamics

The runtime flow starts before the protected action executes. The enforcement
point identifies the principal, action, resource, and contextual facts. It then
builds a request for the decision point. The decision point fetches or receives
attributes, evaluates applicable policy, returns a decision, and the
enforcement point gates the operation.

```text
Client        PEP          Attribute sources       PDP        Resource
  |            |                   |                 |             |
  |-- action ->|                   |                 |             |
  |            |-- get subject --->|                 |             |
  |            |<-- attributes ----|                 |             |
  |            |-- get resource -->|                 |             |
  |            |<-- attributes ----|                 |             |
  |            |-- decision request ---------------->|             |
  |            |                   |                 |-- policy -->|
  |            |                   |                 |<-- match ---|
  |            |<-- permit/deny, obligations --------|             |
  |            |-- write decision log -------------->|             |
  |            |                                                 |
  |            |-- if permit, perform action ------------------->|
  |<-- result -|                                                 |
  |            |                                                 |
```

Three details make or break this flow.

First, the enforcement point must fail closed for missing decisions. XACML
distinguishes several decision results, including Permit, Deny, NotApplicable,
and Indeterminate in its decision model. An application that treats an error or
NotApplicable as Permit has turned policy absence into access, URL
https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-en.html, verified
2026-08-02.

Second, attribute freshness must match risk. A project tag on an object may be
stable enough to read from the resource record. A user's employment status may
need short token lifetimes or online lookup. Device posture may expire in
minutes. ABAC does not choose those lifetimes for you.

Third, obligations must be enforced by the enforcement point, not by the
decision point. XACML section 5.47 says a PEP must deny access when obligations
accompany a decision and the PEP does not understand them or cannot discharge
them, URL
https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-en.html, verified
2026-08-02. In engineering terms, a decision of "permit if you redact column X"
is a deny unless the caller can actually redact column X.

## 8. Implementation variants

**Tag equality ABAC.** A policy compares principal tags with resource tags. AWS
IAM documents this shape through policies that allow access when principal and
resource tag values match, URL
https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction_attribute-based-access-control.html,
verified 2026-08-02. It is easy to explain and scales with new tagged resources.
It is weak for rules that need hierarchy, numeric comparison, or temporal
conditions.

**Role plus condition ABAC.** A role grant names the coarse permission, and a
condition narrows it. Azure ABAC is documented as adding role assignment
conditions to Azure RBAC, with conditions that filter permissions granted by a
role assignment, URL
https://learn.microsoft.com/en-us/azure/role-based-access-control/conditions-overview,
verified 2026-08-02. This variant preserves simple role reasoning for broad
access and uses ABAC where detail matters.

**Policy language ABAC.** Policies are written in a language with expressions
over principal, action, resource, and context. Cedar, used by Amazon Verified
Permissions, supports policy conditions that reference attributes of the
principal and can combine RBAC and ABAC in one policy, URL
https://docs.aws.amazon.com/verifiedpermissions/latest/userguide/terminology.html,
verified 2026-08-02. OPA documents ABAC as decisions using attributes of users,
objects, and actions, with logic describing allowed combinations, URL
https://www.openpolicyagent.org/docs/comparisons/access-control-systems,
verified 2026-08-02. This variant is expressive and testable, but policy author
tooling becomes part of the product.

**Inline code ABAC.** The application evaluates typed predicates in code, often
as small functions over an authorization request. This works well inside a
single service where policy changes follow deployments. It is poor when auditors
or administrators need to change policy without a code release.

**External PDP ABAC.** Services call a central decision service. This improves
policy uniformity and audit visibility. It adds network latency and a new
availability dependency. Caching decisions reduces latency but raises freshness
questions.

**Token-embedded ABAC.** Identity attributes travel in a signed token or session
tag, and the service evaluates policy locally. This reduces lookup cost and
fits federated access. The risk is stale attributes, overlarge tokens, and
confusing authentication claims with authorization facts.

**Resource-local ABAC.** The storage or database layer enforces policy from
resource labels and session attributes. This is strong when all access goes
through that layer. It is weak when side paths can read the same data without
the enforcement point.

## 9. Known production uses

**AWS IAM.** AWS IAM documents ABAC as a permissions strategy based on
attributes called tags, including IAM resource tags, AWS resource tags, and
session tags. The documentation gives the pattern of allowing operations when a
principal tag matches a resource tag. AWS IAM User Guide, "Define permissions
based on attributes with ABAC authorization", URL
https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction_attribute-based-access-control.html,
verified 2026-08-02.

**Google Cloud IAM Conditions.** Google Cloud documents IAM Conditions as a way
to define and enforce conditional, attribute-based access control for Google
Cloud resources. The page says conditions can be used in allow policy role
bindings, deny policy rules, and principal access boundary policy bindings, and
it lists condition attributes such as resource type, resource name, resource
tags, timestamp, and destination IP address. Google Cloud IAM documentation,
"Overview of IAM Conditions", URL
https://docs.cloud.google.com/iam/docs/conditions-overview?hl=en, verified
2026-08-02.

**Azure ABAC.** Microsoft documents Azure ABAC as an authorization system based
on attributes associated with security principals, resources, and the request
environment. It builds on Azure RBAC through role assignment conditions and is
documented for Azure Storage data actions such as Blob Storage and Queue
Storage. Microsoft Learn, "What is Azure attribute-based access control
(Azure ABAC)?", URL
https://learn.microsoft.com/en-us/azure/role-based-access-control/conditions-overview,
verified 2026-08-02.

**Amazon Verified Permissions and Cedar.** Amazon Verified Permissions
documents principal, action, resource, and context concepts and states that
Cedar can support ABAC decisions through policy conditions that reference
principal attributes. It also states that Cedar can combine RBAC and ABAC in a
single policy. Amazon Verified Permissions User Guide, "Terms and concepts",
URL https://docs.aws.amazon.com/verifiedpermissions/latest/userguide/terminology.html,
verified 2026-08-02.

**Open Policy Agent.** OPA documents ABAC as one of the access control systems
it supports, using user attributes, object attributes, and action attributes
with logic that dictates allowed combinations. Open Policy Agent documentation,
"Access Control Systems", URL
https://www.openpolicyagent.org/docs/comparisons/access-control-systems,
verified 2026-08-02.

## 10. Consequences

Judgement. These consequences are recurring engineering outcomes. Their size
depends on policy count, attribute quality, and enforcement coverage.

Positive.

- ABAC keeps roles from multiplying by every project, region, classification,
  device state, and incident state.
- New resources can become accessible by carrying the right attributes, without
  editing a permission list per resource.
- Policy can express conditions that are closer to business language than a
  table of opaque grants.
- Enforcement can be centralized while attributes remain owned by the systems
  that know them best.
- Decision logs can explain why an access request was permitted or denied, if
  the design records policy version and relevant attributes.
- Federation fits the model, because signed identity assertions and session
  tags can carry subject attributes into the decision.
- Least privilege can be expressed with narrower predicates than broad roles.

Negative.

- Attribute governance becomes part of security. A missing tag can be as severe
  as a bad role assignment.
- Policy readers must understand the source and freshness of each attribute.
- A central decision service can add latency and availability risk.
- Local policy engines can drift if policy bundles, schemas, or helper
  functions are not versioned together.
- Audit review is harder than reading a static role table, because access
  depends on runtime facts.
- Debugging denial is harder. The cause may be a policy bug, an attribute bug,
  a stale token, or an enforcement path issue.
- ABAC can hide too much power in generic policy expressions. Without authoring
  limits, a policy store becomes a programming platform.

## 11. Failure modes and misuse

Judgement. Each item below is written as Symptom, Cause, Fix because ABAC faults
are often visible first as strange deny or permit behavior rather than as a
clear exception.

**Missing resource attribute.** Symptom. New resources deny access for every
user, while older resources work. Cause. The create path did not write the tag
or label used by policy. Fix. Make attribute assignment part of resource
creation, add a migration for existing resources, and add a deny reason for
missing attributes.

**User-controlled attribute grant.** Symptom. A user gains access after editing
their own profile, team name, or project field. Cause. Policy trusted an
attribute not issued by an authority. Fix. Split display profile data from
security attributes, and accept authorization attributes only from protected
identity or admin systems.

**Stale token access.** Symptom. A removed employee or transferred user keeps
access until their session expires. Cause. Subject attributes were embedded in a
long-lived token. Fix. Shorten token life for attributes that affect access,
add revocation for high-risk cases, or perform online lookup for those fields.

**Policy drift across services.** Symptom. Service A permits an action that
Service B denies for the same principal and resource. Cause. Services ship
different policy bundles or helper functions. Fix. Version policy bundles,
publish a shared conformance suite, and log policy version on every decision.

**Permit on policy miss.** Symptom. Unknown actions or new resource types are
allowed in production before policy is written. Cause. The enforcement point
treats NotApplicable, missing policy, or evaluation error as permit. Fix. Make
the enforcement point deny by default and require an explicit allow.

**Attribute name collision.** Symptom. A policy that was meant for project tags
starts reading a user-defined metadata field with the same name. Cause. The
schema lacks namespaces or issuer checks. Fix. Use namespaced attribute keys
and record the authority or issuer for each security attribute.

**Overbroad break-glass rule.** Symptom. Incident responders can read resources
outside the incident scope. Cause. The emergency rule checks duty status but not
ticket, tenant, resource class, or time. Fix. Require an incident identifier,
scope binding, expiration, and high-signal audit event.

**Unbounded policy expression.** Symptom. Authorization latency spikes when a
new policy deploys. Cause. The policy language permits expensive loops, regexes,
external calls, or large set scans. Fix. Use a constrained language, precompile
policy, cap input sizes, and reject policies that exceed evaluation limits.

**Decision log leaks data.** Symptom. Audit logs contain sensitive resource
content or personal data copied from attributes. Cause. The decision log stores
full requests rather than selected fields. Fix. Log identifiers, policy IDs,
decision reasons, and redacted attribute summaries.

**Side-path bypass.** Symptom. The API denies access, but a batch job, export
path, or admin endpoint can still read the resource. Cause. ABAC was added to
one enforcement point, not to the resource boundary. Fix. Move enforcement
closer to the resource or add a shared gateway used by every path.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | ABAC | RBAC | ACL | ReBAC | Capability token | Hard-coded checks |
|---|---|---|---|---|---|---|
| Expressiveness | High for attributes and context | Medium for job functions | Low to medium for named grants | High for graph relationships | Medium for delegated rights | Whatever code allows |
| Coupling | Low in app code, high in schema | Low when roles are stable | High to resource records | High to relationship graph | Low after token minting | High to each service |
| Consistency | Strong with one PDP | Strong with one role store | Weak across many resources | Strong with one graph | Strong until token expiry | Weak across codebases |
| Latency | Medium cost from evaluation | Low lookup cost | Low lookup cost | Medium to high graph cost | Very low at use time | Very low |
| Operability | Needs decision traces | Easy role reports | Easy per-resource lists | Needs graph explanation | Needs token audit | Hard to audit globally |
| Cost of change | Low for new tagged resources | Low for job changes | High for bulk changes | Low for relationship changes | Medium, minting path changes | High, deploy needed |
| Team topology | Works with attribute owners | Works with identity teams | Works with resource owners | Works with graph owners | Works with issuer owners | Fragments by service |
| Cognitive load | High | Low to medium | Low | Medium to high | Medium | Low locally, high globally |
| Auditability | Strong with replay tools | Strong | Strong for small sets | Strong with path traces | Medium | Weak |
| Best fit | Contextual access | Job function access | Small resource lists | Ownership and sharing graphs | Delegation and offline use | Small prototypes |

Reading of the table. ABAC is the strongest fit when many changing facts decide
access. RBAC wins when roles map cleanly to duties. ACLs win when a resource
owner edits a small list. ReBAC wins when relationships such as owner, parent,
member, delegate, and viewer are the real model. Capability tokens win when
rights must be passed to another actor or used offline. Hard-coded checks are
acceptable only when the rule is local, small, and unlikely to spread.

## 13. Related and incompatible patterns

- **RBAC.** ABAC often composes with RBAC rather than replacing it. A role can
  grant broad action rights, and ABAC conditions can narrow those rights by
  resource tag, time, network, or data class. Azure documents this hybrid shape
  through role assignment conditions on Azure RBAC, URL
  https://learn.microsoft.com/en-us/azure/role-based-access-control/conditions-overview,
  verified 2026-08-02.
- **Policy Enforcement Point and Policy Decision Point.** These are structural
  partners. ABAC without a PEP is a recommendation. ABAC without a PDP is
  scattered code.
- **Federated Identity.** Composes well when identity providers issue signed
  attributes or session tags. AWS IAM documents SAML or OIDC providers passing
  session tags that IAM can use in ABAC policies, URL
  https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction_attribute-based-access-control.html,
  verified 2026-08-02.
- **ReBAC.** Sometimes replaces ABAC. If the policy asks whether a user is an
  owner, parent, editor through a group, or delegate through a chain, use a
  relationship graph. ABAC can still apply conditions around the graph result.
- **Capability Token.** Composes when ABAC mints a narrow right that another
  service later verifies. The token should carry scope, expiry, audience, and
  issuer, not raw unrestricted attributes.
- **Zero Trust Architecture.** Composes at the policy level. Device posture,
  network path, user state, and resource sensitivity are natural ABAC
  attributes.
- **Ambient Authority.** Conflicts. ABAC depends on explicit subject, resource,
  action, and context. A global current user or process-wide admin flag hides
  the facts policy needs.
- **Hard-coded Authorization.** Conflicts once rules spread. A copied branch in
  service code bypasses policy versioning, decision logs, and central review.

## 14. Refactoring path in and out

Introducing ABAC into code that does not have it.

1. Inventory current authorization checks. Group them by subject facts, resource
   facts, action names, and context facts. Do not start with a policy language.
2. Define an authorization request type with principal, action, resource, and
   context fields. Keep it small enough to log safely.
3. Extract one repeated check into a named predicate over that request type.
   This is Extract Function from the refactoring family.
4. Replace call-site branches with a call to a local decision function. At this
   stage the rule can remain in code.
5. Add decision logging with result, reason, action, resource type, policy
   version, and redacted attribute summary.
6. Add contract tests for missing attributes, stale attributes, and wrong
   resource labels.
7. Move policies out of code only after there are enough rules or enough
   non-developer authors to justify a policy store.
8. Add schema validation for attribute names, types, issuers, and allowed
   values. Reject policies that reference unknown attributes.
9. Roll out in shadow mode. Compare old and new decisions in logs without
   enforcing the new decision. Investigate mismatches.
10. Flip enforcement per action or resource class, not globally. Keep rollback
   simple and observable.

Removing ABAC when it stops earning its place.

1. Use decision logs to find policies that always evaluate the same way for a
   broad group. Those are role candidates.
2. Replace attribute predicates that match stable job functions with RBAC roles.
3. Replace resource-specific attribute rules over a tiny resource set with ACLs
   if resource owners manage access directly.
4. Replace graph-like attribute rules with ReBAC when policies simulate owner,
   parent, group, or delegate paths.
5. Inline one local predicate at a time only after the central policy no longer
   serves any other service. This is Inline Function from the refactoring
   family.
6. Remove unused attributes from tokens and logs after policy no longer reads
   them. This prevents dead security data from becoming accidental authority.
7. Delete policy rules and schema entries in the same change, then replay saved
   authorization fixtures to confirm equivalent decisions.

## 15. Testing and verification

Judgement. ABAC testing must cover policy logic and attribute production. A
perfect policy still fails when the tag writer, identity mapper, or enforcement
point is wrong.

What becomes easier.

- Policy predicates can be tested as pure functions over a request object.
- Missing-attribute cases are easy to name and assert.
- Boundary conditions such as clearance level, expiry time, and network source
  can be table-driven.
- Policy bundles can be replayed against decision fixtures from production logs
  after redaction.

What becomes harder.

- End-to-end tests need trusted attribute sources or realistic fakes.
- A test must say whether an attribute is absent, unknown, empty, stale, or
  present with a false value.
- Policy order and combining rules need fixtures. A single allow fixture is not
  enough.
- Audit expectations must be tested, because logs are part of the security
  control.

Techniques that apply.

- **Decision table tests.** Create a table of subject attributes, resource
  attributes, action, context, expected decision, and expected reason.
- **Property tests for monotonicity.** For policies based on clearance,
  increasing subject clearance should not turn a permit into a deny unless an
  explicit separation-of-duty rule says so.
- **Mutation tests for policy.** Flip comparison operators or remove one
  conjunct and verify tests fail. This catches weak allow-only suites.
- **Schema contract tests.** Verify every policy attribute exists in the schema,
  has one type, has an issuer, and has a documented freshness target.
- **Shadow-mode replay.** Send real requests to the new PDP but enforce the old
  path. Compare decisions and investigate mismatches before launch.
- **PEP bypass tests.** Attempt access through API, batch, export, admin, and
  internal worker paths. Every path should hit the same authorization boundary
  or a stricter one.

## 16. Observability signals

Judgement. ABAC needs observability because the source code no longer contains
the whole answer. The most useful dashboard answers three questions: what was
decided, which policy decided it, and which attributes mattered.

Record these fields for each decision, with privacy review.

- Decision result: permit, deny, not applicable, or error.
- Principal identifier and principal type, with pseudonymization where needed.
- Action and resource type.
- Resource identifier, or a stable hash when the identifier is sensitive.
- Policy bundle version and matched policy IDs.
- Attribute schema version.
- Missing attribute names.
- Attribute issuer names, not only values.
- Decision latency and attribute lookup latency.
- Enforcement outcome, including whether obligations were applied.

Healthy signals.

- Deny rate is stable by action and resource class.
- NotApplicable and evaluation-error counts are near zero for known actions.
- Policy bundle versions converge across services after deployment.
- Missing attribute counts fall after resource creation fixes.
- Decision latency is small compared with the protected operation.
- Shadow-mode mismatch rate trends to zero before enforcement.

Failing signals.

- A spike in NotApplicable after a deploy means new actions or resource types
  lack policy.
- A spike in missing resource tags points to a creation or migration defect.
- One service using an old policy bundle explains cross-service decision drift.
- A sudden permit-rate jump after a policy change deserves security review even
  when no errors are logged.
- High decision latency on one policy ID points to expensive expressions or slow
  attribute lookup.
- Decision logs without policy version are not useful for incident review.

## 17. Security and privacy implications

ABAC closes some access-control gaps and opens others.

Security benefits.

- ABAC can express least privilege using real request facts rather than broad
  roles.
- It can restrict access by resource sensitivity, tenant, project, network
  path, device posture, time, and workflow state.
- It can reduce standing privilege by making emergency access depend on duty
  status, ticket scope, and expiry.
- It can centralize deny logic so that the same restriction applies across
  services.

Security risks.

- Attribute forgery is the main risk. Every attribute used for authorization
  needs an issuer, integrity protection, and a review path.
- Attribute staleness can preserve access after a real-world change. Token
  lifetime and cache lifetime are security parameters.
- Policy mistakes can affect many resources at once. The blast radius is larger
  than a single ACL edit.
- Policy languages can become code execution surfaces if they permit external
  calls, unsafe functions, or unbounded evaluation.
- Logs can leak sensitive attributes. A classification label may be harmless,
  while diagnosis, citizenship, customer name, or investigation status may not
  be.
- Attribute inference is a privacy issue. A deny reason that says "resource is
  under investigation" may reveal more than the caller should know.

Controls.

- Keep security attributes separate from user-editable profile fields.
- Namespace attributes by authority and domain.
- Validate policy against schema before deployment.
- Deny by default on missing policy, missing required attribute, or PDP error.
- Sign tokens that carry attributes, and set lifetimes by attribute risk.
- Redact decision logs and store high-sensitivity values as hashes or reason
  codes.
- Require review for policies that broaden access or weaken deny rules.
- Test every enforcement path, not only the public API.

## Code examples

The examples below are intentionally small. They show ABAC as typed predicates
over a request object, which is the core shape before a policy language or
external PDP is introduced. Python, Go, and Rust were compiled or run locally.
Java was attempted, but the sandbox could not locate a Java runtime.

Python.

```python
from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class Subject:
    department: str
    clearance: int
    on_call: bool

@dataclass(frozen=True)
class Resource:
    department: str
    classification: int
    owner: str

@dataclass(frozen=True)
class Request:
    subject: Subject
    action: str
    resource: Resource
    hour: int

Policy = Callable[[Request], bool]

def same_department(req: Request) -> bool:
    return req.subject.department == req.resource.department

def has_clearance(req: Request) -> bool:
    return req.subject.clearance >= req.resource.classification

def incident_override(req: Request) -> bool:
    return req.action == "read" and req.subject.on_call and 0 <= req.hour <= 6

def allow(req: Request, policies: list[Policy]) -> bool:
    return all(policy(req) for policy in policies[:2]) or incident_override(req)

request = Request(
    subject=Subject("cardiology", 2, False),
    action="read",
    resource=Resource("cardiology", 2, "patient-314"),
    hour=14,
)
print("permit" if allow(request, [same_department, has_clearance]) else "deny")
```

Go.

```go
package main

import "fmt"

type Subject struct {
	Team      string
	Clearance int
}

type Resource struct {
	Team           string
	Classification int
}

type Request struct {
	Subject  Subject
	Action   string
	Resource Resource
	Network  string
}

type Policy func(Request) bool

func sameTeam(req Request) bool {
	return req.Subject.Team == req.Resource.Team
}

func enoughClearance(req Request) bool {
	return req.Subject.Clearance >= req.Resource.Classification
}

func privateNetwork(req Request) bool {
	return req.Action != "delete" || req.Network == "private"
}

func allow(req Request, policies ...Policy) bool {
	for _, policy := range policies {
		if !policy(req) {
			return false
		}
	}
	return true
}

func main() {
	req := Request{
		Subject:  Subject{Team: "payments", Clearance: 3},
		Action:   "delete",
		Resource: Resource{Team: "payments", Classification: 2},
		Network:  "private",
	}
	fmt.Println(allow(req, sameTeam, enoughClearance, privateNetwork))
}
```

Rust.

```rust
struct Subject {
    department: &'static str,
    clearance: u8,
    managed_device: bool,
}

struct Resource {
    department: &'static str,
    classification: u8,
}

struct Request {
    subject: Subject,
    action: &'static str,
    resource: Resource,
}

type Policy = fn(&Request) -> bool;

fn same_department(req: &Request) -> bool {
    req.subject.department == req.resource.department
}

fn enough_clearance(req: &Request) -> bool {
    req.subject.clearance >= req.resource.classification
}

fn managed_device_for_export(req: &Request) -> bool {
    req.action != "export" || req.subject.managed_device
}

fn allow(req: &Request, policies: &[Policy]) -> bool {
    policies.iter().all(|policy| policy(req))
}

fn main() {
    let request = Request {
        subject: Subject { department: "legal", clearance: 5, managed_device: true },
        action: "export",
        resource: Resource { department: "legal", classification: 4 },
    };
    println!("{}", allow(&request, &[same_department, enough_clearance, managed_device_for_export]));
}
```

## 18. References

- Hu, Vincent, David Ferraiolo, Richard Kuhn, Adam Schnitzer, Kenneth Sandlin,
  Robert Miller, and Karen Scarfone. *Guide to Attribute Based Access Control
  (ABAC) Definition and Considerations*. NIST Special Publication 800-162,
  January 2014, updated August 2, 2019. URL
  https://csrc.nist.gov/pubs/sp/800/162/upd2/final, verified 2026-08-02.
- OASIS. *eXtensible Access Control Markup Language (XACML) Version 3.0*.
  Edited by Erik Rissanen. OASIS Standard, January 22, 2013. Sections 2, 3,
  5.44 through 5.48, 7.2, 7.3, and 9. URL
  https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-en.html,
  verified 2026-08-02.
- Amazon Web Services. AWS Identity and Access Management User Guide. "Define
  permissions based on attributes with ABAC authorization." URL
  https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction_attribute-based-access-control.html,
  verified 2026-08-02.
- Google Cloud. Identity and Access Management documentation. "Overview of IAM
  Conditions." URL
  https://docs.cloud.google.com/iam/docs/conditions-overview?hl=en, verified
  2026-08-02.
- Microsoft Learn. "What is Azure attribute-based access control (Azure ABAC)?"
  URL
  https://learn.microsoft.com/en-us/azure/role-based-access-control/conditions-overview,
  verified 2026-08-02.
- Amazon Web Services. Amazon Verified Permissions User Guide. "Amazon Verified
  Permissions and Cedar policy language terms and concepts." URL
  https://docs.aws.amazon.com/verifiedpermissions/latest/userguide/terminology.html,
  verified 2026-08-02.
- Open Policy Agent. "Access Control Systems." URL
  https://www.openpolicyagent.org/docs/comparisons/access-control-systems,
  verified 2026-08-02.
