---
name: Zero Trust
slug: zero-trust
family: 15-security
category: Security
aliases: [Zero Trust Architecture, ZTA, Zero Trust Network Architecture, BeyondCorp Model]
first_described: "Kindervag 2010; NIST SP 800-207 2020"
maturity: established
related: [least-privilege, complete-mediation, defense-in-depth, mutual-tls, abac, audit-log, federated-identity]
incompatible_with: [implicit-network-trust, flat-internal-network, shared-credential, service-locator]
verified: 2026-08-02
---

# Zero Trust

## 1. Name, aliases, and lineage

The canonical name is Zero Trust. In system architecture prose it is often
expanded to Zero Trust Architecture, abbreviated ZTA. Network teams may say
Zero Trust Network Architecture, ZTNA, or software-defined perimeter, although
those labels name narrower access-network variants rather than the whole
pattern. Google popularized the related BeyondCorp label for its internal
model and later product family. Google describes BeyondCorp as its
implementation of the zero trust model and says it moved access controls from
the network perimeter to individual users
([Google Cloud BeyondCorp](https://cloud.google.com/beyondcorp?hl=en),
verified 2026-08-02).

The name came into wide industry use through John Kindervag at Forrester.
Forrester lists the 2010 webinar "No More Chewy Centers. The Zero-Trust Model
Of Information Security" with Kindervag as the presenting analyst, and the
Forrester report "Build Security Into Your Network's DNA. The Zero Trust
Network Architecture" under Kindervag's name
([Forrester webinar](https://www.forrester.com/webinar/No%2BMore%2BChewy%2BCenters%2BThe%2BZeroTrust%2BModel%2BOf%2BInformation%2BSecurity/WEB6741),
verified 2026-08-02;
[Forrester report page](https://www.forrester.com/report/build-security-into-your-networks-dna-the-zero-trust-network-architecture/RES57047),
verified 2026-08-02). NIST SP 800-207, published in August 2020 by Scott
Rose, Oliver Borchert, Stu Mitchell, and Sean Connelly, is the stable public
architecture reference used by many teams. It defines zero trust as a set of
cybersecurity ideas that move defenses away from static network perimeters and
toward users, assets, and resources
([NIST SP 800-207](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-207.pdf),
verified 2026-08-02).

This entry treats Zero Trust as a software and enterprise architecture pattern,
not as a vendor product. The pattern is the control loop: identify the resource,
authenticate the subject and device, evaluate context and policy, grant the
least access needed for the session, observe the session, and revisit the
decision as facts change. Products can host pieces of that loop, but buying a
proxy, identity provider, endpoint agent, or firewall does not by itself create
the pattern.

## 2. Problem and context

A system has users, services, jobs, devices, and partners that need access to
resources from many networks. Some run from offices, some from homes, some from
cloud workloads, and some from third-party environments. The old boundary says
"inside the network is trusted, outside the network is hostile." That boundary
does not match the system anymore. NIST names remote users, bring your own
device, and cloud assets outside an enterprise-owned network as drivers for
zero trust, and says the resource, not the network segment, becomes the focus
of protection
([NIST SP 800-207](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-207.pdf),
verified 2026-08-02).

The code smell appears in many forms. An internal API accepts any request from
an RFC 1918 address. A database subnet is reachable from every application
node. A VPN gives a laptop route-level access to a whole address range because
one admin page lives there. A service token grants all tenants because nobody
modeled workload identity. Logs say the request came from a gateway, but not
which person, device, workload, data set, risk score, or policy allowed it. The
team may have authentication at the edge, but the internal calls act as if the
first gate was enough.

Zero Trust fits when a resource owner must make an access decision with facts
that are richer than source IP. It fits a corporate application, a cloud data
plane, a service mesh, a partner portal, an admin tool, or a build pipeline. The
context is repeated access to named resources under changing identity, device,
network, data, and risk conditions. The pattern is weaker when the system has no
identity fabric, no inventory, no telemetry, or no policy owner. In that case
the first work is not a proxy rollout. It is to name the resources, subjects,
devices, and policy decisions that will later feed the loop.

## 3. Forces

This dimension is engineering judgement except where a specific source is
cited.

- **Security versus reachability.** The pattern favours resource-scoped access
  over network-scoped reachability. A user can reach the payroll application
  without reaching every host in the payroll subnet.
- **Latency versus decision quality.** More context gives better decisions, but
  identity lookup, device posture, policy evaluation, and risk scoring add work
  to the request path. Cache with short lifetimes where the resource permits it.
- **Consistency versus autonomy.** Central policy gives a common access model.
  Local resource owners still need room to express domain rules, such as tenant,
  record class, or break-glass conditions.
- **Operability versus privacy.** The pattern needs telemetry about identities,
  devices, sessions, policy results, and denial reasons. That telemetry can
  expose employee behavior or customer identifiers if labels are careless.
- **Cost versus blast-radius reduction.** Identity, device management, policy
  engines, service identity, segmentation, and observability all have cost. The
  payoff is narrower movement after credential theft or device compromise.
- **Team topology versus shared control.** Platform security can run the policy
  decision plane, while application teams own resource semantics. The pattern
  breaks when every team invents its own terms for subjects, actions, and risk.
- **Availability versus fail-closed behavior.** If the decision plane is down,
  a secure default blocks access, but a broad outage may stop work. Some
  resources need cached grants, local policy bundles, or emergency access.
- **Cognitive load versus explicitness.** Readers must understand identities,
  policies, and context sources. The reward is that access paths become named,
  measured, and reviewable.

NIST states that authentication and authorization of subject and device are
separate functions performed before a session to an enterprise resource is
established, and it also lists policy engine, policy administrator, and policy
enforcement point as logical components
([NIST SP 800-207](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-207.pdf),
verified 2026-08-02). That creates the core trade. Access decisions become
more exact, but the decision system itself becomes infrastructure that must be
designed, operated, and protected.

## 4. Applicability and non-applicability

Reach for Zero Trust when the following hold.

- Resources are accessed from more than one network, device class, tenant, or
  partner boundary.
- The organization cannot treat a network location as proof of trust.
- A resource owner can describe who may do what to which resource, with which
  device and session conditions.
- Identity and device signals are available or can be introduced in stages.
- Lateral movement after a compromised account, host, or token is a material
  risk.
- Operators can observe access decisions and tune policies from real denial and
  grant data.
- The system has high-value administrative paths where broad VPN or subnet
  access creates unnecessary exposure.
- Workloads call other workloads and need service identity, not only human
  identity.

Do NOT reach for Zero Trust in these cases.

- **No resource inventory.** If the team cannot list the applications, APIs,
  data stores, jobs, and admin paths being protected, policy will be vague.
  Start with asset discovery and data classification.
- **No stable subject identity.** Shared accounts, shared service tokens, and
  shared admin passwords defeat the control loop. Replace them with named human
  and workload identities first.
- **Single-process code with no access boundary.** A library function inside one
  process usually needs normal authorization checks, not a Zero Trust access
  plane.
- **Hard real-time paths.** If a control loop cannot tolerate policy calls,
  remote introspection, or short-lived credential renewal, use a local policy
  bundle with a bounded update plan or keep the path out of scope.
- **Air-gapped or isolated lab networks with fixed devices and no remote access.**
  The pattern may still offer useful ideas, but a full identity, device, and
  policy plane may cost more than the risk reduction.
- **Compliance theater.** A proxy in front of an unchanged flat network is not
  Zero Trust. The resource still needs least access, policy evaluation,
  telemetry, and denial behavior.
- **Unowned policy.** If nobody can approve a policy rule or remove a stale
  exception, the policy store becomes an outage source and a hidden permission
  dump.
- **Only encryption is missing.** Use mutual TLS, certificate rotation, or
  transport security directly. Zero Trust includes encrypted paths, but it is
  broader than channel protection.
- **Public unauthenticated resources.** A marketing page, public package mirror,
  or public status feed may need rate limits, integrity, and abuse controls, but
  it does not need subject-specific authorization for normal reads.

## 5. Structure

The participants below use NIST's logical component names where they match the
pattern. NIST describes a policy engine, policy administrator, and policy
enforcement point in SP 800-207
([NIST SP 800-207](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-207.pdf),
verified 2026-08-02).

- **Subject.** The human user, service, device, job, or other actor asking for
  access. A subject must have a stable identity and proof material, such as MFA,
  a token, or a workload certificate.
- **Resource.** The application, API, record set, queue, database, host, or
  admin action being requested. The resource has an owner and a policy scope.
- **Policy Enforcement Point.** The gateway, sidecar, middleware, reverse proxy,
  service mesh filter, database proxy, or application guard that intercepts the
  request and either permits, narrows, or denies it.
- **Policy Decision Point.** The policy engine and policy administrator as a
  logical unit. It evaluates facts, returns a decision, and may issue a scoped
  credential or route.
- **Identity Provider.** The system that authenticates human and workload
  identities and issues claims.
- **Device Posture Source.** The endpoint management, mobile device management,
  inventory, or attestation source that states whether a device is known,
  managed, healthy, patched, encrypted, or high risk.
- **Context Sources.** Risk engines, location signals, data labels, workload
  inventory, vulnerability scanners, time windows, incident state, and behavior
  models. These are inputs, not authorities.
- **Telemetry Store.** Logs, traces, metrics, and audit records for requests,
  grants, denials, policy versions, and context used in the decision.
- **Policy Owner.** The human or team accountable for a resource policy. Without
  this role, exceptions tend to remain forever.

The key relationship is that the enforcement point does not infer trust from
the network. It asks the decision point, and the decision point uses identity,
device, resource, action, policy, and current context. The resource receives
only requests that passed the enforcement point, but high-value resources still
perform local authorization for domain rules. That local check stops a mistaken
gateway rule from becoming total access.

## 6. ASCII structure diagram

```text
  +------------------+        request         +----------------------+
  |     Subject      | ---------------------> | Policy Enforcement   |
  | user, job, svc   |                        | Point                |
  +------------------+                        +----------+-----------+
                                                          |
                                                          | decision query
                                                          v
  +------------------+    claims       +------------------+-----------+
  | Identity         | --------------> | Policy Decision Point         |
  | Provider         |                 | policy engine plus admin      |
  +------------------+                 +------+-------------+----------+
                                             ^             ^
  +------------------+    posture            |             | context
  | Device Posture   | ----------------------+             |
  | Source           |                                      |
  +------------------+                                      |
                                             +-------------+----------+
                                             | Context Sources        |
                                             | risk, data, inventory  |
                                             +-------------+----------+
                                                           |
                                                           | decision
                                                           v
  +------------------+   allowed scoped call  +------------+---------+
  | Telemetry Store  | <--------------------- | Protected Resource   |
  | logs and audit   |                        | app, API, data       |
  +------------------+                        +----------------------+

  The network path carries packets. The decision path carries authority.
```

## 7. Dynamics

At runtime the pattern is a decision loop, not a one-time login. Microsoft
summarizes the three principles as verify explicitly, use least privileged
access, and assume breach
([Microsoft Learn Zero Trust adoption overview](https://learn.microsoft.com/en-us/security/zero-trust/adopt/zero-trust-adoption-overview),
verified 2026-08-02). NIST says zero trust usually involves minimizing access
to resources and continually authenticating and authorizing identity and
posture for each access request
([NIST SP 800-207](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-207.pdf),
verified 2026-08-02).

```text
Subject        Enforcement     Decision       Identity       Posture      Resource
   |                |              |              |              |            |
   | request /pay   |              |              |              |            |
   |--------------->|              |              |              |            |
   |                | facts query  |              |              |            |
   |                |------------->|              |              |            |
   |                |              | validate id  |              |            |
   |                |              |------------->|              |            |
   |                |              |<-------------|              |            |
   |                |              | check device |              |            |
   |                |              |---------------------------->|            |
   |                |              |<----------------------------|            |
   |                |              | evaluate policy and risk    |            |
   |                |<-------------| permit: payroll.read, 5 min |            |
   | scoped call    |              |              |              |            |
   |--------------->|------------------------------------------->|            |
   |                |              |              |              | local auth |
   |                |              |              |              |----------->|
   |                |<-------------------------------------------| response   |
   |<---------------|              |              |              |            |
   |                | write audit: subject, device, action, policy, result    |
   |                |-------------------------------------------------------->|
```

If the device posture flips to high risk, a policy bundle changes, or a risk
engine raises the subject score, the next decision can deny or shorten access.
For long sessions, the enforcement point revalidates on interval or on event.
For service-to-service calls, the same flow uses workload identity, often with
mutual TLS or signed tokens, rather than a human login.

## 8. Implementation variants

**Application guard.** Authorization lives in the application middleware or
request handler. This gives the application full access to domain terms such as
tenant, account, role, record label, and workflow state. The cost is repeated
implementation across many services unless a shared policy library is used.

**Reverse proxy or access gateway.** A proxy sits before web applications and
checks identity, device posture, and policy before forwarding traffic. This is
fast to adopt for legacy web apps. It is weaker for fine-grained actions unless
the proxy receives application context.

**Service mesh.** A mesh sidecar or node proxy gives workloads identity, mutual
TLS, and policy enforcement for service-to-service traffic. This fits
microservices and platform teams. It adds a data-plane dependency to every call
and can hide policy behavior from application developers.

**Software-defined perimeter.** The client establishes a tunnel only to the
specific resource after authorization. This replaces broad VPN access. It fits
admin tools and private applications but needs client software and a resource
catalog.

**Microsegmentation.** Network policy limits east-west movement between hosts,
workloads, or subnets. NIST lists microsegmentation as one ZTA approach
([NIST SP 800-207](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-207.pdf),
verified 2026-08-02). It helps when legacy protocols cannot be changed, but it
does not replace application authorization.

**Identity governance first.** The organization starts with MFA, conditional
access, group hygiene, privilege review, and identity lifecycle. This has a
large payoff because most policy decisions rely on identity facts. It can leave
machine-to-machine traffic under-modeled unless workload identity is added.

**Data-centric policy.** Decisions follow data labels and record sensitivity.
This fits regulated data, analytics, and document stores. It requires labeling
quality and clear data owners.

**Local policy bundle.** Enforcement points receive signed policy bundles and
evaluate locally. This reduces latency and helps during decision-plane outages.
It sacrifices immediate revocation unless the bundle lifetime is short and
emergency invalidation exists.

**Risk-adaptive policy.** A policy engine uses risk scores, impossible travel,
device signals, and incident state. This catches behavior that static groups
miss. It also creates explainability work because users and operators need
clear denial reasons.

**Privileged access first.** Many teams start with administrator consoles,
production shells, database consoles, and cloud control planes. The user set is
small, the resources are high value, and broad access is easy to see in logs.
This variant pairs well with short grant lifetimes, approval workflows, and
session recording. The downside is that it can leave ordinary application data
paths untouched for too long if leadership declares victory after admin access
improves.

**Partner and contractor access.** The enforcement point protects a small set of
applications for external users whose devices and identities are not fully
owned by the enterprise. Federated identity and device attestations become key
inputs. This variant avoids giving a partner a VPN route to internal networks,
but it requires tight resource ownership because partner exceptions tend to
outlive the project that created them.

**Workload-first Zero Trust.** A platform team gives every service, batch job,
and deploy pipeline a workload identity, then writes policy for service-to-
service calls. Human access is still needed for operations, but the primary
risk being handled is machine access. This variant works well in Kubernetes,
service mesh, and cloud-native estates. It is poor for legacy estates where
services cannot present identity or where one host runs many unrelated jobs
under the same account.

## 9. Known production uses

**Google BeyondCorp.** Google says BeyondCorp began as an internal initiative
to let every employee work from untrusted networks without a VPN, and says most
Googlers use it each day for user and device based authentication and
authorization to corporate resources and core infrastructure
([Google Cloud BeyondCorp](https://cloud.google.com/beyondcorp?hl=en),
verified 2026-08-02). The public paper "BeyondCorp. A New Approach to
Enterprise Security" states that Google was removing the privileged intranet
requirement and moving corporate applications to the Internet
([Google Research publication](https://research.google/pubs/beyondcorp-a-new-approach-to-enterprise-security/),
verified 2026-08-02).

**Microsoft internal Zero Trust.** Microsoft Inside Track says Microsoft
adopted a Zero Trust security model internally, focused on verified identity,
verified device, verified access, and verified services. The same article says
Microsoft migrated users to internet-default networks, requires device health
for many high-traffic applications and services, and had transitioned 98
percent of workloads to internet-facing services at publication time
([Microsoft Inside Track](https://www.microsoft.com/insidetrack/blog/implementing-a-zero-trust-security-model-at-microsoft/),
verified 2026-08-02).

**NYC Cyber Command.** Google Cloud's customer story names NYC Cyber Command as
using a BeyondCorp security model and Cloud Identity-Aware Proxy so engineers
can access Google Cloud resources from untrusted networks without a VPN
([Google Cloud customer story](https://cloud.google.com/customers/nyc-cyber-command),
verified 2026-08-02). The source names the organization, the products, and the
access model.

**NTT Communications.** Microsoft customer documentation says NTT
Communications committed to Zero Trust security after hybrid-work needs and
cyberattacks on internal servers, migrated employee IDs to Entra ID, and moved
management of 40,000 Secured PCs to Intune
([Microsoft customer story](https://www.microsoft.com/en/customers/story/24348-ntt-communications-corporation-microsoft-intune),
verified 2026-08-02).

**U.S. Federal Civilian Executive Branch strategy.** OMB Memorandum M-22-09
directs Federal Civilian Executive Branch agencies toward a Zero Trust security
model and sets goals around identity, devices, networks, applications, and data
([OMB M-22-09](https://www.whitehouse.gov/wp-content/uploads/2022/01/M-22-09.pdf),
verified 2026-08-02). This is a policy mandate rather than one production
system, so it is weaker evidence than the named deployments above. It is still
relevant because it shows the pattern has become part of public-sector
architecture governance.

## 10. Consequences

This dimension is engineering judgement except where a specific source is
cited.

Positive.

- Access moves from network membership to named subject, resource, action, and
  context.
- A stolen credential or compromised laptop has a smaller blast radius when
  device state, MFA strength, and resource scope are checked.
- A resource owner can audit why a request was granted or denied.
- Legacy VPN dependencies shrink when private applications are published
  through resource-scoped access paths.
- Service-to-service traffic can use workload identity instead of source IP.
- Policy changes can be tested, staged, and measured before broad rollout.
- Telemetry from grants and denials gives security teams evidence for privilege
  reduction.

Negative.

- The decision plane becomes high-value infrastructure. If it is subverted, the
  attacker can grant access or hide denial data. NIST lists subversion of the
  ZTA decision process as a threat
  ([NIST SP 800-207](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-207.pdf),
  verified 2026-08-02).
- Users can face more denials during early rollout, especially when device
  inventory and application ownership are incomplete.
- Runtime latency increases when every request calls remote identity, posture,
  or policy systems.
- Teams can create policy sprawl with one-off exceptions for every resource.
- Telemetry and risk scoring create privacy obligations.
- Legacy protocols may need proxies or network segmentation because they cannot
  carry identity claims.
- Break-glass access becomes harder and must be designed before an outage.

## 11. Failure modes and misuse

This dimension is engineering judgement.

**Proxy-only rollout.** Symptom. The dashboard says the application is behind a
Zero Trust gateway, but once a user passes the gateway the application still
accepts any action for any tenant. Cause. The team protected the route but not
the resource action. Fix. Add application authorization or policy checks for
tenant, record, action, and data label.

**Flat network behind a new front door.** Symptom. A compromised host can scan
or call internal services after one allowed connection. Cause. The old
east-west reachability remained in place. Fix. Add microsegmentation, service
identity, and workload-level policy for internal paths.

**Shared service identity.** Symptom. Audit logs show `backend-service` for
many unrelated jobs, and no one can identify which job read a data set. Cause.
Many workloads reuse one token or certificate. Fix. Issue separate workload
identities per service, job, environment, and tenant boundary where needed.

**Policy exception pileup.** Symptom. Denials fall after rollout, but the allow
list grows every week and old exceptions have no owner. Cause. Exceptions are
treated as support tickets, not risk decisions. Fix. Require owner, reason,
expiry, and review state for each exception.

**Device posture as a single truth source.** Symptom. A compliant but infected
device keeps access because the endpoint system has not updated the posture
record. Cause. The policy trusts one stale signal. Fix. Add event-driven risk
updates, shorter posture lifetimes for high-risk resources, and defense in the
application.

**Fail-open decision outage.** Symptom. During an identity or policy outage,
users can reach resources that would normally require fresh evaluation. Cause.
The enforcement point was configured to permit when the decision service is
unreachable. Fix. Use fail-closed for high-value resources, local signed policy
bundles for availability, and narrow emergency roles.

**Opaque denials.** Symptom. Users retry, open support tickets, or find unsafe
workarounds because the denial only says "forbidden." Cause. The policy engine
returns no reason code or remediation path. Fix. Return safe denial categories
such as device not managed, MFA missing, location blocked, or policy expired.

**Policy drift across enforcement points.** Symptom. The same user can reach a
resource through one path but not another. Cause. Gateway, mesh, and
application policies were authored in different systems. Fix. Put shared policy
terms in one source of truth and test each path against the same cases.

**Telemetry without retention rules.** Symptom. Access logs contain device IDs,
user locations, resource names, and denial reasons long after they are needed.
Cause. Observability was added without privacy review. Fix. Classify telemetry,
limit labels, set retention, and restrict analyst access.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Zero Trust | Perimeter Firewall | Broad VPN | Bastion Host | Defense in Depth | Mutual TLS Only |
|---|---|---|---|---|---|---|
| Access basis | Subject, device, resource, action, context | Network zone | Network route plus login | Host login | Multiple controls | Certificate identity |
| Lateral movement | Narrow when scoped well | High after breach | High after route grant | Medium, centered on admin path | Depends on layers | Lower for service paths |
| Latency | Policy work per session or request | Low at boundary | Low after tunnel | Medium for admin sessions | Varies | Low to medium |
| Coupling | Shared identity and policy terms | Network topology | Network topology | Admin workflow | Many controls | PKI and service identity |
| Operability | Rich audit and denial data | Zone and flow logs | Tunnel logs | Session logs | Varies by layer | Handshake and cert logs |
| Cost | High rollout and ownership cost | Lower when already present | Low short-term cost | Moderate | High if unmanaged | Moderate PKI cost |
| Team fit | Security platform plus resource owners | Network team | Network team | Operations team | All teams | Platform team |
| Legacy fit | Needs proxy or segmentation | Strong | Strong | Strong for admin | Strong | Weak for old clients |
| Failure mode | Decision plane outage or policy sprawl | Flat trusted interior | Broad blast radius | Shared admin choke point | Layer confusion | Authenticated but overbroad access |
| Best use | Mixed networks, cloud, high-value resources | Basic boundary filtering | Temporary remote access | Controlled admin access | Independent backup controls | Service-to-service identity |

Reading of the table. Zero Trust wins when access must be resource-scoped and
context-aware. A perimeter firewall still belongs at network boundaries, but it
does not answer whether a managed laptop may read one payroll API. A broad VPN
is useful during migration and poor as a long-term authorization model. Mutual
TLS proves peer identity and protects transport, but it needs authorization
policy to become Zero Trust.

## 13. Related and incompatible patterns

- **Least Privilege.** Zero Trust applies least privilege to sessions and
  resources. Without least privilege, the pattern collapses into stronger login
  followed by broad access.
- **Complete Mediation.** The access decision must be checked at each relevant
  access path. Caching can exist, but stale grants need limits.
- **Defense in Depth.** Zero Trust composes with independent layers such as
  endpoint controls, segmentation, application authorization, logging, and data
  protection. Defense in Depth is broader and does not require identity-centric
  decisions.
- **Mutual TLS.** Mutual TLS is a common service identity and transport
  component. It does not express user, device, action, or data policy by itself.
- **ABAC.** Attribute-Based Access Control is a natural policy model for Zero
  Trust because decisions use subject, resource, action, and context
  attributes.
- **RBAC.** Role-Based Access Control can be one input. It is too coarse when
  roles become permanent bundles of broad access.
- **Federated Identity.** External workforce and partner access often need
  federation so the subject can be authenticated by an identity provider the
  enterprise trusts for that relationship.
- **Audit Log.** The pattern needs audit logs for grants, denials, policy
  changes, and emergency access.
- **Service Locator.** It conflicts when services find authority through a
  hidden global lookup rather than explicit identity and policy.
- **Flat Internal Network.** It actively conflicts because reachability becomes
  the permission.
- **Shared Credential.** It actively conflicts because the decision point cannot
  tie action to a real subject or workload.

## 14. Refactoring path in and out

Introducing the pattern into an existing estate.

1. Inventory the protected resources. Name applications, APIs, data stores,
   queues, admin interfaces, jobs, and owners.
2. Pick one high-value resource with a clear owner and a small user group. Do
   not start with the whole estate.
3. Replace shared accounts with named human and workload identities for that
   resource.
4. Put an enforcement point in the path. For a web app, use middleware or an
   access proxy. For service calls, use service identity or a mesh. For admin
   paths, use a resource-scoped access gateway.
5. Write the first policy in resource terms: subject, action, resource, device
   condition, session condition, and expiry.
6. Run in report-only mode where the risk permits it. Compare expected grants
   and denials with observed traffic.
7. Turn on enforcement for the smallest group. Record denial reasons and fix
   policy gaps before expanding.
8. Add local authorization in the application for domain rules that the gateway
   cannot know.
9. Add telemetry for decision inputs, policy version, result, latency, and
   resource.
10. Expand by resource class, not by tool. Each new resource gets an owner,
   policy, test cases, and rollback plan.

Named refactorings from the refactoring family often appear during adoption.
Replace Magic Number with Symbolic Constant helps remove ad hoc role codes.
Replace Conditional with Polymorphism can move per-resource policy behavior out
of a large switch. Extract Class can split identity, posture, and policy
queries out of request handlers. Introduce Parameter Object can carry decision
facts as a named access request instead of a long argument list.

Removing the pattern when it stops earning its place.

1. Identify the resource scope where the policy plane costs more than the risk
   reduction.
2. Confirm that local authorization remains correct without the external
   enforcement point.
3. Replace dynamic policy calls with a simpler local check or static allow list,
   and document the lower assurance.
4. Remove the enforcement point from the path only after traffic shadowing shows
   no hidden users.
5. Delete unused policy rules, device conditions, and telemetry labels.
6. Keep audit history for the retention period, then remove the resource from
   the access catalog.

The usual path out is not "return to trusted network." It is a narrower local
authorization model for a low-risk resource.

## 15. Testing and verification

This dimension is engineering judgement.

Unit tests should target the policy decision function with table-driven cases.
Each case names subject, device, resource, action, context, expected decision,
reason code, and policy version. Include negative cases for missing MFA, stale
device posture, wrong tenant, expired exception, and high-risk session.

Decision tests should be written before policy rollout because policy bugs are
often valid syntax with unsafe meaning. A good test case reads like an access
review: "managed payroll user with phishing-resistant MFA may read payroll
summary," "managed payroll user may not write payroll bank account," "unmanaged
device may not read restricted payroll data," and "break-glass user may perform
admin action only inside the emergency window." The value is not only the test
runner. The table gives policy owners a concrete artifact to approve.

Integration tests should run through the enforcement point, not only through
the policy library. A request that bypasses the gateway must fail or be
unroutable. A request with a valid identity but no resource grant must be
denied. A request with an old policy bundle must be denied or forced to refresh.

Contract tests are needed between context sources and the decision point. The
policy engine must know what "managed device," "high risk," "sensitive data,"
and "break glass" mean. Test those terms as versioned contracts because a field
rename in a posture feed can change authorization.

Replay tests are useful after an incident or near miss. Take a sampled set of
real access events, remove direct personal data, and evaluate them against the
new policy bundle. The expected result is not always "deny more." Sometimes the
right result is "deny a specific class of old grants while preserving normal
work." This catches broad rules that unit tests miss because production traffic
contains old clients, unusual groups, stale devices, and one-off admin paths.

Failure tests matter because the decision plane is now part of availability.
Test identity provider outage, policy store outage, stale posture feed, expired
certificates, clock skew, and telemetry sink failure. High-value resources
should fail closed. Lower-risk resources may use cached grants with strict
lifetimes and visible audit labels.

Verification in production has a different shape. Start in report-only mode and
measure false grants and false denials. Then enforce for a ring of users or one
resource group. Compare help-desk tickets, denial reasons, p95 decision latency,
and exception count before expanding.

For service-to-service paths, add a canary service with a known identity and a
known forbidden action. It should fail every minute from each environment. If it
ever succeeds, the team has evidence of an enforcement bypass or a policy
regression. Add the inverse canary as well: a known allowed action with a short
grant lifetime. If it fails, the decision path may be down or a context source
may be stale.

Useful test doubles include a fake identity provider with signed tokens, a fake
posture source with controllable device state, a test policy bundle, and a spy
telemetry sink. Avoid tests that mock the enforcement point away, because the
pattern lives at that boundary.

## 16. Observability signals

This dimension is engineering judgement.

Record these fields for every decision where volume allows it: subject
identifier class, workload identity, device identifier class, resource, action,
policy version, enforcement point, decision, reason code, decision latency,
grant lifetime, context source versions, and correlation identifier. Do not log
raw secrets, full tokens, or unnecessary personal data.

Separate decision telemetry from application telemetry even when the same
pipeline stores both. Application owners need resource and action counts.
Security operators need policy version, denial class, exception use, and
context freshness. Privacy reviewers need retention, field inventory, and
access control for the logs themselves. A single undifferentiated log stream
makes all three groups over-collect.

Healthy dashboards show a stable grant and denial mix for each resource, low
decision latency, low policy error rate, low stale-context rate, and a shrinking
set of long-lived exceptions. A new policy version should change decision
patterns only for the intended resources and rings.

Failing dashboards show denial spikes after a policy deploy, grant spikes after
an exception change, decision latency above application budgets, policy bundle
age rising, context feeds going stale, or many requests falling back to cached
grants. A flat zero-denial graph is suspicious for a sensitive resource. It may
mean the policy is too broad, the enforcement point is bypassed, or telemetry is
not wired.

Useful logs name the safe reason for denial. Examples: MFA required, device not
managed, device posture stale, resource outside grant, action blocked, data
label blocked, risk too high, policy expired, emergency role required. Operators
need these codes to distinguish a user fix from a policy fix.

Healthy observability also proves coverage. Track the percentage of resources
behind an enforcement point, the percentage of traffic with a named subject,
the percentage of service calls with workload identity, the percentage of
resources with an owner, and the percentage of policies with tests. These are
architecture coverage signals, not threat signals. They stop a team from
mistaking one successful gateway rollout for a complete access model.

Traces should include the enforcement point span, policy evaluation span, and
context lookup spans. Metrics should include decision count, deny count, policy
error count, cache hit count, cache age, policy bundle age, posture feed age,
and emergency access use.

## 17. Security and privacy implications

NIST lists several ZTA threats, including subversion of the decision process,
denial of service or network disruption, stolen credentials and insider threat,
visibility on the network, storage of system and network information, reliance
on proprietary data formats or solutions, and use of non-person entities in ZTA
administration
([NIST SP 800-207](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-207.pdf),
verified 2026-08-02). The pattern closes some attack paths and opens new ones.

Closed or reduced attack paths.

- Network location alone no longer grants access.
- VPN compromise grants less reach when access is resource-scoped.
- Stolen credentials face MFA, device posture, risk, and grant scope checks.
- Service calls can be tied to workload identity rather than host address.
- Lateral movement becomes more visible because internal calls produce policy
  decisions and telemetry.

Opened or increased attack paths.

- The policy decision point becomes a target. Protect its admin plane, policy
  store, signing keys, and deployment pipeline.
- Context feeds can be poisoned. A false healthy device state or false low-risk
  score can grant access.
- Enforcement points can be bypassed through old routes, direct service
  endpoints, or emergency tunnels.
- Policy authors can create broad exceptions that look legitimate in tooling.
- Logs can expose behavior patterns, resource names, locations, and device
  identifiers.

Privacy implications are direct. A mature deployment gathers access telemetry,
device state, location or network facts, risk decisions, and denial reasons.
Treat those records as sensitive operational data. Limit raw identifiers where a
stable pseudonymous label will work. Set retention by use case. Separate
security investigation access from routine application support access. Explain
to employees and partners what is collected for access control and what is not.

The pattern is silent on cryptographic algorithm choice, password storage,
input validation, output encoding, and secure coding inside a resource. Those
remain separate patterns and controls. Zero Trust decides whether a request may
reach or act on a resource. It does not make unsafe application code safe.

Break-glass access deserves separate security treatment. The emergency path
should be small, named, logged, time-limited, and tested. It should not be a
shared password in a vault that bypasses all policy. A good break-glass design
uses stronger proof, fewer users, shorter sessions, and louder alerting than
normal access. The point is to keep the organization able to recover when the
decision plane or identity provider is impaired, without creating a permanent
shadow administrator path.

Policy administration is also a software supply-chain concern. Policy changes
should be reviewed, tested, versioned, and deployed through a controlled path.
An attacker who can edit the policy bundle can often grant quieter access than
an attacker who steals one user's token. Treat policy code, policy data, and
policy signing keys as production assets.

## 18. References

1. John Kindervag. "No More Chewy Centers. The Zero-Trust Model Of Information
   Security." Forrester webinar, original broadcast August 9, 2010.
   https://www.forrester.com/webinar/No%2BMore%2BChewy%2BCenters%2BThe%2BZeroTrust%2BModel%2BOf%2BInformation%2BSecurity/WEB6741
   Verified 2026-08-02. Source for the naming lineage.
2. John Kindervag. "Build Security Into Your Network's DNA. The Zero Trust
   Network Architecture." Forrester report page.
   https://www.forrester.com/report/build-security-into-your-networks-dna-the-zero-trust-network-architecture/RES57047
   Verified 2026-08-02. Source for the Zero Trust Network Architecture label.
3. Scott Rose, Oliver Borchert, Stu Mitchell, Sean Connelly. *Zero Trust
   Architecture*. NIST Special Publication 800-207, August 2020, sections 1,
   2.1, 3, 3.1, 5, and 7.3.
   https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-207.pdf
   Verified 2026-08-02. Source for the public architecture definition, logical
   components, approaches, threats, and migration sequence.
4. Google. "BeyondCorp Zero Trust Enterprise Security."
   https://cloud.google.com/beyondcorp?hl=en
   Verified 2026-08-02. Source for Google's BeyondCorp description and internal
   production use.
5. Rory Ward and Betsy Beyer. "BeyondCorp. A New Approach to Enterprise
   Security." ;login:, Vol. 39, No. 6, 2014, pp. 6-11.
   https://research.google/pubs/beyondcorp-a-new-approach-to-enterprise-security/
   Verified 2026-08-02. Source for Google's move away from a privileged
   intranet.
6. Microsoft. "Zero Trust adoption framework overview." Microsoft Learn.
   https://learn.microsoft.com/en-us/security/zero-trust/adopt/zero-trust-adoption-overview
   Verified 2026-08-02. Source for the three Microsoft Zero Trust principles
   and adoption framing.
7. Microsoft. "Implementing a Zero Trust security model at Microsoft." Inside
   Track, April 24, 2025.
   https://www.microsoft.com/insidetrack/blog/implementing-a-zero-trust-security-model-at-microsoft/
   Verified 2026-08-02. Source for Microsoft's internal production use.
8. Google Cloud. "NYC Cyber Command. Keeping New York City's digital services
   more secure at massive scale."
   https://cloud.google.com/customers/nyc-cyber-command
   Verified 2026-08-02. Source for NYC Cyber Command's BeyondCorp and
   Identity-Aware Proxy use.
9. Microsoft. "NTT Communications achieves a safe hybrid work environment with
   Microsoft Entra ID and Intune." Microsoft Customer Stories.
   https://www.microsoft.com/en/customers/story/24348-ntt-communications-corporation-microsoft-intune
   Verified 2026-08-02. Source for NTT Communications production use.
10. Office of Management and Budget. *Moving the U.S. Government Toward Zero
   Trust Cybersecurity Principles*. Memorandum M-22-09, January 26, 2022.
   https://www.whitehouse.gov/wp-content/uploads/2022/01/M-22-09.pdf
   Verified 2026-08-02. Source for federal strategy context.

## Code examples

The examples model the policy decision at the heart of the pattern. TypeScript
fits web access middleware, Python fits policy testing and internal tools, and
Go fits service-side authorization in small binaries. Each sample is local,
small, and runnable without a framework.

### TypeScript

```typescript
type Subject = { id: string; mfa: boolean; groups: string[] };
type Device = { managed: boolean; healthy: boolean };
type Resource = { name: string; sensitivity: "normal" | "restricted" };
type AccessRequest = {
  subject: Subject;
  device: Device;
  resource: Resource;
  action: "read" | "write";
};

type Decision = { allow: boolean; reason: string };

function decide(req: AccessRequest): Decision {
  if (!req.subject.mfa) return { allow: false, reason: "mfa_required" };
  if (!req.device.managed || !req.device.healthy) {
    return { allow: false, reason: "device_not_trusted" };
  }
  if (req.resource.sensitivity === "restricted") {
    const ok = req.subject.groups.includes("payroll") && req.action === "read";
    return ok
      ? { allow: true, reason: "least_access_grant" }
      : { allow: false, reason: "resource_scope_denied" };
  }
  return { allow: true, reason: "normal_resource" };
}

const request: AccessRequest = {
  subject: { id: "u123", mfa: true, groups: ["payroll"] },
  device: { managed: true, healthy: true },
  resource: { name: "payroll-report", sensitivity: "restricted" },
  action: "read",
};

console.log(decide(request));
```

### Python

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Subject:
    name: str
    mfa: bool
    groups: set[str]


@dataclass(frozen=True)
class Device:
    managed: bool
    healthy: bool


@dataclass(frozen=True)
class Request:
    subject: Subject
    device: Device
    resource: str
    action: str


def decide(req: Request) -> tuple[bool, str]:
    if not req.subject.mfa:
        return False, "mfa_required"
    if not req.device.managed or not req.device.healthy:
        return False, "device_not_trusted"
    if req.resource == "payroll" and "payroll" not in req.subject.groups:
        return False, "resource_scope_denied"
    if req.action == "admin" and "break-glass" not in req.subject.groups:
        return False, "admin_denied"
    return True, "grant"


if __name__ == "__main__":
    req = Request(
        Subject("u123", True, {"payroll"}),
        Device(True, True),
        "payroll",
        "read",
    )
    print(decide(req))
```

### Go

```go
package main

import "fmt"

type Subject struct {
	Name   string
	MFA    bool
	Groups map[string]bool
}

type Device struct {
	Managed bool
	Healthy bool
}

type Request struct {
	Subject  Subject
	Device   Device
	Resource string
	Action   string
}

func Decide(req Request) (bool, string) {
	if !req.Subject.MFA {
		return false, "mfa_required"
	}
	if !req.Device.Managed || !req.Device.Healthy {
		return false, "device_not_trusted"
	}
	if req.Resource == "payroll" && !req.Subject.Groups["payroll"] {
		return false, "resource_scope_denied"
	}
	if req.Action == "admin" && !req.Subject.Groups["break-glass"] {
		return false, "admin_denied"
	}
	return true, "grant"
}

func main() {
	req := Request{
		Subject:  Subject{"u123", true, map[string]bool{"payroll": true}},
		Device:   Device{Managed: true, Healthy: true},
		Resource: "payroll",
		Action:   "read",
	}
	fmt.Println(Decide(req))
}
```
