---
name: Threat Modeling
slug: threat-modeling
family: 15-security
category: Security
aliases: [Threat Modelling, STRIDE Modeling, Attack Tree Analysis, Risk-Centric Threat Modeling]
first_described: "Kohnfelder and Garg 1999; Shostack 2014"
maturity: established
related: [secure-by-default, defense-in-depth, least-privilege, complete-mediation, audit-log, zero-trust, abuse-case]
incompatible_with: [checkbox-compliance, security-theater, unowned-risk-register]
verified: 2026-08-02
---

# Threat Modeling

## 1. Name, aliases, and lineage

The canonical name is Threat Modeling. British and some Commonwealth teams
write Threat Modelling. Security architecture teams may say STRIDE modeling
when the prompt set is STRIDE, Attack Tree Analysis when the model is an
attacker goal tree, or risk-centric threat modeling when business impact and
attack simulation drive the work. This entry uses Threat Modeling for the
general pattern, because the pattern is larger than any one prompt set,
diagram, tool, or scoring method.

Microsoft gives the lineage most software teams recognize. Its DevOps threat
modeling guidance says Loren Kohnfelder and Praerit Garg wrote "The threats to
our products" at Microsoft in 1999, and that the paper introduced STRIDE as the
Microsoft process synonym
([Microsoft, "Integrating threat modeling with DevOps"](https://learn.microsoft.com/en-us/security/engineering/threat-modeling-with-dev-ops),
verified 2026-08-02). Adam Shostack later made the practice accessible to
development teams in *Threat Modeling. Designing for Security*, Wiley, 1st
edition, 2014, chapters 1 through 4. Shostack's book is cited here by chapter,
not page, because no page image was confirmed during this entry.

The Threat Modeling Manifesto frames the practice around four questions: what
is being worked on, what can go wrong, what response will be taken, and whether
the result is good enough
([Threat Modeling Manifesto](https://www.threatmodelingmanifesto.org/),
verified 2026-08-02). OWASP describes application threat modeling as a
repeatable process that builds a security view of a system, identifies threats
from that view, and records responses
([OWASP Threat Modeling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html),
verified 2026-08-02). NIST SP 800-154, draft, calls threat modeling a form of
risk assessment that models attack and defense aspects of a logical entity,
such as data, an application, a host, a system, or an environment
([NIST SP 800-154 draft](https://csrc.nist.gov/pubs/sp/800/154/ipd),
verified 2026-08-02).

The name is sometimes abused. A vulnerability scan is not a threat model. A
static diagram without threats is not a threat model. A red-team report is not
a threat model, although its findings can refresh one. A risk register alone is
not a threat model, because it omits the system representation that explains
why the risk exists. The pattern is the repeatable loop that ties model,
assumption, threat, response, owner, and verification into design work.

## 2. Problem and context

A software team is making a design choice that changes who can reach which
asset, what data crosses which boundary, what authority a component holds, or
what a failed control would expose. The team can review code after it is
written, but many security flaws are design flaws. Once the wrong trust
boundary, token scope, tenancy model, storage class, or administrative path is
built, later scanning detects symptoms rather than the design cause.

The common codebase story is familiar. A service adds webhooks without asking
who can spoof the sender. A batch worker gains a storage role that can read all
tenants because the first test needed a broad role. A browser feature passes
private data into a process that runs code from many origins. A Kubernetes
admission controller is treated as a guard, but the team has not asked what
happens when the webhook times out, is bypassed by a new API version, or is
modified by a privileged workload. Those are not syntax errors. They are
security questions about the shape of the system.

Threat Modeling fits when the system has assets worth protecting, adversaries
or failure modes worth naming, and decisions still open enough that the model
can change the design. It belongs in product design, architecture review, API
design, data modeling, infrastructure design, incident follow-up, and feature
rollout planning. Microsoft lists five major threat modeling steps: define
security requirements, create an application diagram, identify threats,
mitigate threats, and validate those mitigations
([Microsoft SDL Threat Modeling](https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling),
verified 2026-08-02). OWASP's project page says a threat model commonly
contains a system description, assumptions, threats, actions for each threat,
and a way to validate the model and actions
([OWASP Threat Modeling Project](https://owasp.org/www-project-threat-modeling/),
verified 2026-08-02).

The context matters. Threat Modeling is productive when the team can name the
scope and make design trade-offs. It is weak when the architecture is hidden,
the asset owner is absent, the exercise has no route into backlog work, or the
team treats the output as a one-time compliance artifact. It is also weak when
the model tries to cover an entire enterprise in one session. The pattern works
best at a unit where people can draw the system, argue about a boundary, assign
owners, and verify a change.

## 3. Forces

Engineering judgement: this dimension weighs practice trade-offs. Citations
name public guidance and examples; the force balancing is design reasoning.

- **Security versus delivery speed.** Threat Modeling slows a design discussion
  long enough to find bad assumptions before they harden into code. The cost is
  meeting time, preparation, and backlog work.
- **Completeness versus bounded scope.** A broad model finds cross-system
  failures, but it can drown a team. A narrow model moves faster, but it may
  miss how an upstream identity, downstream data store, or operator path changes
  the risk.
- **Consistency versus local knowledge.** A shared method such as STRIDE gives
  comparable prompts across teams. Local domain experts still know the odd
  business rule, tenant split, or operational shortcut that the prompt set will
  not infer.
- **Cognitive load versus shared understanding.** The model asks engineers,
  product owners, security staff, SREs, and privacy reviewers to share a
  vocabulary. That load buys a common picture of assets, trust boundaries, and
  failure cases.
- **Latency and runtime cost.** The modeling activity has no runtime latency.
  The chosen responses may add latency through checks, token exchange,
  isolation, logging, encryption, or validation.
- **Coupling.** Threat Modeling exposes coupling between controls and design
  assumptions. For example, a control may only work if a queue preserves
  tenant labels, or if a browser process never receives cross-origin secrets.
- **Operability.** A good model improves operations by naming what to log,
  alert, test, and rehearse. A poor model creates a paper list with no runtime
  signals.
- **Cost.** The pattern costs facilitation, review time, tool upkeep, and
  occasional redesign. It can reduce rework by finding high-cost design flaws
  before production code depends on them.
- **Team topology.** Platform security can own the method, but product teams
  must own system facts and fixes. A central team that writes models for every
  team becomes a queue. A product team with no security review may normalize
  weak assumptions.
- **Privacy versus security framing.** STRIDE is strong for many security
  prompts, while privacy questions often need a privacy method. LINDDUN lists
  seven privacy threat types: linking, identifying, non-repudiation, detecting,
  data disclosure, unawareness, and non-compliance
  ([LINDDUN threat types](https://linddun.org/threat-types/), verified
  2026-08-02).

The pattern favours explicit design reasoning over implicit trust. It
sacrifices speed and some certainty, because the team must discuss what it
does not yet know.

## 4. Applicability and non-applicability

Reach for Threat Modeling when the following hold.

- A design introduces a new trust boundary, identity, data store, external
  party, deployment path, administrative action, or cross-tenant flow.
- A control is assumed to protect a high-value asset, and the team needs to ask
  how the control can fail or be bypassed.
- A new product feature handles credentials, payment data, personal data,
  regulated records, customer content, safety decisions, or privileged
  automation.
- A platform team publishes an extension point, plugin surface, webhook,
  sandbox, admission controller, policy engine, browser API, or agent tool.
- A prior incident revealed that the system behaved as designed, but the design
  had the wrong security assumption.
- A team needs security test cases derived from architecture rather than from
  generic scanner rules.
- A security champion can facilitate, and the owning team can accept follow-up
  work.
- The design is changing enough that the model will not be stale on arrival.

Do NOT reach for Threat Modeling in these cases.

- **No decision remains open.** If the release is frozen and the only option is
  a hotfix, perform incident response or targeted review. Save broader modeling
  for the next design window.
- **The scope cannot be named.** "Model the company" produces vague threats and
  weak ownership. Start with one service, flow, feature, or data set.
- **The asset owner is absent.** Engineers can draw flows, but the product or
  data owner must state impact and acceptable risk. Without that person, the
  model becomes guesswork.
- **The team wants a compliance checkbox.** A template filled after release
  with no design change, owner, or verification is documentation theater.
- **The system has no architecture representation.** If nobody can draw the
  system, first create a system map. That map may be a precursor, but the
  threat model cannot start from blank memory.
- **The need is a known vulnerability search.** Use SAST, DAST, dependency
  scanning, fuzzing, configuration review, or penetration testing when the
  question is "is this implementation vulnerable to a known class?"
- **The method is heavier than the risk.** A low-risk static page with no
  secrets, accounts, payments, personal data, or privileged backend may need a
  checklist, not a workshop.
- **The output has no route into work tracking.** Microsoft notes that the SDL
  Threat Modeling Tool can plug into issue tracking, making the process part of
  standard development
  ([Microsoft SDL Threat Modeling](https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling),
  verified 2026-08-02). If findings cannot become owned work, pause and fix the
  intake path.
- **A quick triage is the real need.** Mozilla's Rapid Risk Assessment is a 30
  to 60 minute service-level assessment that is not a full threat model, though
  it may lead to one
  ([Mozilla Rapid Risk Assessment](https://infosec.mozilla.org/guidelines/risk/rapid_risk_assessment.html),
  verified 2026-08-02). Use a triage model when the team first needs impact
  classification.

## 5. Structure

Threat Modeling has seven participants.

- **System under analysis.** The bounded service, feature, workflow, data set,
  infrastructure slice, or component being modeled.
- **Asset and impact owner.** The person or group that can state what must be
  protected and what loss means.
- **System model.** The representation of processes, data stores, data flows,
  identities, trust boundaries, dependencies, assumptions, and deployment
  facts. It can be a DFD, sequence diagram, architecture sketch, attack surface
  inventory, or code-level map.
- **Threat prompts.** The method used to ask what can go wrong. STRIDE, attack
  trees, abuse cases, kill chains, CAPEC prompts, PASTA, and LINDDUN are common
  examples. OWASP states that no single industry process is universal, while
  system modeling, threat identification, and risk response appear in many
  approaches
  ([OWASP Threat Modeling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html),
  verified 2026-08-02).
- **Threat register.** The list of concrete threat scenarios, each tied to a
  model element, assumption, control, owner, state, and verification approach.
- **Response backlog.** The accepted work: design change, control, test,
  observability, documentation, risk acceptance, or decision to remove a risky
  feature.
- **Validation loop.** The checks that prove the response landed. Examples
  include tests, policy checks, tabletop exercises, telemetry review, design
  sign-off, or a follow-up model refresh.

The relationships matter more than the artifact format. A threat without a
model element is a generic warning. A mitigation without an owner is a wish. An
owner without verification creates hidden risk. A model with no refresh trigger
ages as soon as the architecture changes.

## 6. ASCII structure diagram

```text
 +---------------------+       +----------------------+
 | Asset and impact    |       | System under analysis|
 | owner               |       | service, flow, data  |
 +----------+----------+       +----------+-----------+
            |                             |
            | impact, risk tolerance      | facts
            v                             v
 +----------------------------------------------------+
 | System model                                       |
 | processes, stores, flows, identities, boundaries   |
 +----------+--------------------+--------------------+
            |                    |
            | prompts apply      | assumptions attach
            v                    v
 +---------------------+       +----------------------+
 | Threat prompts      |       | Assumption list      |
 | STRIDE, trees, etc. |       | what must stay true  |
 +----------+----------+       +----------+-----------+
            |                             |
            v                             v
 +----------------------------------------------------+
 | Threat register                                    |
 | scenario, model node, impact, owner, state, test   |
 +----------+--------------------+--------------------+
            |                    |
            | accepted work      | residual risk
            v                    v
 +---------------------+       +----------------------+
 | Response backlog    |       | Risk decisions       |
 | controls and tests  |       | accept, defer, drop  |
 +----------+----------+       +----------+-----------+
            |                             |
            +-------------+---------------+
                          v
                 +------------------+
                 | Validation loop  |
                 | prove and refresh|
                 +------------------+
```

## 7. Dynamics

The pattern runs as a loop, not as a single meeting. The model is a working
object. A design change can enter at any point and force a revisit of scope,
assumptions, threats, or controls.

```text
Engineer       Facilitator     Product/SRE/Sec       Work tracker      CI/Runtime
   |                |                 |                    |                |
   | propose change |                 |                    |                |
   |--------------->|                 |                    |                |
   |                | set scope       |                    |                |
   |                |---------------->|                    |                |
   |                | draw model with facts and boundaries |                |
   |                |<-------------->|                    |                |
   |                | apply prompts: what can go wrong?    |                |
   |                |<-------------->|                    |                |
   |                | record threats, assumptions, owners  |                |
   |                |------------------------------------->|                |
   |                | choose response: fix, test, accept   |                |
   |                |<-------------->|                    |                |
   | implement work |                 |                    |                |
   |----------------------------------------------------->|                |
   |                |                 |                    | run checks     |
   |                |                 |                    |--------------->|
   |                |                 |                    | telemetry      |
   |                |                 |                    |<---------------|
   |                | refresh model when design or facts change            |
   |                |<---------------------------------------------------->|
```

Timing guidance is engineering judgement. A large new architecture usually
needs a workshop before build starts, a review before release, and refreshes
when data flow or authority changes. A small feature may need a 20 minute
modeling pass in a design review. An incident needs a post-incident refresh
that asks which assumption failed and which model element was absent.

The strongest dynamic is disagreement. When an engineer says "the queue is
internal," the facilitator asks what internal means, who can publish, whether a
partner can influence it, and which identity is logged. When a product owner
says a record is low risk, the privacy reviewer asks whether linking or
inference changes that answer. The result is not perfect prediction. The result
is that assumptions become visible before attackers or outages test them.

## 8. Implementation variants

**STRIDE over data flow diagrams.** This is the common software security form.
The team draws processes, data stores, data flows, external entities, and trust
boundaries, then asks STRIDE prompts across them. Microsoft says its Threat
Modeling Tool uses a notation for components, data flows, and security
boundaries, and helps identify threat classes from design structure
([Microsoft SDL Threat Modeling](https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling),
verified 2026-08-02). Trade-off: good structure and teachability, but weaker
privacy coverage unless paired with privacy prompts.

**Four-question lightweight model.** The team answers the Manifesto questions
in a short design review. Trade-off: low overhead and easy adoption, but depth
depends heavily on the participants.

**Attack trees.** Start with an attacker goal, then decompose ways to reach it.
The Kubernetes admission control threat model includes an attack tree appendix
for webhook attacks
([Kubernetes SIG Security admission control threat model](https://github.com/kubernetes/sig-security/blob/main/sig-security-docs/papers/admission-control/kubernetes-admission-control-threat-model.md),
verified 2026-08-02). Trade-off: excellent for one high-value goal, weaker for
whole-system coverage.

**Abuse cases and misuse cases.** Write malicious or harmful user stories and
derive requirements. Trade-off: accessible to product teams, but it can miss
infrastructure and supply-chain threats.

**Risk-centric modeling.** Start from business impact, attack simulation, and
risk ranking. Tony Uceda-Velez and Marco M. Morana describe PASTA in *Risk
Centric Threat Modeling. Process for Attack Simulation and Threat Analysis*,
Wiley, 1st edition, 2015, chapters 1 through 4. Trade-off: ties security to
business impact, but asks more of the facilitator and team.

**Privacy threat modeling.** Use LINDDUN or a similar privacy method when the
harm is linking, inference, disclosure, retention, lack of awareness, or lack
of control. NIST's privacy framework resource identifies LINDDUN as privacy
threat modeling guidance and notes that it supports eliciting and mitigating
privacy threats in software architectures
([NIST Privacy Framework, LINDDUN resource](https://www.nist.gov/privacy-framework/linddun-privacy-threat-modeling-framework),
verified 2026-08-02). Trade-off: much better privacy reasoning, but it does not
replace security prompts.

**Continuous model in code.** Keep threats, assets, and flows as structured
data in the repository, then generate reports or checks. Trade-off: supports
review and diffing, but risks over-fitting the model to what is easy to encode.

**Rapid risk triage before full modeling.** Mozilla's RRA focuses on service
impact and data, and says details are for full threat models
([Mozilla Rapid Risk Assessment](https://infosec.mozilla.org/guidelines/risk/rapid_risk_assessment.html),
verified 2026-08-02). Trade-off: fast portfolio triage, but not a replacement
for a design-level model.

Three runnable sketches follow. They model the register, not the whole human
process.

```typescript
type Status = "open" | "accepted" | "verified";

type Threat = {
  id: string;
  element: string;
  scenario: string;
  stride: "S" | "T" | "R" | "I" | "D" | "E";
  owner: string;
  status: Status;
};

const threats: Threat[] = [
  {
    id: "TM-1",
    element: "webhook receiver",
    scenario: "sender identity can be spoofed when signatures are absent",
    stride: "S",
    owner: "payments-platform",
    status: "open",
  },
  {
    id: "TM-2",
    element: "audit store",
    scenario: "operator can erase records for denied admin actions",
    stride: "R",
    owner: "security-platform",
    status: "verified",
  },
];

const openByOwner = threats.reduce<Record<string, number>>((acc, threat) => {
  if (threat.status === "open") {
    acc[threat.owner] = (acc[threat.owner] ?? 0) + 1;
  }
  return acc;
}, {});

console.log(openByOwner["payments-platform"]);
```

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Threat:
    threat_id: str
    element: str
    scenario: str
    owner: str
    verified: bool


def unverified(threats: list[Threat]) -> list[str]:
    return [item.threat_id for item in threats if not item.verified]


items = [
    Threat("TM-1", "token issuer", "audience is too broad", "identity", False),
    Threat("TM-2", "event log", "write path lacks append-only control", "secops", True),
]

print(",".join(unverified(items)))
```

```go
package main

import "fmt"

type Threat struct {
	ID       string
	Element  string
	Scenario string
	Owner    string
	Status   string
}

func openThreats(items []Threat) []Threat {
	out := []Threat{}
	for _, item := range items {
		if item.Status == "open" {
			out = append(out, item)
		}
	}
	return out
}

func main() {
	items := []Threat{
		{"TM-1", "tenant router", "label spoofing can steal traffic", "platform", "open"},
		{"TM-2", "admin API", "break-glass action lacks review", "security", "verified"},
	}
	fmt.Println(openThreats(items)[0].ID)
}
```

## 9. Known production uses

**Microsoft Security Development Lifecycle.** Microsoft calls threat modeling a
core element of the SDL and lists it as a routine development lifecycle
activity that should be refined over time
([Microsoft SDL Threat Modeling](https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling),
verified 2026-08-02). Microsoft also states that different product groups use
different variants based on security requirements, and gives Windows and Azure
Cognitive Services as examples of systems with different sizes and
characteristics
([Microsoft, "Integrating threat modeling with DevOps"](https://learn.microsoft.com/en-us/security/engineering/threat-modeling-with-dev-ops),
verified 2026-08-02).

**Kubernetes admission control.** Kubernetes SIG Security published a threat
model for admission controllers. The Kubernetes blog says the security
documentation subgroup spent time developing the model to help users and
designers manage risks around admission controllers
([Kubernetes blog, "Securing Admission Controllers"](https://kubernetes.io/blog/2022/01/19/secure-your-admission-controllers-and-webhooks/),
verified 2026-08-02). The model names webhook flooding, bypass through new API
features, privileged containers on webhook nodes, and RBAC controls
([Kubernetes SIG Security admission control threat model](https://github.com/kubernetes/sig-security/blob/main/sig-security-docs/papers/admission-control/kubernetes-admission-control-threat-model.md),
verified 2026-08-02).

**Chromium and Chrome Site Isolation.** Chromium's post-Spectre security
document says the project had to rethink the threat model and defenses for
Chrome renderer processes after Spectre and Meltdown. It records the new
assumption that active web content can read data in the renderer process and
points to Site Isolation as the direct defensive approach
([Chromium, "Post-Spectre Threat Model Re-Think"](https://chromium.googlesource.com/chromium/src/%2B/master/docs/security/side-channel-threat-model.md),
verified 2026-08-02).

**Mozilla service risk process.** Mozilla documents Rapid Risk Assessment as a
lightweight threat model that can grow into a full threat model for higher-risk
services. The public example discusses Firefox Accounts data and asks what
happens if it is disclosed, unavailable, or modified without authority
([Mozilla Rapid Risk Assessment](https://infosec.mozilla.org/guidelines/risk/rapid_risk_assessment.html),
verified 2026-08-02).

**OpenStack Security Guide.** OpenStack's Security Guide models security
domains, trust requirements, threat actors, and attack vectors for cloud
deployments. Its security boundaries chapter says cloud services often bridge
domains and require special attention when controls are applied
([OpenStack Security Guide, "Security boundaries and threats"](https://docs.openstack.org/security-guide/introduction/security-boundaries-and-threats.html),
verified 2026-08-02).

## 10. Consequences

Engineering judgement: consequences vary by team maturity, system risk, and
whether findings reach implementation.

Positive.

- Security questions move earlier, when changing a data flow, boundary, or
  authority model is still practical.
- The team gets a shared map of assets, flows, assumptions, and controls.
- Threats become concrete scenarios tied to model elements, not generic fear.
- Security tests gain design intent. A test can say which threat it validates.
- Residual risk becomes explicit. A team can accept a risk with an owner and
  revisit date instead of forgetting it.
- Operations improve when the model names denial reasons, control health, and
  attack paths that need telemetry.
- Privacy concerns can be handled beside security concerns when a privacy
  prompt set is included.
- Product trade-offs become visible. A risky feature can be narrowed, delayed,
  isolated, or removed with a clear reason.

Negative.

- A poorly scoped session wastes scarce engineering attention.
- The model ages quickly unless architecture and data-flow changes refresh it.
- False certainty is dangerous. A model can miss threats, especially when
  adversary knowledge or system facts are incomplete.
- Heavy tooling can make teams serve the artifact rather than the decision.
- Threat registers create work. If owners lack time, the pattern exposes
  security debt without paying it down.
- Scoring systems can start arguments that add little value when the team
  already knows a control is needed.
- Cross-team systems can produce ownership gaps when one team owns a flow,
  another owns identity, and a third owns logs.
- Sensitive model details can aid an attacker if stored without access control.

## 11. Failure modes and misuse

Engineering judgement: these are production failure patterns drawn from common
security practice. They are written as observable triples so reviewers can act.

**Checkbox model.** Symptom. The repository contains a filled template, but no
design change, test, backlog item, risk owner, or refresh date. Cause. The
organization rewarded artifact presence rather than risk reduction. Fix. Add a
merge or release rule that every accepted threat has a state: fixed, verified,
accepted by a named owner, or removed with the feature.

**Scope fog.** Symptom. A session produces threats such as "attacker steals
data" with no component, flow, or trust boundary attached. Cause. The model
started before the system under analysis was bounded. Fix. Stop, draw the
smallest service or flow that contains the decision, and park wider concerns in
a follow-up list.

**Hero modeler bottleneck.** Symptom. No team threat models unless one security
expert attends, and reviews wait weeks. Cause. The method lives in one person
rather than in team practice. Fix. Train security champions, use short prompts,
and reserve experts for high-risk or contested designs.

**STRIDE karaoke.** Symptom. The team chants each STRIDE word for every box and
records low-value duplicates. Cause. Prompt mechanics replaced reasoning. Fix.
Ask for concrete attacker action, violated property, affected asset, current
control, and missing evidence.

**Mitigation without verification.** Symptom. A threat is marked closed because
"add auth" was implemented, yet no test proves the denied case and no telemetry
shows denial reason. Cause. The register tracks code changes, not validation.
Fix. Add a verification field and reject closure until a test, policy check, or
runtime signal exists.

**Model drift.** Symptom. The model says the service stores no personal data,
but later incidents show logs, analytics, or support exports contain it. Cause.
New flows were added without refresh triggers. Fix. Refresh when a data type,
identity, authority, dependency, endpoint, model capability, or external party
changes.

**Risk acceptance laundering.** Symptom. Many high-impact threats are
"accepted" by a project lead with no date, condition, or compensating control.
Cause. Acceptance became a way to bypass security work. Fix. Require the asset
owner, expiry date, rationale, and monitoring plan for acceptance.

**Tool-first modeling.** Symptom. Engineers spend the session adjusting stencil
syntax while the security questions stay shallow. Cause. The tool is optimized
for archiving, not discovery. Fix. Whiteboard first, then transfer only the
model that changed decisions.

**Secret map exposure.** Symptom. A broad group can read a model containing
admin endpoints, trust assumptions, and weak controls. Cause. Threat models
were treated as harmless diagrams. Fix. Classify model artifacts, limit access,
and publish a sanitized summary when wide sharing is needed.

## 12. Trade-off matrix

| Force | Threat Modeling | Secure Code Review | Penetration Testing | Vulnerability Scanning | Formal Verification | Red Team Exercise |
|---|---|---|---|---|---|---|
| Primary question | What can go wrong in this design? | Did code implement the design safely? | Can testers exploit the deployed system? | Do known findings match this build? | Does a property hold under a model? | Can an adversary reach an objective? |
| Timing | Design and change planning | During review and before merge | Late pre-release or production-like | Continuous or scheduled | Before or during high-assurance build | Production or staged campaign |
| Coupling to architecture | High | Medium | Medium | Low | Very high | Medium |
| Finds design flaws early | Strong | Medium | Medium | Weak | Strong but narrow | Medium |
| Finds implementation bugs | Medium | Strong | Strong | Strong for known classes | Strong only for modeled properties | Strong when objective reaches them |
| Cost | Meeting time plus fixes | Reviewer time | Specialist time and environment | Tool cost and triage | High modeling and proof cost | High team cost |
| Cognitive load | Medium to high | Medium | Low for product team, high for testers | Low to medium | Very high | Medium |
| Operability output | Logs, alerts, test cases, playbooks | Code changes and review notes | Findings and evidence | Tickets and reports | Proof artifacts | Detection and response lessons |
| Team topology | Product team plus security champion | Engineering reviewers | Security testers plus owners | Platform security plus owners | Specialists plus domain experts | Security operations plus business owners |
| False confidence risk | High if stale | High if reviewers miss design | High if scope is narrow | High if tools miss context | High if model omits reality | High if results are overgeneralized |
| Best alternative when | You need design reasoning | Code already exists | You need exploit evidence | You need broad known-issue coverage | A small property must be proven | You need response realism |

Reading of the table. Threat Modeling is not a replacement for review,
scanning, testing, formal methods, or red teams. It tells those practices where
to look and what properties matter. The alternatives return evidence that can
refresh the model.

## 13. Related and incompatible patterns

- **Secure by Default.** Threat Modeling identifies unsafe defaults before they
  ship. Secure by Default turns that finding into shipped behavior.
- **Defense in Depth.** Threat Modeling asks what happens when one control
  fails. Defense in Depth supplies layered responses when a single control is
  too brittle.
- **Least Privilege.** Many threat responses reduce authority. Least Privilege
  gives the implementation rule for those responses.
- **Complete Mediation.** Threat Modeling finds unmediated paths and cached
  decisions that can bypass authorization. Complete Mediation gives the access
  control discipline.
- **Audit Log.** Threat Modeling names what must be reconstructable after an
  event. Audit Log records it without turning logs into a privacy hazard.
- **Zero Trust.** Threat Modeling can show why network location is a weak trust
  fact. Zero Trust supplies an architecture loop for access decisions.
- **Abuse Case.** Abuse cases are a variant or input. They help product teams
  express malicious stories without needing a diagram-heavy process.
- **Attack Surface Analysis.** Attack surface inventory is often an input to
  the system model. It is not enough by itself, because it does not decide
  response or residual risk.
- **Penetration Testing.** Testing can validate or disprove a model. It does
  not replace the model because it happens after many design choices have been
  made.
- **Checkbox Compliance.** Actively conflicts. Compliance can require evidence,
  but the pattern fails when evidence replaces design improvement.
- **Security Theater.** Actively conflicts. Threat Modeling is valuable only
  when it changes design, tests, controls, telemetry, or risk ownership.

## 14. Refactoring path in and out

Introducing Threat Modeling into a codebase or organization.

1. Pick one high-value flow that is about to change. Good candidates are login,
   payment, webhook ingestion, tenant routing, admin actions, data export,
   model tool execution, or privileged automation.
2. Draw the current system using the simplest notation the team understands.
   Include processes, data stores, flows, identities, trust boundaries,
   dependencies, assumptions, and operators.
3. Name assets and impact owners. Avoid ranking until the owner can say what
   loss, corruption, outage, or misuse means.
4. Apply one prompt set. STRIDE is a good default for software security. Add
   LINDDUN when personal data or inference harm matters.
5. Record only concrete threat scenarios. Each one needs a model element,
   attacker or failure path, affected property, owner, proposed response, and
   verification method.
6. Convert accepted responses into normal work items. Link tests and telemetry
   back to threat IDs where practical.
7. Add refresh triggers to the design checklist: new data type, new authority,
   new identity, new external party, new dependency, new agent action, new
   boundary, or changed deployment model.
8. Repeat on another high-value flow. Do not build an enterprise process until
   two or three teams have proved the smaller loop.

Refactoring out when the pattern is too heavy.

1. Audit recent models. If most threats are low-value duplicates, narrow the
   scope or reduce the prompt set.
2. If sessions are blocked by facilitation scarcity, replace full workshops
   with a four-question design review for low and medium risk changes.
3. If a tool slows discovery, keep it for archive and use a whiteboard or plain
   markdown during the session.
4. If every feature receives the same depth, add triage. Mozilla's RRA is one
   example of a lightweight service assessment that can lead to deeper modeling
   when warranted
   ([Mozilla Rapid Risk Assessment](https://infosec.mozilla.org/guidelines/risk/rapid_risk_assessment.html),
   verified 2026-08-02).
5. If no threats change design, shift effort to code review, scanning,
   penetration testing, or control validation until the next architecture
   change.
6. If the system is being retired, capture only residual risks for the shutdown
   path: data export, access removal, log retention, key destruction, and
   dependency cleanup.

Cross reference the refactoring family for Extract Function, Extract Class, and
Replace Magic Literal where model-backed fixes turn broad checks into named
policy code. Cross reference Inline Class when a threat register wrapper adds
no value and the work tracker can carry the same fields.

## 15. Testing and verification

Engineering judgement: Threat Modeling is verified by the controls, tests, and
signals it creates. The model itself is reviewed, not unit tested.

What becomes easier.

- Security tests can be derived from named threats. A test can assert that a
  webhook without a valid signature is rejected because threat TM-1 describes
  sender spoofing.
- Authorization tests can cover the trust boundary, not only happy-path roles.
- Fuzzing targets can be chosen from high-risk parsers, deserializers, and
  boundary-crossing inputs named in the model.
- Tabletop exercises can rehearse the threats the team accepted instead of
  generic incidents.
- Observability tests can assert that denials, control failures, and privileged
  actions emit fields needed for response.

What becomes harder.

- The test suite must stay aligned with model IDs and architecture changes.
- Some threats are about process or operations, such as missing review for
  break-glass access. Those need workflow tests, audit checks, or tabletop
  verification rather than unit tests.
- Risk acceptance can be verified for ownership and expiry, but not for truth.
  The team must revisit it when facts change.

Techniques that apply.

- **Threat-to-test traceability.** Every high or accepted threat has at least
  one linked test, policy check, monitor, tabletop exercise, or explicit risk
  acceptance.
- **Abuse-case tests.** Encode malicious stories as integration tests. Examples
  include replayed webhook events, cross-tenant object IDs, forged labels,
  expired tokens, missing audit fields, or disallowed model tool calls.
- **Contract tests for controls.** A shared authorization library, webhook
  verifier, or tenant router gets a contract suite that every service must run.
- **Mutation and negative testing.** Remove the expected control in a test
  fixture and confirm the test fails. This guards against tests that do not
  exercise the control.
- **Policy-as-code checks.** For infrastructure, encode findings as admission
  policies, Terraform checks, IAM tests, or CI rules.
- **Model review checklist.** Review scope, asset list, trust boundaries,
  assumptions, threat coverage, response ownership, residual risk, and refresh
  triggers.

The TypeScript, Python, and Go samples in dimension 8 were compiled or run
locally for this entry with `npx tsc`, `python3`, and `go run`.

## 16. Observability signals

Engineering judgement: observability should tell the team whether modeled
controls exist, fire, and fail in ways the model predicted.

Record these signals.

- A count of open, accepted, fixed, and verified threats by service, owner, and
  age.
- A count of model refreshes by trigger type: data-flow change, dependency
  change, identity change, authority change, model capability change, external
  party change, incident, or release review.
- A count of rejected requests by modeled control and denial reason, such as
  signature failure, audience mismatch, tenant mismatch, policy deny, schema
  deny, or rate limit.
- A count of privileged actions, break-glass actions, and administrative
  mutations tied to threat IDs where the model predicted abuse.
- Coverage for high-risk threats: linked test present, monitor present,
  owner present, and expiry present for accepted risk.
- Drift alerts when architecture inventory disagrees with the model, such as a
  new public endpoint, queue, external integration, data class, or IAM grant.
- Time from threat creation to verified response.
- Model access logs for sensitive models.

A healthy dashboard shows few stale high-risk threats, a stable rate of model
refreshes aligned to architecture change, and denial reasons that match known
controls. It also shows some denied abuse-case traffic in test or staging,
because the team is exercising the controls.

A failing dashboard shows old open threats, accepted risks without expiry,
controls with no denial telemetry, model refreshes that stop while deployments
continue, or a large number of production denials with no related threat ID.
That last signal often means reality found a path the model missed.

## 17. Security and privacy implications

Engineering judgement: Threat Modeling is a security pattern, but the artifact
it creates can itself become sensitive.

Security benefits.

- The pattern closes blind spots by making trust boundaries, assets, and
  assumptions explicit.
- It finds design-level attack paths that scanners often miss, such as confused
  deputy paths, cross-tenant routing, fallback behavior, control bypass on
  timeout, and unsafe operator workflows.
- It creates a path from architecture to tests, policy, telemetry, and incident
  exercises.
- It can reveal where defense in depth is needed because one control is too
  brittle.

Security risks.

- A detailed model can expose weak controls, admin endpoints, secret locations,
  bypass assumptions, and incident response gaps. Store it with access control.
- A stale model can mislead reviewers into trusting controls that no longer
  exist.
- A model that omits supply-chain actors, build systems, or operators can
  over-focus on application users and miss higher-authority paths.
- A model tied to one method can miss threat classes outside that method.
  STRIDE alone is not enough for privacy and may be weak for business logic
  abuse.

Privacy implications.

- Threat Modeling can improve privacy when it names data categories, linking
  paths, inference risks, retention, subject control, and disclosure paths.
- The modeling artifact may contain personal data examples, tenant names,
  incident details, or employee workflow details. Minimize examples and redact
  where a real identifier is not needed.
- Model access logs may reveal sensitive project timing or product plans. Treat
  them as internal security metadata.
- Privacy risks need their own prompt set. LINDDUN exists because privacy harm
  is not the same as ordinary security failure
  ([LINDDUN threat types](https://linddun.org/threat-types/), verified
  2026-08-02).

Where the pattern is silent. Threat Modeling does not implement access control,
encryption, isolation, logging, or privacy rights. It identifies why those
controls may be needed and what property they must satisfy. The controls still
need normal engineering design and verification.

## 18. References

- Loren Kohnfelder and Praerit Garg, "The threats to our products," Microsoft,
  1999. Cited through Microsoft, "Integrating threat modeling with DevOps,"
  https://learn.microsoft.com/en-us/security/engineering/threat-modeling-with-dev-ops,
  verified 2026-08-02.
- Adam Shostack, *Threat Modeling. Designing for Security*, Wiley, 1st edition,
  2014, chapters 1 through 4.
- Tony Uceda-Velez and Marco M. Morana, *Risk Centric Threat Modeling. Process
  for Attack Simulation and Threat Analysis*, Wiley, 1st edition, 2015,
  chapters 1 through 4.
- Matt Coles and Izar Tarandach, *Threat Modeling. A Practical Guide for
  Development Teams*, independently published, 2023, chapters 1 through 5.
- Microsoft Security Engineering, "Threat Modeling,"
  https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling,
  verified 2026-08-02.
- Microsoft Security, "Integrating threat modeling with DevOps,"
  https://learn.microsoft.com/en-us/security/engineering/threat-modeling-with-dev-ops,
  verified 2026-08-02.
- NIST, Murugiah Souppaya and Karen Scarfone, *SP 800-154, Guide to
  Data-Centric System Threat Modeling*, Initial Public Draft, March 2016,
  https://csrc.nist.gov/pubs/sp/800/154/ipd, verified 2026-08-02.
- OWASP Cheat Sheet Series, "Threat Modeling Cheat Sheet,"
  https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html,
  verified 2026-08-02.
- OWASP Foundation, "OWASP Threat Modeling Project,"
  https://owasp.org/www-project-threat-modeling/, verified 2026-08-02.
- Threat Modeling Manifesto working group, "Threat Modeling Manifesto,"
  https://www.threatmodelingmanifesto.org/, verified 2026-08-02.
- Kubernetes SIG Security, "Kubernetes Admission Control Threat Model,"
  https://github.com/kubernetes/sig-security/blob/main/sig-security-docs/papers/admission-control/kubernetes-admission-control-threat-model.md,
  verified 2026-08-02.
- Kubernetes Blog, Rory McCune, "Securing Admission Controllers,"
  https://kubernetes.io/blog/2022/01/19/secure-your-admission-controllers-and-webhooks/,
  verified 2026-08-02.
- Chromium project, "Post-Spectre Threat Model Re-Think,"
  https://chromium.googlesource.com/chromium/src/%2B/master/docs/security/side-channel-threat-model.md,
  verified 2026-08-02.
- Mozilla Infosec, "Rapid Risk Assessment,"
  https://infosec.mozilla.org/guidelines/risk/rapid_risk_assessment.html,
  verified 2026-08-02.
- OpenStack Security Guide, "Security boundaries and threats,"
  https://docs.openstack.org/security-guide/introduction/security-boundaries-and-threats.html,
  verified 2026-08-02.
- LINDDUN, "Privacy threat types," https://linddun.org/threat-types/,
  verified 2026-08-02.
- NIST Privacy Framework, "LINDDUN privacy threat modeling framework,"
  https://www.nist.gov/privacy-framework/linddun-privacy-threat-modeling-framework,
  verified 2026-08-02.
