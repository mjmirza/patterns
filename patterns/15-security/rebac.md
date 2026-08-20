---
name: Relationship-Based Access Control
slug: rebac
family: 15-security
category: Security
aliases: [ReBAC, Relationship Based Access Control, Relationship-Based Authorization, Zanzibar-Style Authorization]
first_described: "Gates 2007, Fong 2011"
maturity: established
related: [rbac, abac, least-privilege, complete-mediation, gatekeeper, federated-identity]
incompatible_with: [ambient-authority, hardcoded-authorization, unchecked-direct-object-reference]
verified: 2026-08-02
---

# Relationship-Based Access Control

## 1. Name, aliases, and lineage

The canonical name is Relationship-Based Access Control, shortened to ReBAC.
The unhyphenated form Relationship Based Access Control also appears in papers
and product material. In production authorization teams, the same design is
often called relationship-based authorization, fine-grained authorization, or
Zanzibar-style authorization. The last name points to Google's Zanzibar paper,
not to one standard API.

The term has a social-computing lineage and a systems lineage. Carrie Gates
used the ReBAC name in work on Web 2.0 security and privacy requirements, and
Philip W. L. Fong's later papers made it a formal access-control model rather
than only a social-network idea. DBLP records Fong's "Relationship-based access
control: protection model and policy language" in CODASPY 2011, pages 191 to
202, DOI 10.1145/1943513.1943539
([DBLP record](https://dblp.org/rec/conf/codaspy/Fong11.html), verified
2026-08-02). Fong and Ida Siahaan's SACMAT 2011 paper, "Relationship-Based
Access Control Policies and Their Policy Languages", says the model was
proposed as a general-purpose access-control model and treats relational
policies as the thing that separates ReBAC from older models
([ResearchGate full text page](https://www.researchgate.net/publication/221366961_Relationship-based_access_control_policies_and_their_policy_languages),
verified 2026-08-02).

The production lineage changed with Zanzibar. Google's 2019 USENIX ATC paper
describes Zanzibar as a global system for storing and evaluating access control
lists with one data model and one configuration language across hundreds of
Google services, including Calendar, Cloud, Drive, Maps, Photos, and YouTube
([Google Research Zanzibar paper page](https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/),
verified 2026-08-02). Modern ReBAC systems such as Auth0 FGA, OpenFGA, and
SpiceDB borrow Zanzibar's tuple vocabulary, graph traversal, and check API.
Auth0 FGA documentation says Auth0 FGA is inspired by Zanzibar and relies on
ReBAC
([Auth0 FGA getting started](https://docs.fga.dev/getting-started), verified
2026-08-02). AuthZed describes SpiceDB as relationship-based access control in
the Google Zanzibar style
([AuthZed documentation](https://authzed.com/docs/index), verified
2026-08-02).

ReBAC is not a replacement name for RBAC. RBAC binds permissions to roles and
subjects to roles. ReBAC binds subjects and objects through named
relationships, then derives permissions from relationship paths. A project can
use both. A tuple such as `group:finance#member@user:anne` is group membership;
a rule such as "viewer includes member from parent" makes that membership grant
object access. The pattern is graph authorization with named business edges.

## 2. Problem and context

A collaborative system grants access because of how a subject is related to a
particular object. A user can read a document because they own it, because the
document was shared with their team, because the document is in a folder whose
viewer set includes a domain, or because they are a delegated editor for the
tenant that owns the document. A service account can mutate a pipeline because
it belongs to the project that owns that pipeline. An agent can call a tool
because it is acting for a user who has access to the data that tool will read.

Flat roles cannot express this cleanly. A role named `editor` says too little:
editor of which file, board, account, workspace, branch, patient, case, or
deployment? Per-object roles help, but then the model needs a way to inherit
from containers, expand groups, subtract blocklists, and answer list queries.
Per-user permission rows start as a local fix and end as policy scatter. Every
service learns its own version of "owner", "member", "viewer", and "parent".
The first audit then finds that the same word has different meaning in three
databases.

ReBAC introduces a graph of typed relationships. The protected world is modeled
as subjects, objects, relations, and permissions. The application writes tuples
such as `document:roadmap#owner@user:maya`,
`folder:eng#viewer@group:staff#member`, and
`document:roadmap#parent@folder:eng`. The authorization engine evaluates a
request by asking whether the subject reaches the requested permission through
direct relationships or derived relationships declared in the model.

The context that makes the pattern fit has four parts.

- Access is object-specific. The question is not "is this user an admin", but
  "can this subject perform this action on this object".
- Relationships already matter in the product model, such as owner, parent,
  member, assignee, collaborator, delegate, or tenant.
- Access must be checked in many services or endpoints, so duplicating policy
  code would create drift.
- The system needs auditability. A reviewer must be able to explain why a check
  returned allow or deny by tracing stored facts and model rules.

Engineering judgement: ReBAC is strongest for document sharing, source code
hosting, project management, enterprise SaaS tenancy, compliance platforms,
authorization for agents, and data filtering. It is weaker for small systems
where one table of roles and a few checks are enough.

## 3. Forces

Engineering judgement: this dimension weighs design pressure. Citations here
identify concrete systems or mechanisms; the balance described is a design
reading.

- **Coupling.** Favoured. Application services depend on a check contract and a
  model, not on local copies of every sharing rule. The price is a new coupling
  to the authorization schema, tuple writer, and consistency model.
- **Latency.** Sacrificed unless the graph is shallow, cached, or partly
  materialized. Zanzibar reported 95th percentile latency below 10 milliseconds
  while serving millions of authorization requests per second, but that result
  came from a purpose-built service, caching, and consistency design
  ([Google Research Zanzibar paper page](https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/),
  verified 2026-08-02). A small team copying the shape without the operational
  work should expect a cost per check.
- **Consistency.** Favoured when tuple writes happen in the same transaction
  boundary as domain writes or are tied to a causal token. Sacrificed when the
  application commits data first and emits tuple changes later through an
  unreliable queue.
- **Operability.** Favoured after instrumentation exists, because every decision
  can be traced as a graph question. Sacrificed before that, because a deny may
  be caused by missing tuple write, stale replica, bad model, bad subject
  mapping, or a true lack of permission.
- **Cost.** Sacrificed. Teams pay for an authorization service, schema review,
  backfill jobs, tuple repair, caches, list filtering strategies, and incident
  runbooks.
- **Team topology.** Favoured when platform security owns the model language and
  product teams own their resource types. Sacrificed when all teams must queue
  behind one central authorization group for every relation change.
- **Cognitive load.** Sacrificed. A reader must reason about graph reachability,
  inheritance, exclusion, and consistency windows. RBAC is easier to explain.
- **Privacy.** Favoured when the graph limits data retrieval before rows are
  returned. Sacrificed if tuple data reveals sensitive relationships, such as
  patient assignment, union membership, incident involvement, or private group
  names.

The pattern favours expressiveness, consistency of policy, and auditability. It
sacrifices local simplicity and some latency predictability.

## 4. Applicability and non-applicability

Reach for ReBAC when the following hold.

- Users, groups, service accounts, or agents gain access through their
  relationship to a resource, resource owner, group, tenant, folder, project, or
  organization.
- Permissions inherit through containment, such as folder to document, org to
  project, project to repository, repository to issue, or account to invoice.
- Multiple services need the same answer, and service-local checks would drift.
- The product needs share, delegate, transfer ownership, invite, remove, and
  audit flows with one policy model.
- List endpoints must return only objects visible to the caller. ReBAC can back
  `ListObjects`, `ListUsers`, reverse index, or overfetch plus batch-check
  strategies.
- The organization can operate the data pipeline that keeps the relationship
  graph current.

Non-applicability list.

- **The system has fewer than a handful of stable roles.** Use RBAC. ReBAC adds
  graph state and model review without returning enough value.
- **Authorization depends mostly on environment or request attributes.** Use
  ABAC or a policy language with context conditions. ReBAC can carry relations,
  but time, device posture, IP class, risk score, and transaction amount are not
  graph edges.
- **Policy is a fixed legal rule with little object sharing.** A policy engine
  or explicit code may read better than a graph encoding.
- **The product cannot tolerate a remote check on the hot path.** Consider
  signed capabilities, edge-local policy, materialized permission sets, or a
  cache with a documented staleness budget.
- **Relationship data is not trustworthy.** ReBAC turns relationship facts into
  authority. If tuple writers are uncontrolled, compromised, or impossible to
  audit, the graph becomes a privilege escalation surface.
- **The team cannot own migrations and backfills.** ReBAC schema changes often
  need tuple rewrites, backfills, and dual-read periods. Without that capacity,
  a smaller model is safer.
- **The access question is only "who has this global permission".** RBAC,
  groups, or IAM-style policy documents are a closer fit.
- **The graph is secret but decisions are delegated to many clients.** A
  capability or token design may leak less relationship data.

## 5. Structure

The participants are named by the role they play in the authorization system.

- **Subject.** The actor seeking access. It may be a user, service account,
  workload, team, group, domain, organization, or delegated agent.
- **Object.** The protected resource, such as document, folder, repository,
  issue, account, workspace, patient record, tool, feature, or dataset.
- **Relation.** A named edge from object to subject or object to another object.
  Examples are owner, editor, viewer, parent, member, blocked, assignee, and
  delegate.
- **Tuple.** A stored relationship fact with object, relation, and subject.
  Zanzibar-style systems commonly write it as `object#relation@subject`.
- **Authorization model.** A typed schema that declares object types, relations,
  permissions, unions, intersections, exclusions, and inheritance through other
  relations. Auth0 FGA's configuration language includes Zanzibar-style
  constructs such as computed usersets and tuple-to-userset rewrites
  ([Auth0 FGA configuration language](https://docs.fga.dev/modeling/configuration-language),
  verified 2026-08-02).
- **Policy decision point.** The engine that evaluates `check(subject, action,
  object)` by combining tuples with model rules.
- **Policy enforcement point.** The API handler, data-access interceptor,
  gateway, job runner, or tool host that asks the policy decision point before
  doing protected work.
- **Tuple writer.** The code path that creates, deletes, and backfills
  relationship facts when domain state changes.
- **Consistency token or revision.** A marker that lets a caller bind a check to
  a known graph version when read-after-write semantics matter.

The main relationship is asymmetric. The application owns domain events and
resource identifiers. The authorization model owns what those facts mean for
access. The decision point should not mutate domain state, and the domain
service should not duplicate authorization derivation rules in private helpers.

## 6. ASCII structure diagram

```text
        writes facts                         evaluates decisions
  +-------------------+      tuples      +-------------------------+
  | Domain services   | ---------------> | Relationship graph      |
  | owners, folders,  |                  | object#relation@subject |
  | groups, tenants   |                  +-----------+-------------+
  +---------+---------+                              |
            |                                        | reads
            | model changes                          v
            |                              +-----------------------+
            +----------------------------> | Authorization model   |
                                           | types, relations,     |
                                           | permissions, rewrites |
                                           +-----------+-----------+
                                                       |
                                                       v
  +-------------------+     check call      +-----------------------+
  | Enforcement point | ------------------> | Decision point        |
  | API, worker, PEP  | <------------------ | allow, deny, explain  |
  +---------+---------+      decision       +-----------------------+
            |
            v
  +-------------------+
  | Protected action  |
  | read, write, run  |
  +-------------------+

  Tuples say what relationships exist.
  The model says which relationships imply permissions.
```

## 7. Dynamics

At runtime the pattern has two flows: graph maintenance and access checking.
Most failures come from forgetting that both flows are part of one design.

```text
Graph maintenance

Client        Domain service        Tuple writer        Relationship graph
  |                 |                    |                       |
  | share doc       |                    |                       |
  |---------------> |                    |                       |
  |                 | validate owner     |                       |
  |                 |------------------->|                       |
  |                 |                    | write doc#viewer@user  |
  |                 |                    |---------------------->|
  |                 | commit domain row  |                       |
  |                 |------------------->|                       |
  |                 | return revision    |                       |
  |<----------------|                    |                       |

Access check

Subject       Enforcement point      Decision point       Graph and model
  |                 |                    |                       |
  | GET document    |                    |                       |
  |---------------> | check view         |                       |
  |                 |------------------->| read tuples, rules     |
  |                 |                    |---------------------->|
  |                 |                    | allow or deny          |
  |                 |<-------------------|                       |
  | return or 403   |                    |                       |
  |<----------------|                    |                       |
```

The decision point may walk a direct edge, expand a group, climb a parent edge,
apply union, require intersection, subtract a blocklist, or stop at a depth
limit. In a document model, `viewer` might include direct viewers, writers,
owners, members of a shared group, and viewers of the parent folder. In a
tenant model, `can_administer` might require both tenant membership and a
feature entitlement.

Consistency matters. If a user shares a file and immediately opens it from
another device, the check must observe the tuple write or the product feels
broken. Zanzibar explicitly treats causal ordering of user actions as a design
goal
([Google Research Zanzibar paper page](https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/),
verified 2026-08-02). Smaller systems need an equivalent contract, even if it
is only "same transaction" or "same primary database read".

## 8. Implementation variants

**Embedded graph in the application database.** Relationship rows live beside
domain tables, and checks run as SQL joins, recursive CTEs, or application
queries. This is simple to deploy and works for one service. It becomes hard
when many services need the same answer, when schemas diverge, or when the same
object appears in several datastores.

**External Zanzibar-style service.** A service such as OpenFGA, Auth0 FGA, or
SpiceDB stores tuples and evaluates checks through an API. Auth0 FGA documents a
store, relationship tuples, authorization models, and API calls
([Auth0 FGA getting started](https://docs.fga.dev/getting-started), verified
2026-08-02). This variant centralizes policy and fits many services, but adds
network latency, service dependency, schema operations, and tuple backfills.

**Policy language plus relationship attributes.** Cedar can represent
relationships as input attributes or as template-linked policies. Its best
practices distinguish between relationships already tracked for other reasons
and relationships that exist only for permission management
([Cedar relationship representation](https://docs.cedarpolicy.com/bestpractices/bp-relationship-representation.html),
verified 2026-08-02). This variant fits teams that already use policy
documents and want relations in request data. The trade is that the application
must fetch the correct relationship data before policy evaluation.

**Graph database plus policy engine.** AWS shows a design that uses Amazon
Neptune to traverse relationship data and Amazon Verified Permissions to
evaluate Cedar policies
([AWS Security Blog on ReBAC with Verified Permissions and Neptune](https://aws.amazon.com/blogs/security/how-to-implement-relationship-based-access-control-with-amazon-verified-permissions-and-amazon-neptune/),
verified 2026-08-02). This fits organizations already operating a graph store.
The risk is split-brain reasoning: traversal correctness and policy correctness
must be tested together.

**Materialized permission sets.** A write path expands relationships into
principal-to-object permission rows. Reads are fast and list endpoints are
easy. Writes, revokes, and hierarchy changes are harder, because one edge
change can invalidate many rows.

**Hybrid RBAC and ReBAC.** A role can be a relation on a resource, such as
`repo:api#maintainer@team:platform#member`. This keeps role words where people
expect them while preserving object scope. It is often the best shape for SaaS:
global roles for coarse duties, relationship tuples for resource access.

**In-process check library.** A small library holds tuples in memory for tests,
edge services, or single-process tools. It has no network cost and is easy to
compile. It lacks production-grade consistency, backfill, query, and audit
features unless the team builds them.

## 9. Known production uses

**Google Zanzibar.** Google's paper says Zanzibar serves hundreds of client
services at Google, including Calendar, Cloud, Drive, Maps, Photos, and
YouTube. The same page reports scale to trillions of ACLs and millions of
authorization requests per second for services used by billions of people
([Google Research Zanzibar paper page](https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/),
verified 2026-08-02). That is the canonical production proof for this pattern.

**Agicap with OpenFGA.** OpenFGA's Agicap case study says Agicap's SaaS platform
serves more than 8,000 customers and that every backend service validates
access through OpenFGA. The case study records production since April 2023,
about 250 requests per second, and use of ReBAC plus conditional relationships
([OpenFGA Agicap case study](https://openfga.dev/docs/adopters/agicap),
verified 2026-08-02).

**Openlane with OpenFGA.** OpenFGA's Openlane case study says Openlane wires
OpenFGA into its data-access layer so every GraphQL query and mutation is
authorized. The same case study describes ent hooks for tuple writes, query
interceptors, object-owned cascading permissions, and batch checks
([OpenFGA Openlane case study](https://openfga.dev/docs/adopters/openlane),
verified 2026-08-02).

**Headspace, Docker, Read AI, Grafana Labs, and other OpenFGA adopters.**
OpenFGA's adopter page lists named production deployments. It records Read AI
at a 5,200 RPS peak with more than 5.3 billion tuples, Docker in production
since March 2024, Grafana Labs for multi-tenant SaaS plus embedded OSS, and
Headspace with 10 to 15 ms p99
([OpenFGA adopters](https://openfga.dev/docs/adopters), verified
2026-08-02).

**Sourcegraph.** The OpenFGA community adopter list says Sourcegraph built an
internal-facing Zanzibar-style ReBAC framework based on OpenFGA to standardize
service roles and permissions
([OpenFGA community adopters](https://github.com/openfga/community/blob/main/ADOPTERS.md),
verified 2026-08-02).

## 10. Consequences

Positive.

- Access rules move from scattered `if` statements into a named model.
- The product can express object-specific sharing, group membership, parent
  inheritance, delegation, and deny lists without inventing one table per case.
- Auditors can inspect tuples and model rules rather than reading every API
  handler.
- List filtering has a principled backing model.
- Central policy lets product teams add resource types without copying every
  older check.
- RBAC can be scoped to objects instead of becoming global role sprawl.
- A single decision API makes authorization telemetry much easier to collect.

Negative.

- The access path gains a new service or graph query.
- Model mistakes can grant access across many endpoints at once.
- Tuple drift is a new class of data bug. Domain state and authorization state
  can disagree.
- Schema migrations need planning. Renaming a relation may require backfills,
  dual writes, and old-model support.
- Developers must learn graph reasoning, inheritance, and set operations.
- Debugging denies is harder than reading local code unless the system can
  explain which edge or rule failed.
- Relationship data may itself be sensitive.
- Very deep or cyclic graphs can make latency and explanation hard.

Engineering judgement: the pattern earns its place when product semantics are
already relational. It is overbuilt when it is adopted because the term
"fine-grained" sounds safer than a smaller RBAC design.

## 11. Failure modes and misuse

Engineering judgement: these triples describe failure patterns that appear in
production ReBAC systems. They are testable by their symptoms.

**Symptom.** A user shares a document, then receives `403` when opening the
same document through another endpoint. **Cause.** Domain write and tuple write
are not atomic, or the second endpoint reads an older graph revision. **Fix.**
Write tuples in the same transaction boundary where possible, return a revision
token, and pass that token into the next check.

**Symptom.** List endpoints return either too many rows or empty pages after
pagination. **Cause.** The service pages the domain database before filtering
by authorization, or it uses a list API with a model that cannot reverse the
permission cheaply. **Fix.** Use a supported list operation, maintain a reverse
index, or overfetch then batch-check with documented page bounds.

**Symptom.** Removing a user from a group does not revoke access to child
objects for minutes or hours. **Cause.** Materialized permissions or caches are
not invalidated on group membership changes. **Fix.** Add change streams for
all relation types that feed the materialization, set bounded TTLs, and test
revocation paths as first-class flows.

**Symptom.** A support role unexpectedly grants access to every tenant. **Cause.**
A relation intended to be tenant-scoped was modeled as global, or inheritance
crossed a tenant boundary. **Fix.** Put tenant or organization in every object
path, add a boundary relation, and write model tests for cross-tenant deny.

**Symptom.** Authorization checks time out on a few resources with large
folders, teams, or nested groups. **Cause.** The model permits deep recursive
walks, broad fan-out, or cycles. **Fix.** Put depth and fan-out limits in the
model review checklist, flatten hot hierarchies, and add query cost metrics.

**Symptom.** Engineers bypass the ReBAC service in urgent feature work. **Cause.**
The check API is too slow, too hard to use in tests, or unavailable in local
development. **Fix.** Provide a tiny in-memory evaluator, typed helper methods,
and service templates that make the check call the shortest path.

**Symptom.** An audit cannot explain why a decision was allowed. **Cause.** The
system logs only allow or deny, not the model version, tuple revision, relation
path, and caller. **Fix.** Log decision metadata and build a bounded
explanation endpoint for security review.

**Symptom.** A deleted object continues to grant inherited permissions. **Cause.**
Object deletion removed domain rows but left parent or member tuples. **Fix.**
Make tuple cleanup part of deletion transactions, add orphan tuple scans, and
block reusing mutable identifiers.

**Symptom.** A blocklist relation appears in the model but does not affect some
actions. **Cause.** Exclusion was added to one permission and missed in others.
**Fix.** Define blocklist once as a reusable permission or relation expression,
then add tests for every action that must observe it.

## 12. Trade-off matrix

| Force | ReBAC | RBAC | ABAC | ACL per object | Capability tokens | Policy engine with request context |
|---|---|---|---|---|---|---|
| Coupling | Low to local code, high to model | Low for global duties | Low to roles, high to attributes | High to each object store | Low after issue | Low to app code, high to policy inputs |
| Object-specific access | Strong | Weak unless roles are scoped | Medium | Strong | Strong for granted operations | Medium to strong |
| Inheritance | Strong when modeled | Role hierarchy only | Must be encoded | Usually ad hoc | Not natural | Depends on fetched context |
| Latency | Remote graph or cache cost | Usually low | Policy eval plus data fetch | Local read cost | Very low at check time | Eval plus context fetch |
| Consistency | Hard but explicit | Easier | Depends on attribute freshness | Tied to object store | Revocation hard | Depends on input source |
| Operability | Good with explain and revision | Good for audits | Hard when attributes sprawl | Hard across services | Hard after token issue | Good if policies are versioned |
| Cost | High | Low to medium | Medium | Low first, high later | Medium | Medium |
| Team topology | Good for platform plus product teams | Good for central IAM | Good with policy owners | Poor across services | Good for edge teams | Good with policy review |
| Cognitive load | High | Low | Medium | Low locally | Medium | Medium |
| Revocation | Good if graph is fresh | Good | Good if attributes fresh | Good locally | Poor until expiry | Good if inputs fresh |

Reading of the table. ReBAC wins when object relationships are the domain
truth. RBAC wins for job duties. ABAC wins when environment and subject
attributes dominate. ACLs win for a single product surface with simple sharing.
Capability tokens win for offline delegation and edge checks with short expiry.
A policy engine wins when the rule is more about context than graph reachability.

## 13. Related and incompatible patterns

- **RBAC.** Composes with ReBAC. A role can be represented as a relation scoped
  to an organization, project, repository, or account. Use global RBAC for
  broad duties and ReBAC for resource-level reachability.
- **ABAC.** Complements ReBAC when decisions also need device, time, region,
  risk, or data classification. Cedar documentation describes representing
  relationships through attributes when the relationship is already tracked for
  reasons outside permission management
  ([Cedar relationship representation](https://docs.cedarpolicy.com/bestpractices/bp-relationship-representation.html),
  verified 2026-08-02).
- **Gatekeeper.** Hosts the enforcement point. An API gateway can perform coarse
  checks, but most ReBAC checks need object identifiers known inside the
  service or data-access layer.
- **Complete Mediation.** ReBAC depends on it. Every protected operation must
  ask the decision point or a validated cached equivalent.
- **Least Privilege.** ReBAC helps express narrow grants, but it does not prove
  those grants are narrow. Model review and tuple hygiene still matter.
- **Valet Key and capability token.** Substitute when access must be delegated
  without contacting the graph on every request. The trade is revocation and
  audit path length.
- **Service Locator.** Conflicts when services fetch authorization state from a
  global helper that hides inputs. The check should make subject, action,
  object, model version, and context visible.
- **Hardcoded authorization.** Conflicts directly. If endpoints keep private
  role switches beside ReBAC checks, the system has two policy sources and no
  clear answer during incidents.

## 14. Refactoring path in and out

Introducing ReBAC into a system without it.

1. Inventory authorization questions. Write them as subject, action, object,
   and reason. Do not start with tables.
2. Identify relationship names already present in the product: owner, member,
   parent, assigned, delegate, blocked, shared, tenant.
3. Pick one high-value flow, such as document view or project edit. Keep the
   first model small.
4. Add an enforcement wrapper around the existing check. It should log subject,
   object, action, old decision, and new decision while still enforcing the old
   path.
5. Build tuple writers from domain mutations. Use transactional writes where the
   datastore permits it.
6. Backfill tuples from current domain data. Count expected and written tuples.
7. Run shadow checks. Compare old and new decisions, investigate mismatches,
   and classify each as old bug, new bug, or intended policy change.
8. Add model tests with allow and deny cases, including cross-tenant denial,
   blocklist, inheritance, and group revocation.
9. Switch one endpoint to enforce ReBAC. Keep the old path as telemetry until
   confidence is earned.
10. Expand by resource type, not by random endpoint. A complete resource model
    is easier to reason about than a half-migrated model.

Named refactorings from the refactoring family often apply: Extract Function
for local authorization predicates, Replace Conditional with Polymorphism when
resource types choose tuple writers, Introduce Parameter Object for the check
request, and Move Function when enforcement belongs in the data-access layer.

Removing ReBAC when it stops earning its place.

1. Prove the graph no longer expresses business relationships that matter for
   access. If only two global roles remain, migrate to RBAC.
2. Freeze model changes and emit decision logs for a full usage cycle.
3. Replace checks with a smaller policy or role call behind the same
   enforcement wrapper.
4. Run old and new decisions in parallel until mismatch rate is understood.
5. Stop tuple writes only after all readers are off the graph.
6. Archive relationship history according to retention rules, because tuple
   logs may be audit evidence.
7. Delete tuple tables and schemas last.

## 15. Testing and verification

Engineering judgement: ReBAC testing must cover model semantics, tuple
maintenance, integration boundaries, and operational behavior. Unit tests alone
are weak here.

- **Model tests.** For each permission, create small tuple fixtures with named
  allow and deny cases. Include inherited allow, direct allow, group allow,
  blocklisted deny, cross-tenant deny, and missing-parent deny.
- **Tuple writer tests.** Every domain mutation that changes access should
  assert the exact tuples written and deleted. This catches drift before the
  decision point sees it.
- **Shadow decision tests.** During migration, run old and new authorization in
  parallel and record mismatches with enough data to replay them.
- **Property tests.** Generate small graphs and assert invariants such as "a
  blocked subject cannot view" or "membership in tenant A never grants access
  to tenant B".
- **Contract tests for callers.** Each service using the decision point should
  prove that it passes stable subject IDs, object IDs, action names, model
  version, and context.
- **Revocation tests.** Deleting a share, removing group membership, disabling
  a service account, or moving an object out of a folder must be tested as
  carefully as granting access.
- **List endpoint tests.** Test empty result, full page, partial page after
  filtering, large fan-out, and pagination cursor behavior.
- **Replay tests.** Keep a redacted corpus of production decision records and
  replay it against model changes before rollout.

What became easier. A test can explain access through tuples rather than
building half the application state. What became harder. Correctness depends on
writers, readers, caches, model versioning, and list strategies all agreeing.

## 16. Observability signals

Record the decision as a first-class production event.

- Decision count by action, object type, subject type, result, model version,
  and enforcement point.
- Decision latency histogram by permission and relation depth.
- Tuple write count, delete count, retry count, and lag from domain event to
  graph visibility.
- Cache hit rate, cache age, and stale-read count where the engine exposes it.
- Graph traversal counters: edge reads, recursion depth, fan-out, cycle stops,
  and expansion type.
- Deny reason categories: no subject, no object, no relation path, blocked,
  stale revision, invalid model, and decision service unavailable.
- List endpoint metrics: candidate count, checked count, allowed count, page
  fill ratio, and batch-check latency.
- Model rollout metrics: checks by model version and mismatch rate during
  shadow evaluation.

A healthy dashboard shows stable allow and deny ratios per endpoint, low tuple
lag, bounded traversal depth, and list page fill that matches product traffic.
A failing dashboard shows depth spikes on one resource type, rising stale reads,
tuple writer lag after deploy, or a sudden allow-rate jump for a new model
version. The last signal is a security incident until proven otherwise.

Logs should include subject type, object type, action, result, model version,
tuple revision, enforcement point, and request ID. Avoid logging raw user IDs or
resource names where those fields are sensitive. Hash or tokenize them when the
operator does not need the literal value.

## 17. Security and privacy implications

ReBAC can reduce overbroad roles, but it creates a high-value authorization
graph. Treat graph writes as privileged operations. A compromised tuple writer
can grant access without touching the domain object.

Primary security concerns.

- **Tuple injection.** If a caller can write `object#owner@attacker`, they own
  the resource. Protect tuple APIs with stronger controls than ordinary
  product APIs.
- **Cross-tenant inheritance.** Parent edges that cross tenant boundaries turn
  one grant into many unintended grants. Add tenant boundary checks in model
  tests and tuple writers.
- **Stale grants.** Delayed tuple deletion keeps access alive after offboarding,
  share removal, or incident response. Revocation SLOs belong in the design.
- **Over-permissive indirect paths.** AWS warns that indirect relationships can
  be hard to reason about and can become over-permissive without a boundary
  ([AWS Security Blog on ReBAC with Verified Permissions and Neptune](https://aws.amazon.com/blogs/security/how-to-implement-relationship-based-access-control-with-amazon-verified-permissions-and-amazon-neptune/),
  verified 2026-08-02).
- **Identifier reuse.** Reusing a deleted object ID can attach old tuples to a
  new object. Use immutable identifiers and orphan cleanup.
- **Deny by outage.** The decision point is on the access path. Security
  posture should state whether failures are closed, degraded to cached
  decisions, or routed through break-glass controls.

Privacy concerns.

The relationship graph may reveal sensitive facts: who belongs to a private
group, which employee handles a legal case, which clinician treats a patient,
which customer has a premium feature, or which user delegated authority to an
agent. Apply retention, access review, encryption, and deletion policies to
tuple data and decision logs. Explanation tools should be scoped by role,
because explaining a deny can reveal relationships the requester should not
see.

Engineering judgement: ReBAC improves privacy only when checks happen before
data fetch or before data leaves a trusted boundary. If services fetch broad
rows and filter later in memory, the model has not protected the data path.

## Code examples

Three runnable examples show the core relation graph in different language
styles. They are not clients for any vendor service.

### Python

```python
from collections import defaultdict


class Rebac:
    def __init__(self) -> None:
        self.edges: dict[tuple[str, str], set[str]] = defaultdict(set)

    def add(self, obj: str, relation: str, subject: str) -> None:
        self.edges[(obj, relation)].add(subject)

    def has(self, subject: str, permission: str, obj: str) -> bool:
        seen: set[tuple[str, str]] = set()

        def related(target: str, relation: str) -> bool:
            key = (target, relation)
            if key in seen:
                return False
            seen.add(key)
            direct = self.edges[key]
            if subject in direct:
                return True
            if relation == "viewer" and related(target, "owner"):
                return True
            for parent in self.edges[(target, "parent")]:
                if related(parent, relation):
                    return True
            for group in direct:
                if group.startswith("group:") and related(group, "member"):
                    return True
            return False

        return permission == "view" and related(obj, "viewer")


graph = Rebac()
graph.add("folder:eng", "viewer", "group:staff")
graph.add("group:staff", "member", "user:maya")
graph.add("doc:roadmap", "parent", "folder:eng")
print(graph.has("user:maya", "view", "doc:roadmap"))
```

### Go

```go
package main

import "fmt"

type Graph map[string]map[string]bool

func key(object, relation string) string {
	return object + "#" + relation
}

func (g Graph) Add(object, relation, subject string) {
	k := key(object, relation)
	if g[k] == nil {
		g[k] = map[string]bool{}
	}
	g[k][subject] = true
}

func (g Graph) Has(subject, permission, object string) bool {
	seen := map[string]bool{}
	var related func(string, string) bool
	related = func(target, relation string) bool {
		k := key(target, relation)
		if seen[k] {
			return false
		}
		seen[k] = true
		if g[k][subject] {
			return true
		}
		if relation == "viewer" && related(target, "owner") {
			return true
		}
		for parent := range g[key(target, "parent")] {
			if related(parent, relation) {
				return true
			}
		}
		for member := range g[k] {
			if len(member) > 6 && member[:6] == "group:" && related(member, "member") {
				return true
			}
		}
		return false
	}
	return permission == "view" && related(object, "viewer")
}

func main() {
	g := Graph{}
	g.Add("folder:eng", "viewer", "group:staff")
	g.Add("group:staff", "member", "user:maya")
	g.Add("doc:roadmap", "parent", "folder:eng")
	fmt.Println(g.Has("user:maya", "view", "doc:roadmap"))
}
```

### Rust

```rust
use std::collections::{HashMap, HashSet};

#[derive(Default)]
struct Rebac {
    edges: HashMap<(String, String), HashSet<String>>,
}

impl Rebac {
    fn add(&mut self, object: &str, relation: &str, subject: &str) {
        self.edges
            .entry((object.to_string(), relation.to_string()))
            .or_default()
            .insert(subject.to_string());
    }

    fn has(&self, subject: &str, permission: &str, object: &str) -> bool {
        fn related(
            g: &Rebac,
            subject: &str,
            target: &str,
            relation: &str,
            seen: &mut HashSet<(String, String)>,
        ) -> bool {
            let key = (target.to_string(), relation.to_string());
            if !seen.insert(key.clone()) {
                return false;
            }
            let direct = g.edges.get(&key);
            if direct.is_some_and(|set| set.contains(subject)) {
                return true;
            }
            if relation == "viewer" && related(g, subject, target, "owner", seen) {
                return true;
            }
            if let Some(parents) = g.edges.get(&(target.to_string(), "parent".to_string())) {
                for parent in parents {
                    if related(g, subject, parent, relation, seen) {
                        return true;
                    }
                }
            }
            if let Some(members) = direct {
                for member in members {
                    if member.starts_with("group:")
                        && related(g, subject, member, "member", seen)
                    {
                        return true;
                    }
                }
            }
            false
        }

        permission == "view"
            && related(self, subject, object, "viewer", &mut HashSet::new())
    }
}

fn main() {
    let mut graph = Rebac::default();
    graph.add("folder:eng", "viewer", "group:staff");
    graph.add("group:staff", "member", "user:maya");
    graph.add("doc:roadmap", "parent", "folder:eng");
    println!("{}", graph.has("user:maya", "view", "doc:roadmap"));
}
```

## 18. References

1. Carrie E. Gates. "Access Control Requirements for Web 2.0 Security and
   Privacy." IEEE Web 2.0 Privacy and Security Workshop, 2007. Cited through
   Fong and Siahaan's lineage discussion because the workshop page was not used
   directly for a claim in this entry.
2. Philip W. L. Fong. "Relationship-based access control: protection model and
   policy language." CODASPY 2011, pages 191 to 202. DOI
   10.1145/1943513.1943539.
   https://dblp.org/rec/conf/codaspy/Fong11.html
   Verified 2026-08-02. Source for the formal ReBAC model lineage.
3. Philip W. L. Fong and Ida Siahaan. "Relationship-Based Access Control
   Policies and Their Policy Languages." SACMAT 2011, pages 51 to 60. DOI
   10.1145/1998441.1998450.
   https://www.researchgate.net/publication/221366961_Relationship-based_access_control_policies_and_their_policy_languages
   Verified 2026-08-02. Source for relational policies as a ReBAC distinction.
4. Ruoming Pang, Ramon Caceres, Mike Burrows, Zhifeng Chen, Pratik Dave,
   Nathan Germer, Alexander Golynski, Kevin Graney, Nina Kang, Lea Kissner,
   Jeffrey L. Korn, Abhishek Parmar, Christina D. Richards, and Mengzhi Wang.
   "Zanzibar: Google's Consistent, Global Authorization System." USENIX ATC
   2019.
   https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/
   Verified 2026-08-02. Source for Zanzibar design goals, Google production
   use, service names, scale, latency, and availability statements.
5. Auth0. "Getting started with Auth0 FGA."
   https://docs.fga.dev/getting-started
   Verified 2026-08-02. Source for Auth0 FGA's Zanzibar inspiration, ReBAC
   basis, stores, tuples, and API framing.
6. Auth0. "Configuration Language."
   https://docs.fga.dev/modeling/configuration-language
   Verified 2026-08-02. Source for computed usersets, tuple-to-userset rewrites,
   and Zanzibar-style model constructs.
7. AuthZed. "AuthZed Documentation."
   https://authzed.com/docs/index
   Verified 2026-08-02. Source for SpiceDB as a Zanzibar-style ReBAC system.
8. Cedar Policy Language. "Best practice: Use attributes or templates to
   represent relationships."
   https://docs.cedarpolicy.com/bestpractices/bp-relationship-representation.html
   Verified 2026-08-02. Source for relationship representation variants in
   Cedar.
9. Amazon Web Services Security Blog. "How to implement relationship-based
   access control with Amazon Verified Permissions and Amazon Neptune."
   https://aws.amazon.com/blogs/security/how-to-implement-relationship-based-access-control-with-amazon-verified-permissions-and-amazon-neptune/
   Verified 2026-08-02. Source for the Cedar plus Neptune variant and warnings
   about indirect relationships.
10. OpenFGA. "OpenFGA Adopters and Case Studies."
    https://openfga.dev/docs/adopters
    Verified 2026-08-02. Source for named OpenFGA production adopters and
    deployment scale.
11. OpenFGA. "Agicap: Fine-grained authorization for a European fintech
    platform."
    https://openfga.dev/docs/adopters/agicap
    Verified 2026-08-02. Source for Agicap production use.
12. OpenFGA. "Openlane: Authorization at the data-access layer for compliance
    automation."
    https://openfga.dev/docs/adopters/openlane
    Verified 2026-08-02. Source for Openlane production use.
13. OpenFGA Community. "ADOPTERS.md."
    https://github.com/openfga/community/blob/main/ADOPTERS.md
    Verified 2026-08-02. Source for Sourcegraph and other community-listed
    production uses.
