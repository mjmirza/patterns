---
name: STRIDE
slug: stride
family: 15-security
category: Security
aliases: [STRIDE Threat Modeling, STRIDE per Element, STRIDE Taxonomy]
first_described: "Kohnfelder and Garg 1999"
maturity: established
related: [threat-modeling, defense-in-depth, least-privilege, complete-mediation, audit-log, zero-trust]
incompatible_with: [checklist-compliance, unsourced-risk-scoring, attacker-free-threat-modeling]
verified: 2026-08-02
---

# STRIDE

## 1. Name, aliases, and lineage

The canonical name is STRIDE. The name is an acronym for six threat prompts:
Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service,
and Elevation of Privilege. Microsoft Learn describes the same six categories
in its Threat Modeling Tool threat list and says Microsoft uses STRIDE to group
threats so teams can form pointed security questions
([Microsoft Learn, "Microsoft Threat Modeling Tool threats"](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats),
verified 2026-08-02).

The common aliases are **STRIDE Threat Modeling**, **STRIDE per Element**, and
**STRIDE taxonomy**. The first means the team uses STRIDE as the threat
identification method inside a broader threat modeling activity. The second
means each element in a system model is examined against the STRIDE categories.
The third means STRIDE is used only as a labelling scheme for threats found by
another method. Microsoft Learn's archived getting started page for the Threat
Modeling Tool summarizes the older SDL method as diagramming, identifying
threats, mitigating them, and validating each mitigation
([Microsoft Learn, "Getting started with the Threat Modeling Tool"](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-getting-started),
verified 2026-08-02).

Microsoft gives the lineage most teams recognize. Its DevOps threat modeling
paper says Loren Kohnfelder and Praerit Garg wrote "The threats to our
products" at Microsoft in 1999, and that the paper introduced STRIDE as a
synonym for the Microsoft threat modeling process
([Microsoft Learn, "Integrating threat modeling with DevOps"](https://learn.microsoft.com/en-us/security/engineering/threat-modeling-with-dev-ops),
verified 2026-08-02). Adam Shostack later taught STRIDE as one way to answer
"what can go wrong" in *Threat Modeling. Designing for Security*, Wiley, 1st
edition, 2014, chapters 1 through 4. This entry cites Shostack by chapter, not
page, because no page image was confirmed for this entry.

STRIDE is not the whole threat modeling pattern. The Threat Modeling Manifesto
frames the practice around four questions: what the team is working on, what
can go wrong, what response the team will take, and whether the work is good
enough ([Threat Modeling Manifesto](https://www.threatmodelingmanifesto.org/),
verified 2026-08-02). STRIDE answers the second question. It does not draw the
system, value assets, choose owners, rank risk, or prove fixes. Treating STRIDE
as the whole model is the most common misuse.

## 2. Problem and context

A team has an architecture sketch, a data flow, a new feature, or a service
boundary, and needs a disciplined way to ask security questions before the
design becomes expensive to change. Free-form brainstorming finds what the
loudest participant already knows. Scanner output arrives after code exists.
Incident reviews arrive after damage. STRIDE gives the team six prompts that
force attention across identity, integrity, accountability, confidentiality,
availability, and authorization.

The situation appears in codebases whenever a design contains an actor, a
process, a data store, a trust boundary, a queue, an API, an operator console,
or a service-to-service call. A web application adds webhooks, and the team
needs to ask how a sender can be spoofed or a payload can be changed. A worker
reads from a queue, and the team needs to ask whether one tenant can poison
another tenant's job. A control plane adds a self-service admin action, and the
team needs to ask what audit evidence exists when the action is denied later.
A public endpoint accepts uploads, and the team needs to ask both information
disclosure and denial of service questions.

Microsoft describes threat modeling as a core element of the Microsoft Security
Development Lifecycle and as an engineering technique for identifying threats,
attacks, vulnerabilities, and countermeasures that can affect an application
([Microsoft Security Engineering, "Threat Modeling"](https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling),
verified 2026-08-02). The same page lists five major steps: define security
requirements, create an application diagram, identify threats, mitigate
threats, and validate mitigations. STRIDE belongs inside that third step.

The context matters because STRIDE is a prompt set, not a threat oracle. It is
productive when the team has a bounded model and enough system knowledge to
turn each category into a concrete scenario. It is weak when the system model
is vague, the asset owner is absent, or the output cannot become owned work.
OWASP's Threat Modeling Cheat Sheet says threat modeling commonly includes
system modeling, threat identification, and risk response, and notes that no
single industry process is universal
([OWASP Threat Modeling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html),
verified 2026-08-02).

## 3. Forces

Engineering judgement: this dimension weighs trade-offs from practice. The
citations identify public guidance and named tools; the balancing below is
design reasoning.

- **Coverage versus depth.** STRIDE widens coverage by forcing six categories
  across the model. It sacrifices depth when a team stops at category labels
  rather than writing concrete threat statements.
- **Speed versus precision.** STRIDE is quick to teach. The cost is that its
  terms are broad. "Tampering" can mean a changed HTTP body, a poisoned build
  artifact, a modified database row, or a changed log record.
- **Consistency versus domain fit.** A shared taxonomy lets teams compare
  threat registers across services. Domain-specific attacks may need another
  source, such as abuse cases, ATT&CK, CAPEC, LINDDUN, or product incident
  data.
- **Coupling.** STRIDE couples each threat to a model element. That improves
  traceability, but it can hide business workflow abuse that spans many
  elements and does not live neatly inside one box or arrow.
- **Latency.** The activity adds no runtime latency. Responses derived from it
  can add latency through authentication, integrity checks, rate limits,
  logging, token exchange, and extra authorization decisions.
- **Consistency of security properties.** STRIDE maps categories to familiar
  security properties: authentication, integrity, non-repudiation or
  accountability, confidentiality, availability, and authorization. Microsoft
  Azure secure design guidance presents those mappings in a STRIDE mitigation
  table for Azure platform controls
  ([Microsoft Learn, "Design secure applications on Microsoft Azure"](https://learn.microsoft.com/en-us/azure/security/develop/secure-design),
  verified 2026-08-02).
- **Operability.** Good STRIDE output gives operators test cases and signals.
  Weak output gives labels with no logs, traces, dashboards, or runbooks.
- **Cost.** The method is cheap to introduce because it is mnemonic. It becomes
  costly when applied mechanically to every element in a large graph without
  scoping or triage.
- **Team topology.** Product teams can own concrete threats because the prompts
  do not require rare expertise. Security teams still need to coach quality,
  because novices often confuse category naming with threat discovery.
- **Cognitive load.** STRIDE lowers initial load through six repeatable words.
  It raises later load when multiple categories apply to the same scenario and
  the team debates labels instead of fixes.

The pattern favours repeatable questioning and comparability. It sacrifices
some domain richness and can create category theater when facilitation is weak.

## 4. Applicability and non-applicability

Reach for STRIDE when the following hold.

- A team has a data flow diagram, sequence diagram, architecture sketch, API
  route list, cloud resource graph, or code-derived model that can be examined
  element by element.
- The goal is to identify what can go wrong in a software or infrastructure
  design, not to score an already known vulnerability.
- The system includes identities, trust boundaries, data stores, cross-process
  communication, administrative capabilities, tenant separation, or external
  integrations.
- The team needs a low-ceremony method that engineers, product owners,
  security reviewers, and SREs can learn in one session.
- The output will become threat statements with owners, mitigations, tests, and
  acceptance or deferral records.
- The team wants to compare threats across services using a stable vocabulary.
- A threat modeling tool or rules engine will generate starter prompts from
  model elements, and human review will decide what is real.

Do NOT reach for STRIDE in these cases.

- **No system model exists.** STRIDE needs a target. First draw the feature,
  data flow, deployment path, or code path.
- **The problem is privacy-first.** STRIDE can find information disclosure, but
  privacy work often needs prompts for linkability, identifiability,
  detectability, user awareness, and compliance. LINDDUN defines privacy threat
  types for that job ([LINDDUN threat types](https://linddun.org/threat-types/),
  verified 2026-08-02).
- **The threat is business workflow abuse.** A refund loop, coupon race, market
  manipulation path, or moderation evasion path may cross many elements. Use
  abuse cases or business logic threat modeling rather than forcing the issue
  into one STRIDE label.
- **The team already has a live incident.** Incident response, containment, and
  forensic work come first. STRIDE can help the follow-up design review.
- **The team needs adversary behavior detail.** STRIDE says "what property can
  fail." It does not model reconnaissance, lateral movement, persistence, or
  command and control. Use ATT&CK or an attack tree when those steps matter.
- **The team needs quantitative risk.** STRIDE does not supply likelihood,
  impact, loss magnitude, or risk appetite. Pair it with a risk method if those
  values drive decisions.
- **The output will be labels only.** "Information disclosure on database" is
  not a threat statement. If nobody will write cause, path, impact, owner, and
  response, the activity is not earning its time.
- **The target is a low-risk static asset.** A static public page with no user
  data, secrets, identity, backend state, or privileged action may be served
  better by a short checklist.
- **The team wants a scanner substitute.** STRIDE can create test ideas, but it
  will not find vulnerable package versions, missing compiler flags, weak TLS
  settings, or injection bugs in source code.
- **The facilitator cannot stop category debates.** If the group spends its
  time arguing whether a scenario is tampering or elevation of privilege, switch
  to threat statements first and label later.

## 5. Structure

STRIDE has six prompt roles and five supporting participants.

- **Spoofing prompt.** Ask who or what can pretend to be another subject,
  service, device, tenant, job, operator, webhook sender, or data source. The
  usual control families are authentication, identity binding, mutual
  authentication, signed messages, and replay resistance.
- **Tampering prompt.** Ask who can modify data, code, configuration, requests,
  responses, queues, logs, builds, images, state machines, or model context
  without authorization. The usual control families are integrity checks,
  validation, authorization, immutable storage, and signed artifacts.
- **Repudiation prompt.** Ask who can deny an action, erase evidence, create
  ambiguous records, or perform work through a shared identity. The usual
  control families are audit logs, time synchronization, actor binding, request
  IDs, approvals, and tamper-evident records.
- **Information Disclosure prompt.** Ask who can read data, metadata, secrets,
  tokens, logs, errors, backups, model prompts, query results, or traffic that
  they should not see. The usual control families are access control,
  encryption, output encoding, data minimization, masking, and tenancy checks.
- **Denial of Service prompt.** Ask who can exhaust CPU, memory, sockets,
  threads, queues, storage, retries, quotas, tokens, locks, rate budgets,
  external dependencies, or operator attention. The usual control families are
  rate limits, backpressure, timeouts, quotas, isolation, and graceful
  degradation.
- **Elevation of Privilege prompt.** Ask who can gain a capability beyond their
  intended role, tenant, process, sandbox, workflow step, service account, or
  execution context. The usual control families are least privilege, complete
  mediation, privilege separation, policy checks, sandboxing, and defense in
  depth.

The supporting participants make the prompts actionable.

- **Model element.** A process, data flow, data store, external actor, trust
  boundary, identity provider, queue, job, control plane, plugin, or operator
  action.
- **Threat statement.** A concrete sentence that names actor, prerequisite,
  action, impact, and asset. AWS's generative AI threat modeling blog describes
  a threat grammar with those fields and says AWS uses such statements in
  threat modeling
  ([AWS Security Blog, "Threat modeling your generative AI workload to evaluate security risk"](https://aws.amazon.com/blogs/security/threat-modeling-your-generative-ai-workload-to-evaluate-security-risk/),
  verified 2026-08-02).
- **Mitigation.** A design or control that reduces, removes, transfers, or
  accepts the threat under explicit ownership.
- **Verification.** A test, review, simulation, monitor, or runbook that shows
  whether the mitigation works.
- **Owner.** The person or team accountable for the threat state, not merely
  the meeting participant who wrote it down.

The relationship is simple. Model elements receive STRIDE prompts. Prompts
produce candidate threats. Candidate threats are rewritten into statements.
Statements receive responses. Responses receive verification and owners.

## 6. ASCII structure diagram

```text
  +-----------------------+      apply prompts       +------------------+
  |    system model       | -----------------------> | STRIDE prompts   |
  |-----------------------|                          |------------------|
  | actors                |                          | S  spoofing      |
  | processes             |                          | T  tampering     |
  | data stores           |                          | R  repudiation   |
  | data flows            |                          | I  info disclose |
  | trust boundaries      |                          | D  denial svc    |
  +-----------------------+                          | E  privilege     |
             |                                       +------------------+
             | candidate threats                              |
             v                                                v
  +-----------------------+      refine          +----------------------+
  | threat statements     | -------------------> | response backlog     |
  |-----------------------|                      |----------------------|
  | actor                 |                      | mitigation           |
  | prerequisite          |                      | owner                |
  | action                |                      | verification         |
  | impact                |                      | accepted residual    |
  | asset                 |                      | review trigger       |
  +-----------------------+                      +----------------------+
```

## 7. Dynamics

At runtime STRIDE is not a software component. The dynamics are the review flow
that converts a model into backlog and tests.

```text
Facilitator       Owning team       System model       STRIDE table       Backlog
     |                 |                 |                  |                |
     | set scope       |                 |                  |                |
     |---------------->|                 |                  |                |
     |                 | draw elements   |                  |                |
     |                 |---------------->|                  |                |
     | select element  |                 |                  |                |
     |---------------------------------->|                  |                |
     | ask S,T,R,I,D,E |                 |                  |                |
     |----------------------------------------------------->|                |
     |                 | propose scenario|                  |                |
     |<----------------|                 |                  |                |
     | rewrite as threat statement       |                  |                |
     |---------------->|                 |                  |                |
     |                 | choose response |                  |                |
     |                 |--------------------------------------------------->|
     |                 | add owner, test, review trigger                   |
     |                 |--------------------------------------------------->|
     | next element    |                 |                  |                |
     |---------------------------------->|                  |                |
```

The loop should be bounded. A practical session chooses the riskiest elements
first: internet entry points, trust boundary crossings, identity and
authorization decisions, persistent stores, queues, privileged automation, and
operator paths. Exhaustive STRIDE per element is defensible for small models.
For large systems, engineering judgement should triage elements by asset value,
exposure, privilege, blast radius, and rate of change.

STRIDE dynamics also include refresh triggers. Rerun the prompts when a new
identity provider appears, a data flow crosses a new trust boundary, a queue is
shared by tenants, a service account gains a role, a public API gains a write
operation, a storage class changes, or an incident shows that an assumption was
false. Without triggers, the model becomes a historical artifact.

## 8. Implementation variants

**Whiteboard STRIDE.** A facilitator walks a small group through the six
prompts against a hand-drawn model. It is fast, cheap, and good for new design.
It fails when nobody records concrete statements or owners.

**STRIDE per element.** Each DFD element is checked against applicable STRIDE
categories. Microsoft Threat Modeling Tool guidance describes generated threat
categories from a diagram in the SDL tool chain
([Microsoft Security Engineering, "Threat Modeling"](https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling),
verified 2026-08-02). This variant gives repeatability. It can also produce
long lists of low-value generated threats.

**STRIDE per interaction.** The review focuses on data flows and call paths
rather than boxes. It is strong for service-to-service calls, queues, webhooks,
event streams, and API gateways. It can miss privileged local operations inside
one process.

**STRIDE as metadata.** Threats are discovered through incidents, abuse cases,
or attack trees, then tagged with STRIDE. AWS Security Agent's CreateThreat API
has a `stride` array whose valid values are the six STRIDE categories
([AWS Security Agent API, "CreateThreat"](https://docs.aws.amazon.com/securityagent/latest/APIReference/API_CreateThreat.html),
verified 2026-08-02). This variant helps reporting and filtering but does not
itself discover threats.

**Rules engine STRIDE.** A tool generates threats based on model element type,
trust boundary, protocol, and data classification. OWASP Threat Dragon says it
supports STRIDE and implements a rule engine to auto-generate threats and
mitigations
([OWASP Threat Dragon project](https://owasp.org/www-project-threat-dragon/),
verified 2026-08-02). This variant scales the first pass. Human review remains
needed because rules do not know the full business context.

**Code-derived STRIDE.** A tool extracts routes, services, cloud resources, or
source paths, then creates promptable model elements. AWS announced that AWS
Security Agent can analyze design documents or source code and identify threats
with recommended mitigations using STRIDE
([AWS What's New, "AWS Security Agent announces support for Threat Modeling"](https://aws.amazon.com/about-aws/whats-new/2026/06/aws-security-agent-threat-modeling/),
verified 2026-08-02). This variant reduces blank-page time. It can overtrust
source code and miss business assets, data sensitivity, or planned behavior.

**STRIDE plus risk method.** STRIDE identifies scenarios, then a separate method
prioritizes them. Use this when many threats are valid but backlog capacity is
limited. Do not pretend STRIDE alone has ranked the work.

**STRIDE plus privacy method.** Use STRIDE for security properties and LINDDUN
or a privacy impact process for privacy properties. This avoids hiding privacy
concerns under the single information disclosure category.

## 9. Known production uses

- **Microsoft SDL and Microsoft Threat Modeling Tool.** Microsoft says threat
  modeling is a core element of its SDL, and its Threat Modeling Tool helps
  architects identify classes of threats from the structure of a software
  design ([Microsoft Security Engineering, "Threat Modeling"](https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling),
  verified 2026-08-02). Microsoft Learn's Threat Modeling Tool threat page says
  Microsoft uses STRIDE to categorize threat types
  ([Microsoft Learn, "Microsoft Threat Modeling Tool threats"](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats),
  verified 2026-08-02). Microsoft also says the SDL became an integral part of
  its software development process in 2004 and continues to be fundamental to
  how it develops products and services
  ([Microsoft Security Engineering, "About the Microsoft SDL"](https://www.microsoft.com/en-us/securityengineering/sdl/about),
  verified 2026-08-02).
- **OWASP Threat Dragon.** OWASP Threat Dragon is an OWASP Production status
  project, runs as a web or desktop application, supports STRIDE, and includes a
  rule engine to generate threats and mitigations
  ([OWASP Threat Dragon project](https://owasp.org/www-project-threat-dragon/),
  verified 2026-08-02). This is a named production tool use, not merely a
  teaching example.
- **AWS Security Agent.** AWS announced in June 2026 that AWS Security Agent,
  now part of AWS Continuum, includes threat modeling that identifies threats
  with recommended mitigations using STRIDE
  ([AWS What's New, "AWS Security Agent announces support for Threat Modeling"](https://aws.amazon.com/about-aws/whats-new/2026/06/aws-security-agent-threat-modeling/),
  verified 2026-08-02). Its API reference includes `stride` as a field on a
  threat, with the six STRIDE category values
  ([AWS Security Agent API, "CreateThreat"](https://docs.aws.amazon.com/securityagent/latest/APIReference/API_CreateThreat.html),
  verified 2026-08-02).
- **OWASP pytm.** OWASP pytm is a Python framework for threat modeling. Its
  repository describes automatic generation of data flow diagrams, sequence
  diagrams, and relevant threats from an architectural design
  ([OWASP pytm repository](https://github.com/OWASP/pytm),
  verified 2026-08-02). Engineering judgement: pytm is a production use of
  automated threat modeling ideas adjacent to STRIDE, but the stronger STRIDE
  claim in this entry comes from Threat Dragon, Microsoft, and AWS.

## 10. Consequences

Engineering judgement: the lists below describe likely outcomes when STRIDE is
used with a real model and owned follow-up.

Positive consequences.

- The team gets a shared vocabulary for six common security failure classes.
- Design review becomes less dependent on the memory of one security expert.
- The model gains traceability from element to threat, mitigation, and test.
- Threat registers can be filtered by security property, owner, component, and
  control family.
- The method exposes missing assumptions. For example, a spoofing prompt often
  reveals that a service trusts a header, and a repudiation prompt often
  reveals shared admin accounts.
- Tooling can generate starter prompts for novices, which reduces blank-page
  friction.
- The output can drive negative tests, rate tests, audit tests, and abuse case
  tests.

Negative consequences.

- Teams may write labels instead of threats. "Tampering" is not a scenario.
- Generated threats can overwhelm a backlog when the model is large.
- STRIDE can underrepresent business logic, privacy, and adversary campaign
  detail.
- The acronym can become a meeting ritual that gives false confidence.
- Multiple categories often apply to one scenario, causing unhelpful debates.
- If every category is applied to every element without triage, the session can
  waste expert time on low-risk elements.
- Tool-generated output may be accepted without understanding why a threat
  applies.
- The method can age poorly if model refresh triggers are missing.

## 11. Failure modes and misuse

Engineering judgement: each triple names an observable symptom, likely cause,
and fix.

- **Symptom.** The threat register contains many rows such as "Spoofing on API"
  with no actor, prerequisite, action, asset, or impact. **Cause.** The team
  recorded categories instead of threat statements. **Fix.** Require each row
  to follow a sentence shape: an actor with a condition can take an action,
  causing impact to an asset.
- **Symptom.** Backlog items from the model never close, and the same threats
  reappear in later reviews. **Cause.** The session produced findings without
  owners, acceptance criteria, or verification. **Fix.** Do not leave the
  session until every open threat has owner, response, target date, and test or
  acceptance record.
- **Symptom.** Participants argue for ten minutes about whether a scenario is
  tampering or elevation of privilege. **Cause.** Labels are being treated as
  the goal. **Fix.** Write the threat and mitigation first, then allow multiple
  STRIDE tags if reporting needs them.
- **Symptom.** The model misses a refund abuse path, signup fraud path, or
  moderation evasion path. **Cause.** STRIDE per element focused on technical
  boxes and ignored workflow incentives. **Fix.** Add abuse cases and business
  process walkthroughs for value-bearing workflows.
- **Symptom.** The output contains every generated threat from a tool, but
  engineers cannot explain why half of them apply. **Cause.** Rules engine
  output was accepted as analysis. **Fix.** Mark generated threats as draft and
  require human confirmation, rejection reason, or rewrite.
- **Symptom.** Operators cannot detect whether a mitigation is working in
  production. **Cause.** The model named preventive controls but no telemetry.
  **Fix.** Add observability requirements for each high-risk threat: log fields,
  counters, alerts, traces, and runbook checks.
- **Symptom.** A new tenant flow ships without review even though an old model
  exists. **Cause.** The model has no refresh triggers tied to architecture
  changes. **Fix.** Add change triggers for identity, trust boundary, tenant,
  privilege, data classification, and public API changes.
- **Symptom.** Privacy review keeps reopening STRIDE findings. **Cause.** The
  team used information disclosure as a catch-all for privacy issues. **Fix.**
  Pair STRIDE with a privacy method and keep privacy outcomes separately owned.
- **Symptom.** Denial of service threats are accepted as "not security" and
  left unowned. **Cause.** The team treats security only as confidentiality.
  **Fix.** Tie availability threats to user harm, SLOs, cost ceilings, queue
  depth, and incident response.
- **Symptom.** The same service account appears as a mitigation for many
  threats and also as a source of privilege escalation. **Cause.** The model
  failed to distinguish control identity from workload identity. **Fix.** Split
  identities by component and task, then rerun spoofing and elevation prompts.

## 12. Trade-off matrix

| Method | Best fit | Coupling | Operability | Cost | Team load | Main sacrifice |
|---|---|---|---|---|---|---|
| STRIDE | Software design threat discovery from a model | Ties threats to elements | Good when linked to tests and logs | Low to medium | Low entry load | Business workflow and privacy depth |
| Attack Trees | Attacker goal decomposition | Ties paths to attacker goals | Good for path testing | Medium | Higher analysis load | Slower for broad first pass |
| Abuse Cases | User or adversary misuse of product workflows | Ties threats to user stories | Good for product tests | Low to medium | Product context needed | Less systematic across infrastructure |
| LINDDUN | Privacy threat modeling | Ties threats to privacy properties | Good for privacy review | Medium | Privacy expertise needed | Does not replace security prompts |
| PASTA | Risk-centric application threat modeling | Ties threats to business impact | Strong for risk decisions | High | High facilitation load | Too heavy for many feature reviews |
| MITRE ATT&CK | Adversary tactics and techniques | Ties threats to observed attack behavior | Strong for detection engineering | Medium | Security operations knowledge needed | Weak for early product design |
| OWASP ASVS Review | Control requirement review for applications | Ties findings to verification controls | Strong for test planning | Medium | AppSec knowledge needed | Starts from controls, not attacker scenarios |

STRIDE is the lightest broad prompt set in this table. Engineering judgement:
use it as the first pass when the team lacks a better domain method, then add a
more specific method where the product risk calls for it.

## 13. Related and incompatible patterns

**Threat Modeling** is the parent pattern. STRIDE supplies one threat
identification method inside it. A threat model without STRIDE can still be
valid. STRIDE without a model, response, and validation is incomplete.

**Defense in Depth** composes with STRIDE because many threats deserve more
than one control. A spoofed webhook might need sender authentication, payload
signatures, replay windows, idempotency keys, audit logs, and rate limits.

**Least Privilege** is the common response to elevation of privilege findings.
It also reduces blast radius for tampering and information disclosure threats.

**Complete Mediation** composes with STRIDE when each request, queue message,
or object access needs an authorization decision. It is often the fix for
spoofing, tampering, information disclosure, and elevation scenarios.

**Audit Log** composes with repudiation. It is not enough to record an action;
the record must bind actor, target, time, authority, request context, and result
in a way operators can query.

**Zero Trust** generalizes several STRIDE responses. It removes implicit trust
from networks and calls, which helps with spoofing, tampering, information
disclosure, and elevation scenarios.

**Abuse Case** can replace STRIDE for workflows where value extraction matters
more than element-level technical prompts.

**LINDDUN** is not incompatible. It complements STRIDE for privacy. Do not
collapse privacy into information disclosure when the privacy question concerns
linking, identifying, detection, awareness, or consent.

**Checklist compliance** conflicts with STRIDE when the organization wants a
filled template instead of design change. The conflict is not with checklists as
memory aids; it is with checklist completion as a substitute for threat
reasoning.

**Unsourced risk scoring** conflicts with STRIDE when teams assign numbers to
category labels without evidence, impact owner input, or acceptance criteria.

## 14. Refactoring path in and out

To introduce STRIDE into a team that already ships software:

1. Pick one bounded target: a new feature, API, service, queue flow, admin path,
   or tenant boundary.
2. Draw the smallest model that explains actors, processes, data stores, data
   flows, and trust boundaries.
3. Select high-risk elements first: public entry points, authentication,
   authorization, state writes, cross-tenant data, privileged automation, and
   third-party callbacks.
4. Ask each STRIDE prompt against the selected element or interaction.
5. Rewrite valid answers as concrete threat statements.
6. Assign response: mitigate, remove design choice, transfer responsibility, or
   accept with owner and reason.
7. Convert mitigations into backlog items and tests.
8. Add observability requirements for high-risk threats.
9. Store the model with the design record or service documentation.
10. Add refresh triggers to pull the model back into review when the design
    changes.

Refactor a weak STRIDE practice into a stronger one:

1. Delete duplicate category-only rows.
2. Merge threats that share the same actor, path, asset, and fix.
3. Split rows that contain more than one actor or impact.
4. Replace vague mitigations such as "add validation" with buildable controls.
5. Add owner and verification fields to every open threat.
6. Mark generated threats as generated until a human confirms them.
7. Add acceptance records for threats the team will not mitigate.

To remove STRIDE when it stops earning its place:

1. Identify which domain method now does better work: abuse cases, LINDDUN,
   attack trees, ATT&CK, ASVS, PASTA, or incident-driven review.
2. Preserve existing threat statements, owners, tests, and residual risk
   records.
3. Keep STRIDE tags as historical metadata if reports depend on them.
4. Stop requiring STRIDE per element for low-risk changes.
5. Add a trigger that brings STRIDE back for identity, trust boundary,
   privilege, or tenant changes.

Cross reference the refactoring family entries on Extract Function and Replace
Conditional with Polymorphism when STRIDE findings reveal tangled authorization
or validation code. Cross reference Introduce Parameter Object when threat
statements need a stable request context object for actor, tenant, capability,
asset, and trace ID.

## 15. Testing and verification

Engineering judgement: STRIDE improves testing when each threat becomes one or
more falsifiable checks.

Test spoofing by attempting requests with missing identity, forged identity,
expired tokens, wrong audience, wrong issuer, replayed signatures, stale
certificates, confused tenant claims, and service accounts from the wrong
environment.

Test tampering by changing request bodies, query parameters, queue messages,
JWT claims, object IDs, webhook payloads, client-side state, build artifacts,
and configuration. The expected result should be rejection, quarantine,
read-only handling, or a logged policy decision.

Test repudiation by checking that actions bind actor, tenant, request ID,
target, authority source, decision, time, and result. Shared accounts should
fail the test unless a compensating approval or session binding exists.

Test information disclosure with cross-tenant reads, verbose errors, log
scrapes, backup access, search indexes, object storage paths, cache keys,
browser storage, trace payloads, model prompts, and support tooling.

Test denial of service with rate tests, quota tests, timeout tests, retry storm
tests, queue saturation tests, large payload tests, lock contention tests, and
dependency failure tests. Tie expected behavior to SLOs and cost ceilings.

Test elevation of privilege with role changes, direct object references,
workflow skips, tenant switches, confused deputy calls, plugin capabilities,
sandbox escapes, service account permissions, and admin-only routes.

Test doubles should represent external identity providers, webhook senders,
object stores, queues, and policy engines. Avoid doubles that always approve or
always return well-formed data, because they erase the threat. Property-based
tests are useful for tampering and input boundaries. Contract tests are useful
for signed messages and service identity. Chaos tests are useful for denial of
service and dependency failure.

Verification for the threat model itself is separate from code tests. Review
whether the model still matches production, whether every open high-risk threat
has an owner, whether accepted risks are still acceptable, whether mitigations
have tests, and whether incidents or near misses created new prompts.

## 16. Observability signals

Engineering judgement: observability should make STRIDE assumptions visible
without logging secrets or personal data.

For spoofing, log authentication result, issuer, audience, credential type,
token age bucket, certificate fingerprint hash, replay result, and actor
binding failures. A healthy dashboard shows low rejected-auth rates with
explainable spikes during deploys or token rotation. A failing dashboard shows
issuer mismatches, replay attempts, unknown key IDs, or sudden cross-tenant
identity failures.

For tampering, log integrity check failures, schema rejection reason, signature
failure, policy decision, object version mismatch, and write conflict. A
healthy system has rare tamper rejections and no sustained growth. A failing
system has repeated payload changes from one source, high queue poison rates,
or writes rejected after authorization approved.

For repudiation, log immutable event IDs, request IDs, actor IDs, delegation
chain, approval ID, target ID, and clock source. Healthy signals include high
coverage of actor-bound events and low unknown actor rates. Failing signals
include shared actor IDs, missing request IDs, log gaps, clock drift, or
operator actions with no approval link.

For information disclosure, measure access denials, cross-tenant query
rejections, secret redaction counts, verbose error suppression, and outbound
data volume by tenant and role. Healthy signals show stable access patterns.
Failing signals show unusual export volume, repeated denied reads, or logs that
contain data classifications banned from logs.

For denial of service, measure request rate, queue depth, retry count, timeout
rate, CPU, memory, open sockets, lock wait, external dependency latency, and
cost burn. Healthy signals stay within SLO and quota. Failing signals include
retry storms, queue age growth, pool exhaustion, and defensive rate limits
triggering without recovery.

For elevation of privilege, log policy decision inputs, role source, tenant,
capability, privilege grant, privilege use, and denied high-risk action. A
healthy system has expected admin action volume and traceable privilege grants.
A failing system shows privilege use without grant, policy bypass paths, direct
object reference attempts, or service accounts using capabilities outside their
task.

## 17. Security and privacy implications

Engineering judgement: STRIDE is a security prompt set. Its value depends on
the quality of the model, threat statements, and follow-up controls.

STRIDE closes attack surface by making design assumptions explicit. It pushes
teams to ask who can impersonate, modify, deny, read, exhaust, or escalate. It
also opens a process risk: threat models contain sensitive architecture facts,
asset names, controls, known gaps, and deferred risks. Store them with access
control, review retention, and redact details that would help an attacker more
than a defender.

The method is strong for authentication, integrity, accountability,
confidentiality, availability, and authorization. It is weaker for privacy
harms that do not present as disclosure, such as linkability or user awareness.
It is also weaker for social engineering, supply chain compromise, insider
misuse, and business rule abuse unless the model includes those actors and
flows.

STRIDE should not create a false promise that all security concerns are covered
because six boxes were checked. Microsoft secure design guidance says STRIDE is
a common methodology for enumerating threats, and also states that it is not a
substitute for thinking like an attacker
([Microsoft Security Engineering, "Secure By Design"](https://www.microsoft.com/en-us/securityengineering/sdl/practices/secure-by-design),
verified 2026-08-02). That is the right security posture: use STRIDE as a
memory aid, then test whether the scenario, actor, and control make sense in
the specific system.

Privacy handling also matters in the artifact. Do not copy raw production
personal data into threat statements. Use data classes, synthetic examples, and
asset labels. If a model must name a regulated data set or customer segment,
apply the same access controls used for architecture and incident material.

## Code examples

The examples model a small STRIDE triage rule. They are intentionally tiny: a
threat receives tags from its affected security properties. The examples use
TypeScript, Python, and Go because those languages are common in service,
tooling, and security automation codebases.

```typescript
type Property =
  | "identity"
  | "integrity"
  | "accountability"
  | "confidentiality"
  | "availability"
  | "authorization";

type Stride =
  | "Spoofing"
  | "Tampering"
  | "Repudiation"
  | "Information Disclosure"
  | "Denial of Service"
  | "Elevation of Privilege";

const byProperty: Record<Property, Stride> = {
  identity: "Spoofing",
  integrity: "Tampering",
  accountability: "Repudiation",
  confidentiality: "Information Disclosure",
  availability: "Denial of Service",
  authorization: "Elevation of Privilege",
};

interface ThreatDraft {
  actor: string;
  action: string;
  asset: string;
  properties: Property[];
}

function classify(threat: ThreatDraft): Stride[] {
  return [...new Set(threat.properties.map((name) => byProperty[name]))];
}

const tags = classify({
  actor: "external caller",
  action: "replays a signed webhook",
  asset: "payment state",
  properties: ["identity", "integrity"],
});

if (tags.join(",") !== "Spoofing,Tampering") {
  throw new Error("unexpected STRIDE tags");
}
```

```python
from dataclasses import dataclass


PROPERTY_TO_STRIDE = {
    "identity": "Spoofing",
    "integrity": "Tampering",
    "accountability": "Repudiation",
    "confidentiality": "Information Disclosure",
    "availability": "Denial of Service",
    "authorization": "Elevation of Privilege",
}


@dataclass(frozen=True)
class ThreatDraft:
    actor: str
    action: str
    asset: str
    properties: tuple[str, ...]


def classify(threat: ThreatDraft) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for name in threat.properties:
        tag = PROPERTY_TO_STRIDE[name]
        if tag not in seen:
            seen.add(tag)
            result.append(tag)
    return result


threat = ThreatDraft(
    actor="tenant user",
    action="changes another tenant object id",
    asset="invoice record",
    properties=("integrity", "authorization"),
)

assert classify(threat) == ["Tampering", "Elevation of Privilege"]
```

```go
package main

import (
	"fmt"
	"strings"
)

type ThreatDraft struct {
	Actor      string
	Action     string
	Asset      string
	Properties []string
}

var propertyToStride = map[string]string{
	"identity":        "Spoofing",
	"integrity":       "Tampering",
	"accountability":  "Repudiation",
	"confidentiality": "Information Disclosure",
	"availability":    "Denial of Service",
	"authorization":   "Elevation of Privilege",
}

func classify(threat ThreatDraft) []string {
	seen := map[string]bool{}
	var tags []string
	for _, property := range threat.Properties {
		tag := propertyToStride[property]
		if !seen[tag] {
			seen[tag] = true
			tags = append(tags, tag)
		}
	}
	return tags
}

func main() {
	threat := ThreatDraft{
		Actor:      "anonymous client",
		Action:     "sends large upload batches",
		Asset:      "upload worker pool",
		Properties: []string{"availability"},
	}
	got := strings.Join(classify(threat), ",")
	if got != "Denial of Service" {
		panic(fmt.Sprintf("unexpected STRIDE tags: %s", got))
	}
}
```

## 18. References

- Loren Kohnfelder and Praerit Garg, "The threats to our products," Microsoft,
  1999. Cited through Microsoft Learn's DevOps threat modeling paper at
  https://learn.microsoft.com/en-us/security/engineering/threat-modeling-with-dev-ops,
  verified 2026-08-02.
- Adam Shostack, *Threat Modeling. Designing for Security*, Wiley, 1st edition,
  2014, chapters 1 through 4.
- Microsoft Learn, "Microsoft Threat Modeling Tool threats,"
  https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats,
  verified 2026-08-02.
- Microsoft Learn, "Getting started with the Threat Modeling Tool,"
  https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-getting-started,
  verified 2026-08-02.
- Microsoft Security Engineering, "Threat Modeling,"
  https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling,
  verified 2026-08-02.
- Microsoft Security Engineering, "About the Microsoft Security Development
  Lifecycle,"
  https://www.microsoft.com/en-us/securityengineering/sdl/about,
  verified 2026-08-02.
- Microsoft Security Engineering, "Secure By Design,"
  https://www.microsoft.com/en-us/securityengineering/sdl/practices/secure-by-design,
  verified 2026-08-02.
- Microsoft Learn, "Design secure applications on Microsoft Azure,"
  https://learn.microsoft.com/en-us/azure/security/develop/secure-design,
  verified 2026-08-02.
- OWASP Cheat Sheet Series, "Threat Modeling Cheat Sheet,"
  https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html,
  verified 2026-08-02.
- OWASP Foundation, "OWASP Threat Dragon,"
  https://owasp.org/www-project-threat-dragon/, verified 2026-08-02.
- OWASP, "pytm," https://github.com/OWASP/pytm, verified 2026-08-02.
- AWS Security Blog, Danny Cortegaca, Ana Malhotra, and Kareem Abdol-Hamid,
  "Threat modeling your generative AI workload to evaluate security risk,"
  https://aws.amazon.com/blogs/security/threat-modeling-your-generative-ai-workload-to-evaluate-security-risk/,
  verified 2026-08-02.
- AWS, "AWS Security Agent announces support for Threat Modeling,"
  https://aws.amazon.com/about-aws/whats-new/2026/06/aws-security-agent-threat-modeling/,
  verified 2026-08-02.
- AWS Security Agent API Reference, "CreateThreat,"
  https://docs.aws.amazon.com/securityagent/latest/APIReference/API_CreateThreat.html,
  verified 2026-08-02.
- LINDDUN, "Threat Types," https://linddun.org/threat-types/, verified
  2026-08-02.
- Threat Modeling Manifesto, https://www.threatmodelingmanifesto.org/,
  verified 2026-08-02.
