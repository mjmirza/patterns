---
name: Secure by Default
slug: secure-by-default
family: 15-security
category: Security
aliases: [Secure Defaults, Fail-Safe Defaults, Deny by Default, Safe Defaults]
first_described: "Saltzer and Schroeder 1975"
maturity: established
related: [least-privilege, complete-mediation, defense-in-depth, secure-configuration, policy-as-code]
incompatible_with: [permit-by-default, ambient-authority, insecure-default-configuration]
verified: 2026-08-02
---

# Secure by Default

## 1. Name, aliases, and lineage

The canonical name is Secure by Default. In security engineering it overlaps
with **Secure Defaults**, **Deny by Default**, and **Fail-Safe Defaults**. The
names differ by community. Product security teams tend to say Secure by Default
when they mean that a product starts in a hardened state. Access-control
literature tends to say Fail-Safe Defaults when it means that access starts
closed and must be opened by a positive grant. Policy authors often say Deny by
Default when the same rule is written as an authorization decision.

The lineage starts with Jerome H. Saltzer and Michael D. Schroeder, "The
Protection of Information in Computer Systems," 1975. Their design principle
of fail-safe defaults says that access decisions should be based on permission
rather than exclusion, and that lack of access is the default state
([Saltzer and Schroeder, University of Virginia mirror](https://www.cs.virginia.edu/~evans/cs551/saltzer/),
verified 2026-08-02). The paper also names least privilege and complete
mediation as related design principles, which this pattern often composes with.

Microsoft's Security Development Lifecycle popularized the product phrase
Secure by Default as part of SD3+C, alongside Secure by Design, Secure in
Deployment, and Communications. Microsoft described Secure by Default as a
release goal in the SDL era, meaning that a product ships with reduced attack
surface and with dangerous features disabled or restricted until an operator
chooses them
([Microsoft SDL Introduction](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/cc307406%28v%3Dmsdn.10%29),
verified 2026-08-02).

OWASP uses the same family of ideas in current product guidance. The OWASP
Secure Product Design Cheat Sheet names Secure by Default as configuration
guidance, with minimal manual setup needed for a secure starting state
([OWASP Secure Product Design Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Product_Design_Cheat_Sheet.html),
verified 2026-08-02).

This entry uses Secure by Default for the pattern because it covers more than
access control. It includes default network exposure, cryptography choices,
session flags, generated project templates, service identity scopes, and
workflow guardrails. Fail-Safe Defaults is the narrower historical principle
inside the broader pattern.

## 2. Problem and context

A system has settings, generated files, API defaults, permission rules, feature
switches, installation steps, or project scaffolds. Most users accept those
defaults. They rarely inspect every generated header, network binding,
permission grant, storage scope, cookie flag, or service token before first
use. In many organizations, a default that ships in a template becomes the
production baseline within days.

The problem appears when the default state is open. A new service binds to every
interface instead of localhost. A generated administrator role has broad
permissions. A session cookie lacks a secure flag until a developer adds it. A
cross-site request forgery check exists but must be manually enabled. An object
store bucket, development database, preview branch, or management endpoint is
created in a permissive mode because the first-run path tried to avoid friction.
Those choices are not edge cases. They are the path most users take.

Secure by Default changes the starting state. The default path should be safe
for ordinary production use. Risky behavior remains possible when the product
has a valid reason to support it, but it requires an explicit opt-out with a
name that makes the risk visible. A user can still publish a public endpoint,
allow anonymous access, run without TLS for a local test, or grant a broad
role, but the system should make that a clear act rather than an accidental
inheritance from a permissive template.

The context matters. The pattern is most useful where many teams repeat the
same setup, where security controls have a known good baseline, and where the
product or platform owner can encode that baseline into code. It is weaker
where no one default fits the deployment context, or where false refusal would
cause greater harm than false acceptance. In those cases the pattern shifts
from automatic hardening to explicit choice, see dimension 4.

There is a social reason this pattern matters. Defaults are copied more often
than policies are read. A wiki page may say to enable TLS, turn on request
forgery checks, narrow service-account permissions, and avoid wildcard origins,
but a generated project file says what the organization will really do. The
default becomes the tutorial, the test fixture, the internal example, and the
starting point for incident response. Secure by Default treats those artifacts
as production controls rather than as developer convenience.

The pattern also handles time. A choice that was safe five years ago may no
longer be safe after threat models, browsers, operating systems, package
ecosystems, and deployment models change. A product that owns its defaults can
move the fleet by changing a baseline, emitting migration warnings, and
blocking high-risk old modes. A product that pushed every decision to each
adopter has to find and persuade every adopter later.

## 3. Forces

Engineering judgement. The ranking below is analytical. The sources in
dimension 18 establish the named principles and production behavior, not the
weight assigned here.

- **Safety versus first-run friction.** Secure defaults favor a safe starting
  state, even when a user must perform one extra explicit step to open access or
  lower a guard for local work.
- **Availability versus confidentiality.** Denying uncertain access protects
  data but may block legitimate work. The pattern chooses confidentiality and
  integrity when intent is unclear.
- **Consistency versus local freedom.** A common baseline reduces variation
  across teams. It also narrows the set of choices available to a local owner
  unless escape hatches are documented and audited.
- **Latency versus mediation.** A secure default often adds checks, token
  validation, certificate setup, encryption, sandbox setup, or policy
  evaluation. Most checks are small, but they are not free.
- **Operability versus hidden magic.** Automatic TLS, default security headers,
  generated private storage, and default denial reduce setup mistakes. They can
  confuse operators when the automation fails unless the product exposes clear
  diagnostics.
- **Cost versus platform investment.** The cheapest feature ships a loose
  default and asks each adopter to harden it. Secure by Default moves that cost
  to the platform once, then amortizes it across every user.
- **Team topology versus ownership.** Platform teams favor this pattern because
  they can encode policy centrally. Application teams may resist when a default
  blocks a special case. The design must preserve explicit, reviewable opt-out.
- **Cognitive load versus surprise.** Safe defaults lower the number of
  decisions for new users. They raise cognitive load when a user expects an
  older permissive behavior and must learn why the system now refuses it.

The pattern favors safety, repeatability, and low operator variance. It
sacrifices some freedom, some first-run simplicity, and some ability to infer
behavior from one local file.

The hard force is trust. Users trust the product author when they accept a
default. That trust is often implicit. They may not know that a cookie can be
host-only or domain-wide, that a token can be long-lived or short-lived, that a
server can bind to a loopback address or a public address, or that a policy can
grant wildcard access to future resource types. Secure by Default asks the
platform owner to spend expertise once, in the place where expertise is most
concentrated, then let ordinary users inherit that work.

The counterforce is product honesty. A safe default must not become a way to
paper over missing documentation or weak error handling. If the product refuses
to start, the message must name the unsafe setting, the safer setting, and the
escape hatch if one exists. If automatic hardening performs background work,
such as certificate provisioning or policy migration, it must report progress
and failure. Silent protection that cannot be inspected will be treated as
flakiness.

## 4. Applicability and non-applicability

Reach for Secure by Default when these conditions hold.

- A product has a common deployment path, and most users will accept the
  generated or shipped baseline.
- The cost of an unsafe default is data exposure, privilege escalation,
  unauthorized mutation, cross-tenant access, downgraded transport security, or
  secret leakage.
- The product owner can define a safe baseline that fits most deployments.
- A risky mode is valid only for development, migration, compatibility, or
  emergency operation.
- A setting is security-sensitive and invisible to end users, such as cookie
  flags, same-origin checks, HTTP security headers, token lifetime, network
  bind address, or storage isolation.
- A platform hosts many teams and wants every new service to inherit the same
  baseline without each team rebuilding the control.
- An authorization rule can be expressed as positive grants. Saltzer and
  Schroeder's fail-safe defaults principle fits this case directly
  ([Saltzer and Schroeder](https://www.cs.virginia.edu/~evans/cs551/saltzer/),
  verified 2026-08-02).

Non-applicability. Do NOT reach for Secure by Default in these cases.

- **No single default is safe across contexts.** A database migration tool that
  may run against a clone, staging, or production cannot infer the safe target
  from a default. Require an explicit environment choice and fail on omission.
- **False refusal is more dangerous than false grant.** Some safety systems
  need fail-operational behavior. Security defaults should not be copied into
  availability domains where denial can cause physical harm or contractual
  outage.
- **The default would hide a required design choice.** Key custody, data
  residency, regulated retention, and tenant isolation model are not good
  places for a quiet default. Make the user choose.
- **The control depends on unknown threat data.** If a system cannot know which
  origins, roles, keys, or networks are trusted, it should start closed and ask
  for a policy, not guess a narrow allowlist.
- **The escape hatch cannot be made observable.** A risky opt-out without logs,
  metrics, or configuration inventory becomes a silent backdoor.
- **The old behavior is part of a published compatibility contract.** Changing
  defaults can break clients. Use versioned defaults, migration warnings, or a
  new major version.
- **The platform lacks a repair path.** A safe default that users cannot
  diagnose or change will be disabled through unsupported hacks.
- **Security is being used to avoid product clarity.** Judgement. A default
  should encode a known safe choice. It should not conceal an unresolved product
  decision behind a vague "secure mode."

An applicability test that works well in design review is this. Ask what a new
user would do if they read no security documentation and accepted every prompt.
If that path would be unsafe for a normal production deployment, the product has
a default problem. Then ask whether the product owner can name a safer value
that fits most users. If yes, use it. If no, make the product require an
explicit choice and refuse omission.

Another test is reversibility. A secure default should have a clear path for a
valid exception. That path may require an approval, a policy file, a command
line flag, or a higher product tier, but it must exist when the risky behavior
is a real use case. Otherwise teams will fork the template, patch the generated
code, or disable the platform guard entirely. The pattern works when exceptions
are visible. It fails when exceptions become shadow configuration.

## 5. Structure

The pattern has six participants.

- **Safe Baseline.** The configuration, generated code, policy, runtime guard,
  or product behavior that is active without extra user action. It should be
  production-suitable for the common case.
- **Risky Capability.** A capability that may be valid but can expose data,
  widen privilege, lower transport protection, weaken isolation, or expand
  attack surface.
- **Explicit Opt-Out.** A named setting, flag, role binding, manifest field, or
  migration step that activates the risky capability. It should be searchable in
  source and visible in generated configuration.
- **Guardrail.** Code that rejects missing, ambiguous, or unsafe configuration.
  In access control this is the default-deny decision. In transport it may be
  redirect-to-HTTPS or refusal to start with an insecure listener.
- **Audit Surface.** Logs, metrics, config inventory, startup warnings, policy
  reports, and tests that reveal both the baseline and any opt-out.
- **Owner Boundary.** The team or module that owns the safe baseline, the
  compatibility policy, and the approved ways to opt out.

Relationships. The user touches the product through a default path. The default
path applies the Safe Baseline and invokes Guardrails before the Risky
Capability can run. The Explicit Opt-Out is the only route to the risky mode.
The Audit Surface records which route was taken. The Owner Boundary decides
which defaults are versioned, which opt-outs are allowed, and which old opt-outs
must expire.

The design is weaker if the opt-out is a negative double such as
`disable_security = true`. Prefer a name tied to the actual behavior, such as
`allow_public_read`, `listen_on_all_interfaces`, or `allow_http`. The name is a
small control surface. It tells reviewers what risk was accepted.

The participants should be separated in code. The Config Loader should parse
syntax and apply default values. The Guardrail should validate the effective
state. The Runtime should receive a complete, already validated policy object.
Mixing those roles creates ambiguous behavior, for example a runtime method that
silently fills missing policy with broad access because a parser forgot to do
so. Split Phase is often the right refactoring here. Parse first, validate
second, run third.

The Audit Surface is part of the structure, not an optional reporting feature.
Without it, secure defaults cannot be governed at scale. A platform owner needs
to know which services use the current baseline, which services use a
compatibility mode, and which services have risky flags. That inventory should
be machine-readable. Human memory is not a control.

## 6. ASCII structure diagram

```text
        +--------------------+
        | User or Template   |
        | accepts defaults   |
        +---------+----------+
                  |
                  v
        +--------------------+       owns         +--------------------+
        | Safe Baseline      |<-------------------| Owner Boundary     |
        | closed, private,   |                    | platform, product, |
        | encrypted, scoped  |                    | security team      |
        +---------+----------+                    +---------+----------+
                  |                                         |
                  v                                         |
        +--------------------+                              |
        | Guardrail          | rejects absent or             |
        | policy and checks  | unsafe intent                 |
        +----+----------+----+                              |
             |          |                                   |
             | safe     | explicit opt-out                  |
             v          v                                   |
   +----------------+  +--------------------+               |
   | Normal Runtime |  | Risky Capability   |               |
   | safe behavior  |  | public, broad, or  |               |
   +-------+--------+  | weaker behavior    |               |
           |           +----------+---------+               |
           |                      |                         |
           v                      v                         |
        +--------------------------------+                  |
        | Audit Surface                  |------------------+
        | logs, metrics, inventory, tests|
        +--------------------------------+
```

## 7. Dynamics

The runtime flow should make safe behavior the short path. Risky behavior should
take the longer path with a named decision and telemetry.

```text
Actor        Config Loader       Guardrail       Runtime       Audit
  |                |                 |              |            |
  |-- start app -->|                 |              |            |
  |                |-- load cfg ---->|              |            |
  |                |                 |-- check ---->|            |
  |                |                 |              |            |
  |                |<-- no opt-out --|              |            |
  |                |                 |-- safe mode ------------->|
  |                |                 |              |-- serve -->|
  |                |                 |              |            |
  |-- start app -->|                 |              |            |
  |                |-- load cfg ---->|              |            |
  |                |   allow_http    |              |            |
  |                |                 |-- validate opt-out ------>|
  |                |                 |-- risky mode ------------>|
  |                |                 |              |-- serve -->|
  |                |                 |              |            |
  |-- start app -->|                 |              |            |
  |                |-- load cfg ---->|              |            |
  |                |   ambiguous     |              |            |
  |                |                 |-- reject --------------->|
  |<-- startup failure -------------|              |            |
```

The same dynamics apply to authorization. A request arrives without a matching
grant. The policy engine returns deny. If a grant exists, the policy engine
returns allow and records the policy rule. If the policy file is missing,
unparseable, stale, or ambiguous, the guard should deny by default and emit a
visible failure.

## 8. Implementation variants

**Deny-by-default authorization.** The policy engine starts from denial and
allows only actions covered by a positive rule. Kubernetes documentation warns
against `AlwaysAllow` mode and describes authorization modes that return deny
or no opinion
([Kubernetes Authorization](https://kubernetes.io/docs/reference/access-authn-authz/authorization/index.html),
verified 2026-08-02). This is the closest implementation of Saltzer and
Schroeder's fail-safe defaults principle.

**Safe generated template.** A project generator emits secure headers, CSRF
protection, strict cookie flags, private network bindings, scoped roles, and
minimal permissions. The user can change them, but the generated artifact is
already on the safe path. Rails documents CSRF token verification for newly
created applications and default security headers in its security guide
([Rails Security Guide](https://guides.rubyonrails.org/security.html),
verified 2026-08-02).

**Automatic secure transport.** The server chooses HTTPS when it has a hostname
and manages the certificate path. Caddy's HTTPS quick start says Caddy uses
HTTPS for sites by default when a host name is provided
([Caddy HTTPS quick start](https://caddyserver.com/docs/quick-starts/https),
verified 2026-08-02). This variant moves a fragile operator task into the
server baseline.

**Runtime isolation by default.** The platform isolates processes, storage, or
origins unless the application asks for broader sharing. Chrome Enterprise
documentation states that Site Isolation is enabled by default on desktop
platforms as of Chrome 76 and for most signed-in Android sites as of Chrome 77
([Chrome Enterprise Site Isolation](https://support.google.com/chrome/a/answer/7581529?hl=en),
verified 2026-08-02). Android documentation describes scoped storage behavior
and the legacy opt-out path for apps targeting Android 10
([Android storage use cases](https://developer.android.com/training/data-storage/use-cases?hl=en),
verified 2026-08-02).

**Safe API default with explicit risk flag.** A library function takes a config
object where omitted fields choose the safe value. To enable a risky behavior,
the caller must set a field with a risk-bearing name. This is the most common
application-code form.

**Policy-as-code baseline.** A platform stores the safe baseline in policy
rules, then applies it at build, admission, deploy, or runtime. The default is
not scattered across projects. It is a versioned artifact with review history.

**Compatibility mode.** The product changes a default in a new major version
and offers a named compatibility opt-out for older workloads. This variant
should have a removal date. Otherwise the risky mode becomes permanent.

**Interactive explicit choice.** When there is no known safe default, the
installer refuses to continue until the user chooses. This is still in the
pattern family because absence of a choice does not silently pick the risky
mode.

**Immutable baseline object.** The product constructs one effective security
profile during startup, freezes it, and passes it to the runtime. This avoids
late mutation, where a background job or plugin changes a guard after startup.
It also makes testing easier because the effective profile can be printed and
compared.

**Scoped unsafe mode.** The opt-out applies to one route, one origin, one
service account, one tenant, or one local profile rather than to the whole
process. This variant is more work than a global flag, but it preserves most of
the baseline while allowing a narrow exception.

**Progressive enforcement.** The platform first reports risky defaults, then
warns, then blocks new deployments, then blocks existing deployments. This
variant is useful where a large fleet has old behavior. It should have dates,
owners, and measurable exit criteria.

**Secure profile inheritance.** A platform publishes profiles such as `local`,
`staging`, and `production`. Each profile has explicit differences, and the
production profile is the one CI or deployment policy requires. This lowers
copy-paste drift between environments while still permitting local workflows.

## 9. Known production uses

**Caddy, automatic HTTPS.** Caddy's public documentation states that Caddy uses
HTTPS for sites by default when a host name is provided, and the quick start
shows certificate provisioning without a separate TLS setup step
([Caddy HTTPS quick start](https://caddyserver.com/docs/quick-starts/https),
verified 2026-08-02). The production use is a web server making encrypted
transport the default path instead of an operator add-on.

**Chrome, Site Isolation.** Google Chrome Enterprise documentation states that
Site Isolation separates pages from different websites into different
processes, and that it is enabled by default on desktop platforms as of Chrome
76
([Chrome Enterprise Site Isolation](https://support.google.com/chrome/a/answer/7581529?hl=en),
verified 2026-08-02). The production use is a browser platform moving origin
isolation into the default runtime model.

**Android, scoped storage.** Android developer documentation describes
app-scoped storage and the `requestLegacyExternalStorage` opt-out for apps
targeting Android 10, with that legacy attribute ignored for apps running on
Android 11 when targeting the newer model
([Android storage use cases](https://developer.android.com/training/data-storage/use-cases?hl=en),
verified 2026-08-02). The production use is a mobile platform reducing default
file exposure between apps.

**Rails, CSRF and security headers.** The Rails security guide says token-based
CSRF protection is automatic for newly created Rails applications when the
default forgery-protection setting is true, and it documents default security
headers returned by Rails responses
([Rails Security Guide](https://guides.rubyonrails.org/security.html),
verified 2026-08-02). The production use is a web framework placing common web
security controls in the generated application baseline.

**Django, CSRF middleware.** Django's CSRF documentation describes middleware
and template tags for protection against cross-site request forgery, with
unsafe methods protected by the documented token workflow
([Django CSRF documentation](https://docs.djangoproject.com/en/6.0/ref/csrf/),
verified 2026-08-02). The production use is a web framework making a common
request-forgery defense available through a standard middleware path.

**Kubernetes, authorization mode warning.** Kubernetes documentation warns that
`AlwaysAllow` bypasses authorization and should not be used where API clients
or workloads are not fully trusted
([Kubernetes Authorization](https://kubernetes.io/docs/reference/access-authn-authz/authorization/index.html),
verified 2026-08-02). The production use is a cluster control plane that
documents the danger of permit-by-default authorization and provides stricter
authorization modes.

## 10. Consequences

Engineering judgement. The consequences below are design effects observed in
systems that encode safe baselines. They should be tested in the local product.

Positive.

- The common path is safer because users who do not read every setting still
  receive a hardened baseline.
- Security review scales better. Reviewers can focus on opt-outs and policy
  changes rather than rediscovering the baseline in every service.
- New projects inherit the platform's current security posture at creation
  time.
- Risky modes become searchable. A reviewer can look for `allow_public_read`,
  `allow_http`, or `automountServiceAccountToken` instead of inferring intent.
- Incident blast radius usually shrinks because default permissions are
  narrower and default sharing is lower.
- Onboarding becomes clearer for junior teams. The platform expresses the
  preferred path in code, not in a separate wiki page.

Negative.

- The product may refuse to start in configurations that previously worked.
- Compatibility risk rises when an old permissive default becomes closed.
- Operators may develop a false sense of safety if the default is good but the
  opt-out path is untracked.
- Some users will disable the guard if diagnostics are poor.
- The platform owner now owns migration work when the safe baseline changes.
- Safe defaults can hide complexity. Automatic certificate handling, for
  example, still needs storage, renewal, DNS, and failure diagnostics.
- Defaults can become stale. A secure cipher suite, header set, sandbox rule,
  or token lifetime must evolve as threats and standards change.

Neutral or mixed.

- Support load often moves rather than disappears. Instead of "how do I enable
  protection," users ask "why was my request denied" or "why did the server
  choose HTTPS."
- Documentation changes shape. The main page can describe the safe path, but
  the exception page must be precise, because exception users are operating
  near risk.
- Product metrics may initially look worse. Denied requests, blocked deploys,
  and startup failures become visible. That is often a sign that hidden risk is
  being surfaced, not that the product became less reliable.
- Ownership becomes clearer and therefore more political. A default has an
  owner, and the owner must answer for both strictness and compatibility.

The biggest positive consequence is compounding. One good default in a template
may be copied into hundreds of services and thousands of deploys. The biggest
negative consequence is also compounding. One bad default in a template can
propagate at the same speed. This is why default changes deserve design review,
tests, and release notes even when the code change is small.

## 11. Failure modes and misuse

Engineering judgement. Each item is written as an observable production
failure, not as a theoretical mistake.

**Symptom.** A newly created service exposes an internal admin endpoint on a
public interface during a preview deployment.

**Cause.** The generated server template binds to `0.0.0.0` and relies on a
later firewall or ingress rule to narrow exposure.

**Fix.** Bind to localhost or a private interface by default. Require
`listen_on_all_interfaces = true` for public binding, log that setting at
startup, and test generated projects for their listener address.

**Symptom.** A tenant reads another tenant's data after a new feature launches,
but only for records lacking an explicit access row.

**Cause.** The authorization function treats missing policy as allow or no
opinion.

**Fix.** Make missing policy deny. Add a contract test where absent policy,
  corrupt policy, and unknown action all return deny.

**Symptom.** Users see TLS failures after a certificate automation feature was
adopted, and operators cannot tell whether DNS, storage, issuer rate limits, or
local trust setup caused the failure.

**Cause.** Secure transport was automated, but the automation did not expose
diagnostic events.

**Fix.** Emit structured events for certificate request, validation challenge,
storage write, renewal, redirect setup, and fallback. Keep HTTPS as the default
path, but make failures explainable.

**Symptom.** Teams add `allow_http = true` to many services to make local
development easier, and the flag later appears in production manifests.

**Cause.** The opt-out was not scoped by environment and was not blocked by
deployment policy.

**Fix.** Gate risky flags by environment. Permit them in local profiles, reject
them in production admission checks, and report all use in configuration
inventory.

**Symptom.** A major version upgrade breaks clients because anonymous read is
now denied by default.

**Cause.** The product changed a default without a migration path, warning
period, or compatibility mode.

**Fix.** Ship a versioned migration. Warn before the change, provide an
explicit compatibility flag with a removal date, and generate a report of
resources that need grants.

**Symptom.** A security team believes every service has CSRF protection, but
custom controllers or API endpoints bypass it.

**Cause.** The default template includes the middleware, but the bypass API is
too easy to use and not audited.

**Fix.** Make bypass calls require a named reason, add static analysis for the
  bypass API, and trace rejected as well as accepted unsafe requests.

**Symptom.** A generated role works for every feature but also grants future
resource types the team did not know about.

**Cause.** The default policy uses wildcard permissions.

**Fix.** Generate enumerated permissions. Add a test that fails when the
resource set grows without a matching policy review.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Secure by Default | Secure by Checklist | Permit by Default | Runtime Detection | Manual Hardening Guide | Zero Trust Architecture |
|---|---|---|---|---|---|---|
| First-run safety | High. Safe baseline is active | Medium. Depends on completion | Low. Open until changed | Low. Detects after action | Low to medium. Depends on operator | High when fully built |
| First-run friction | Medium. Some actions need opt-out | High. Many manual steps | Low | Low | High | High |
| Coupling to platform | Medium to high | Low | Low | Medium | Low | High |
| Compatibility | Medium risk when defaults change | High compatibility | High compatibility | High compatibility | High compatibility | Medium risk |
| Operability | Good if audit is built | Varies by checklist quality | Simple until incident | Alert-heavy | Varies by operator skill | Requires mature telemetry |
| Latency | Policy checks may add cost | No runtime cost after setup | Lowest | Monitoring cost | No direct runtime cost | Multiple checks per request |
| Team topology | Platform owned baseline | Security review bottleneck | Team owned risk | SecOps owned alerts | Operator owned hardening | Platform and identity teams |
| Failure mode | False deny, bad opt-out | Missed step | Silent exposure | Late detection | Drift | Policy sprawl |
| Best fit | Repeated product setup | Low-scale regulated deploy | Trusted closed lab | Legacy system coverage | Small expert team | Distributed service estate |

Reading of the table. Secure by Default wins when many users repeat the same
setup and a safe baseline is known. Secure by Checklist fits rare deployments
with expert operators. Runtime Detection fits legacy systems where defaults
cannot change yet. Zero Trust Architecture is broader than this pattern. It
uses secure defaults but also requires identity, policy, network boundaries,
device posture, and continuous verification.

## 13. Related and incompatible patterns

- **Least Privilege.** Secure by Default is the delivery mechanism for least
  privilege. The default role, token, service account, or generated policy
  should carry the smallest permission set that supports the common use.
- **Complete Mediation.** The default-deny rule matters only if every access is
  checked. If a second path bypasses the guard, secure defaults protect only
  the visible path.
- **Defense in Depth.** Secure defaults should not be the only layer. A private
  default bucket still needs identity checks, audit, encryption, and network
  controls.
- **Policy as Code.** Composes well. The baseline can be reviewed, tested, and
  rolled forward as code rather than copied through documentation.
- **Secure Configuration.** Secure by Default is the starting point. Secure
  Configuration is the long-term state, including drift detection and approved
  exceptions.
- **Feature Flags.** Can compose or conflict. Flags are a clean opt-out channel
  when they are typed, audited, and environment-scoped. They conflict when a
  global flag disables a guard for every tenant.
- **Service Locator.** Often conflicts. A global locator creates ambient
  authority, where any code can ask for privileged objects without declaring
  need.
- **Permit by Default.** Directly incompatible for authorization and exposure
  controls. It starts open and tries to enumerate danger, the opposite of
  fail-safe defaults.
- **Compatibility Mode.** A temporary companion during migration. It becomes an
  anti-pattern when it has no owner, no expiry, and no telemetry.

## 14. Refactoring path in and out

Introducing Secure by Default into an existing product.

1. Inventory the defaults that affect exposure. Include network listeners,
   storage visibility, generated roles, cookies, cross-origin rules, token
   lifetime, TLS, logging of sensitive fields, secret delivery, and generated
   templates.
2. Classify each default as safe, risky, or context-dependent. For
   context-dependent items, decide whether the product should ask for an
   explicit choice rather than choosing.
3. Add tests that pin current behavior before changing anything. The first test
   should prove the risky default exists.
4. Introduce the safe path behind a new setting while the old behavior remains
   available. Prefer `allow_public_read` over `disable_private_mode`.
5. Emit startup warnings and inventory records for the old risky behavior.
6. Change new projects, new resources, or new major-version deployments to the
   safe default. Keep old deployments on a compatibility path if the contract
   requires it.
7. Add deployment policy that blocks risky opt-outs in production unless an
   approved exception exists.
8. Remove the compatibility path after the warning window. If removal is not
   possible, keep it visible in telemetry and documentation.

Named refactorings often used along this path include Replace Magic Literal
with Symbolic Constant for risky flags, Encapsulate Variable for scattered
settings, Split Phase for separate parse and validate steps, and Separate Query
from Modifier when a validation call also mutates runtime state.

Refactoring out of the pattern is rarer but valid.

1. Prove that the default is causing more harm than it prevents. Use incident
   data, support volume, false-deny metrics, and migration failures.
2. Replace the automatic default with an explicit required choice rather than a
   permissive default.
3. Keep the old secure mode as a named profile so teams that need it can still
   select it.
4. Remove policy checks only after an equivalent control exists elsewhere.
5. Update tests so missing configuration fails, instead of silently selecting
   the old baseline.

## 15. Testing and verification

Engineering judgement. Tests should prove the absence of unsafe behavior when
configuration is absent, malformed, stale, or partially migrated.

Unit tests.

- Missing authorization rule returns deny.
- Unknown action returns deny.
- Corrupt policy returns deny and reports a diagnostic.
- Default config uses private binding, HTTPS, scoped storage, secure cookies, or
  narrow roles as applicable.
- Risky mode requires a named opt-out field.
- Risky opt-out is rejected in production profile.
- Generated templates contain the safe baseline.

Integration tests.

- Start the service with an empty config and verify the effective config.
- Start with an explicit opt-out and verify both behavior and audit event.
- Start with ambiguous config and verify startup failure.
- Exercise real middleware for unsafe HTTP methods, not only controller units.
- Run admission or deploy policy against representative manifests.

Security tests.

- Attempt access without a grant.
- Attempt access with a grant for a different tenant or scope.
- Attempt downgrade to HTTP, public binding, broad CORS, unsigned cookie, or
  unscoped token.
- Attempt to bypass middleware through custom routes, alternate handlers, or
  background jobs.

Regression tests should lock the dangerous defaults that were fixed. A test
named `missing_policy_denies` is better than a broad test named
`security_works`, because it records the rule the pattern depends on.

Verification should include generated artifacts. If a CLI creates a new
project, the test should run the CLI and inspect the result. If a Helm chart,
Terraform module, SDK, or framework generator supplies defaults, test the
rendered output rather than the helper function alone. Many default failures
occur in glue code, not in the guard itself.

Verification should include upgrade paths. Start from an old permissive config,
run the migration, and assert that the new effective state is either safe or
requires an explicit compatibility flag. Test the warning text too. A warning
that does not name the setting and replacement action will be ignored in large
deploy logs.

Verification should include abuse of the opt-out. Set the risky flag in the
wrong environment, in the wrong file, under an alias, and through a deprecated
path. The system should either reject it or record it in the same inventory as
the primary flag. The attack is often not on the default. It is on the escape
hatch.

Code examples below implement a small authorization and transport-policy
baseline. TypeScript, Python, and Go are chosen because secure defaults often
appear as configuration APIs and policy evaluators in service code. Java, Rust,
and Swift are omitted here only to keep the examples focused.

### TypeScript

```typescript
type Action = "read" | "write" | "admin";

type Rule = {
  subject: string;
  action: Action;
};

type Config = {
  allowHttp?: boolean;
  rules?: Rule[];
};

function can(subject: string, action: Action, config: Config): boolean {
  const rules = config.rules ?? [];
  return rules.some((rule) => rule.subject === subject && rule.action === action);
}

function scheme(config: Config): "https" | "http" {
  return config.allowHttp === true ? "http" : "https";
}

const base: Config = { rules: [{ subject: "billing", action: "read" }] };

console.log(can("billing", "read", base));
console.log(can("billing", "admin", base));
console.log(scheme({}));
```

### Python

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    subject: str
    action: str


@dataclass(frozen=True)
class Config:
    rules: tuple[Rule, ...] = ()
    allow_http: bool = False


def can(subject: str, action: str, config: Config) -> bool:
    return any(rule.subject == subject and rule.action == action for rule in config.rules)


def scheme(config: Config) -> str:
    return "http" if config.allow_http else "https"


if __name__ == "__main__":
    base = Config(rules=(Rule("billing", "read"),))
    print(can("billing", "read", base))
    print(can("billing", "admin", base))
    print(scheme(Config()))
```

### Go

```go
package main

import "fmt"

type Rule struct {
	Subject string
	Action  string
}

type Config struct {
	Rules     []Rule
	AllowHTTP bool
}

func Can(subject, action string, config Config) bool {
	for _, rule := range config.Rules {
		if rule.Subject == subject && rule.Action == action {
			return true
		}
	}
	return false
}

func Scheme(config Config) string {
	if config.AllowHTTP {
		return "http"
	}
	return "https"
}

func main() {
	base := Config{Rules: []Rule{{Subject: "billing", Action: "read"}}}
	fmt.Println(Can("billing", "read", base))
	fmt.Println(Can("billing", "admin", base))
	fmt.Println(Scheme(Config{}))
}
```

## 16. Observability signals

Secure defaults are not visible enough until the system reports the effective
state. Record the baseline, the opt-outs, and the refusals.

What to log or measure.

- Effective security profile at startup, including config version and whether
  any risky opt-out is active.
- Count of denied authorization decisions by subject type, action, resource
  type, and rule outcome. Avoid logging sensitive resource identifiers unless
  local policy allows it.
- Count of risky opt-outs by environment and service.
- Certificate automation events, including request, validation, renewal,
  storage, and failure class.
- Middleware bypass count, grouped by bypass reason.
- Generated template version in each deployed service.
- Admission or policy failures for broad roles, public storage, insecure
  transport, wildcard origins, and token auto-mount.
- Time since last baseline update for each service.

A healthy dashboard has boring shape. Most services report the standard
profile. Risky opt-outs are rare, named, reviewed, and tied to owners. Denials
exist and move with traffic, because a default-deny system should refuse some
invalid requests. Certificate and policy errors are low and explainable.

A failing dashboard has one of four shapes. First, opt-outs spread across
services after a template change, which means the default is too painful or
poorly documented. Second, denials drop to zero after a deploy, which may mean
the guard stopped running. Third, production services run with local or
development profiles. Fourth, the baseline version differs widely across
services, which means old unsafe templates may still be alive.

Alerts should be sparse and tied to action. Alert when a production service
activates a risky opt-out for the first time, when a service regresses to an old
baseline version, when default-deny checks stop producing any decision events,
or when a policy parser enters fail-open behavior. Do not page on every denied
request. A deny is normal. Page on changes that suggest the guard is gone, the
baseline moved backward, or an exception escaped its approved scope.

Trace attributes should avoid secret or tenant-rich values. Prefer rule IDs,
profile names, control names, and coarse resource classes. A trace saying
`auth.default=deny`, `rule_id=orders_read_v3`, and `profile=production` is
useful. A trace that records full user identifiers, object names, and raw
policy text may create a privacy incident in the monitoring system.

Configuration inventory is the long-term signal. Logs help during one incident.
Inventory answers fleet questions. Which services still use compatibility
mode? Which generated projects predate the current baseline? Which opt-outs
have no owner? Which teams carry public-read storage? Without that inventory,
the organization has a pattern in code but not in operations.

## 17. Security and privacy implications

Security is the point of the pattern, but it still opens trade-offs.

Attack surface reduced.

- Missing access rules fail closed.
- New resources start private.
- Transport starts encrypted where the product can automate it.
- Generated projects include common web defenses.
- Service accounts and tokens start with narrow scope.
- Storage and process isolation become a platform default.

Attack surface opened or shifted.

- The opt-out mechanism becomes a target. An attacker who can set
  `allow_public_read` or `allow_http` can bypass the baseline.
- The baseline owner becomes a concentration point. A bad template or policy
  release can affect every new service.
- Automation needs credentials. Certificate managers, policy engines, and
  deployment controllers often need privileges that must be scoped and audited.
- Compatibility flags can preserve old risk long after the migration window.

Privacy implications.

Secure defaults can reduce accidental data sharing through private storage,
scoped service identities, and deny-by-default access. They can also create
privacy-sensitive telemetry. Effective policy logs may reveal user IDs,
resource names, tenant names, denied actions, or geographic routing. Treat
those logs as security data with retention limits and restricted access.

The pattern is silent on consent, purpose limitation, and data minimization. It
can make a privacy control easier to adopt, but it does not decide what data a
product should collect.

## 18. References

1. Jerome H. Saltzer and Michael D. Schroeder. "The Protection of Information
   in Computer Systems." *Proceedings of the IEEE*, volume 63, issue 9, 1975,
   pages 1278 to 1308. University of Virginia mirror:
   https://www.cs.virginia.edu/~evans/cs551/saltzer/
   Verified 2026-08-02. Source for fail-safe defaults, least privilege, and
   complete mediation lineage.
2. Microsoft. "Introduction." Security Development Lifecycle guidance,
   previous Microsoft Learn version. Section "Secure by Design, Secure by
   Default, Secure in Deployment, Communications."
   https://learn.microsoft.com/en-us/previous-versions/windows/desktop/cc307406%28v%3Dmsdn.10%29
   Verified 2026-08-02. Source for the SD3+C lineage.
3. OWASP Foundation. "Secure Product Design Cheat Sheet." Section
   "Configuration."
   https://cheatsheetseries.owasp.org/cheatsheets/Secure_Product_Design_Cheat_Sheet.html
   Verified 2026-08-02. Source for Secure by Default as product configuration
   guidance.
4. Caddy project. "HTTPS quick-start." Caddy Documentation.
   https://caddyserver.com/docs/quick-starts/https
   Verified 2026-08-02. Source for Caddy HTTPS default production use.
5. Google. "Protect your data with site isolation." Chrome Enterprise and
   Education Help.
   https://support.google.com/chrome/a/answer/7581529?hl=en
   Verified 2026-08-02. Source for Chrome Site Isolation production use.
6. Google. "Android storage use cases and best practices." Android Developers.
   https://developer.android.com/training/data-storage/use-cases?hl=en
   Verified 2026-08-02. Source for Android scoped storage production use.
7. Ruby on Rails. "Securing Rails Applications." Rails Guides.
   https://guides.rubyonrails.org/security.html
   Verified 2026-08-02. Source for Rails CSRF and default security headers
   production use.
8. Django Software Foundation. "Cross Site Request Forgery protection." Django
   documentation.
   https://docs.djangoproject.com/en/6.0/ref/csrf/
   Verified 2026-08-02. Source for Django CSRF middleware behavior.
9. Kubernetes project. "Authorization." Kubernetes documentation.
   https://kubernetes.io/docs/reference/access-authn-authz/authorization/index.html
   Verified 2026-08-02. Source for authorization modes and the `AlwaysAllow`
   warning.
10. Microsoft. "Architecture strategies for securing a development lifecycle."
   Azure Well-Architected Framework.
   https://learn.microsoft.com/en-us/azure/well-architected/security/secure-development-lifecycle
   Verified 2026-08-02. Source for default-deny application design guidance
   and lifecycle framing.
