---
name: Content Security Policy
slug: content-security-policy
family: 15-security
category: Security
aliases: [CSP, CSP header, Strict CSP, Browser Content Policy]
first_described: "Sterne 2012"
maturity: established
related: [defense-in-depth, secure-by-default, complete-mediation, least-privilege, csrf-token, session-management]
incompatible_with: [inline-script-by-default, wildcard-asset-policy, client-side-template-injection]
verified: 2026-08-02
---

# Content Security Policy

## 1. Name, aliases, and lineage

The canonical name is Content Security Policy. In daily engineering speech it is
shortened to CSP, CSP header, or browser content policy. The phrase strict CSP
means a script policy built around nonces or hashes, normally with
`strict-dynamic`, rather than a long host allowlist. The W3C Content Security
Policy Level 3 draft uses the name Content Security Policy and defines it as a
mechanism by which developers control resources a page can fetch or execute, as
well as related policy decisions
([https://www.w3.org/TR/CSP/](https://www.w3.org/TR/CSP/), verified
2026-08-02).

The first W3C Content Security Policy 1.0 Recommendation was published on 15
November 2012. Brandon Sterne of Mozilla is listed as editor on that
Recommendation, and CSP Level 2 later reached W3C Recommendation status on 15
December 2016 with Mike West, Adam Barth, and Dan Veditz as editors
([https://www.w3.org/TR/CSP2/](https://www.w3.org/TR/CSP2/), verified
2026-08-02). Level 3 is still published as a W3C Working Draft, with Mike West
and Antonio Sartori listed as editors in the 13 August 2026 draft
([https://www.w3.org/TR/CSP/](https://www.w3.org/TR/CSP/), verified
2026-08-02).

The lineage is browser-mediated defense in depth for content injection. CSP
does not replace escaping, sanitization, type-safe templates, Trusted Types, or
server-side authorization. The Level 3 draft states that CSP is not a first line
of defense against content injection and is best used as defense in depth
([https://www.w3.org/TR/CSP/](https://www.w3.org/TR/CSP/), verified
2026-08-02). MDN describes the header as a way for site administrators to
control resources a user agent may load for a page
([https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy),
verified 2026-08-02).

CSP is often confused with three related controls. It is not CORS, which governs
which origins may read selected responses. It is not HSTS, which tells browsers
to use HTTPS for future visits. It is not output encoding, which changes data so
that a parser treats it as text rather than code. CSP is a policy interpreted by
the browser after a response is received.

## 2. Problem and context

A web page runs with large ambient power. If an attacker can inject script into
the page, the browser grants that script access to the page's DOM, origin-bound
storage, same-origin fetch ability, and user interaction surface. The usual
root cause is a content injection bug, such as reflected XSS, stored XSS, DOM
XSS, unsafe template rendering, unsafe rich text, an unsafe dependency, or
markup accepted from a partner channel. MDN describes CSP's main use case as
controlling which resources, especially JavaScript resources, a document may
load, mainly as defense against XSS
([https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP),
verified 2026-08-02).

The problem appears in mature systems because pages accrete script entry points.
Templates gain inline boot code. Analytics tags arrive from a vendor. A payment
widget loads a nested script. A legacy page needs inline event handlers. A build
system emits hashes, then a later team adds a tag manager. At some point nobody
can answer, from code review alone, which script is allowed to execute on every
route. The browser, however, is the participant that sees the final document and
every load request. CSP moves part of the control decision to that participant.

The context is a browser-rendered document, worker, or embedded surface where
the server can deliver a policy with the response. The policy may be delivered
through `Content-Security-Policy`, through `Content-Security-Policy-Report-Only`,
or for a subset of features through a `meta` element. MDN notes that the header
form should be used for all responses and that the `meta` form does not support
all CSP features
([https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP),
verified 2026-08-02).

Engineering judgement. CSP earns its place when a page has enough value or
enough script surface that a browser-side policy will reduce exploit impact or
give useful telemetry. It is a poor substitute for fixing injection defects.
The clean mental model is this. Input handling prevents hostile bytes from
becoming markup. CSP limits what the browser will do if hostile markup still
appears.

## 3. Forces

Engineering judgement. CSP trades runtime restriction and incident visibility
for deployment complexity, browser variance, and extra coordination between
templates, build output, and operations.

- **Latency.** Mixed. The browser evaluates policies locally, so no extra
  request path call is required. Policy size can still increase response header
  bytes, and violation reporting can create background traffic.
- **Coupling.** Sacrificed between application code and response generation.
  A nonce in a header must match nonce attributes in the HTML generated for the
  same response. Static hash policies couple inline code bytes to a build step.
- **Consistency.** Favoured when policy construction is centralized. Sacrificed
  when each route hand-builds directives and drift appears between pages.
- **Operability.** Favoured when report-only rollout and report aggregation are
  used. Sacrificed when a policy blocks production assets without clear alerting.
- **Cost.** Mixed. A strict policy can reduce XSS impact without an expensive
  rewrite. It can also consume time in template cleanup, vendor negotiation, and
  report triage.
- **Team topology.** Favoured when a platform or security team owns defaults and
  feature teams request narrow exceptions. Sacrificed when third-party tags are
  owned by several business teams and no one owns the final policy.
- **Cognitive load.** Sacrificed. Engineers must understand fallback rules,
  nonces, hashes, `strict-dynamic`, report-only mode, and browser console output.
- **Privacy.** Mixed. CSP can reduce exfiltration paths when `connect-src`,
  `form-action`, and `default-src` are tight. Violation reports can include URLs
  or samples that need careful retention handling. The Level 3 draft has a
  security and privacy consideration for violation reports
  ([https://www.w3.org/TR/CSP/](https://www.w3.org/TR/CSP/), verified
  2026-08-02).

The pattern favours least privilege at the browser boundary and sacrifices some
developer convenience. A policy that allows all inline script and all origins is
mostly documentation, not a control.

## 4. Applicability and non-applicability

Reach for Content Security Policy when the following hold.

- A browser-rendered page carries authenticated user power, session cookies,
  private data, payment flow state, admin actions, or partner trust.
- The team can deliver response headers from a server, edge function, reverse
  proxy, framework middleware, or CDN rule.
- Script execution can be moved toward nonce-based or hash-based trust, or at
  least toward a smaller set of origins while legacy code is remediated.
- The organization can collect, sample, triage, and retire CSP reports instead
  of leaving report-only noise unowned.
- Third-party scripts are known, contractual, and reviewable. A policy cannot
  make an unknown tag supply chain safe.
- Clickjacking or form exfiltration risk matters, and directives such as
  `frame-ancestors` and `form-action` can express the intended browser behavior.
- The page is a platform surface embedded by another product, such as a Shopify
  admin app, where the valid frame ancestors depend on the authenticated shop.
  Shopify documents a `frame-ancestors` requirement for apps rendered in the
  Shopify admin
  ([https://shopify.dev/docs/apps/build/security/set-up-iframe-protection](https://shopify.dev/docs/apps/build/security/set-up-iframe-protection),
  verified 2026-08-02).

Do NOT reach for Content Security Policy in these cases.

- **There is no browser document.** JSON APIs, queues, CLIs, and server-to-server
  endpoints do not execute page script. A narrow API header such as
  `default-src 'none'; frame-ancestors 'none'` can help scanners, but CSP is not
  the main API control. Mozilla Observatory documents that API results may not
  reflect API security posture even when security headers are present
  ([https://developer.mozilla.org/en-US/observatory/docs/faq](https://developer.mozilla.org/en-US/observatory/docs/faq),
  verified 2026-08-02).
- **The team wants CSP instead of output encoding.** CSP can block many script
  execution paths, but the defect remains. Fix the injection path.
- **All script is managed by an uncontrolled tag manager.** A policy that trusts
  the tag manager and whatever it loads gives the attacker the same supply chain
  target.
- **The site requires arbitrary user-authored JavaScript.** A code playground,
  theme editor, or extension host needs sandboxing, origin isolation, and
  capability design. CSP may be one layer, but it is not the product boundary.
- **The HTML is static and contains changing inline boot data.** A nonce cannot
  be generated per response for cached bytes. Prefer external scripts, data
  attributes encoded as data, or hash-based policies when bytes are stable.
- **Browsers outside the supported matrix must receive equal protection.** CSP
  directive behavior changes by browser and version. A server-side mitigation is
  needed when browser support is not enough.
- **The policy would be maintained by copy-paste.** Route-local strings become
  stale. Build a typed policy builder or framework-level defaults first.
- **The policy would hide symptoms during migration.** Blocking reports are not
  a substitute for test failures. Use report-only mode before enforcement, then
  promote only after expected reports are explained.

## 5. Structure

The participants are named by their security role.

- **Policy author.** Defines the intended browser powers for a route, route
  group, or whole product. In a large organization this is often a security
  platform team plus route owners.
- **Policy generator.** Produces the serialized directive string. It may be a
  web framework middleware, CDN configuration, reverse proxy, edge function, or
  typed application helper.
- **Protected response.** The HTTP response that carries the policy and the HTML
  or worker script to which it applies.
- **Browser policy engine.** Parses the serialized CSP, stores it with the
  document or worker, and checks fetches, inline script, inline style, dynamic
  code evaluation, form submission, and embedding decisions.
- **Trust token.** A nonce or hash source expression for script or style. In a
  nonce policy, the same unpredictable value must appear in the response header
  and in trusted elements for that response.
- **Resource request.** A script, style, image, font, connection, worker, frame,
  form action, manifest, or other browser action covered by a directive.
- **Violation reporter.** The browser path that emits reports to a configured
  reporting endpoint or to console tooling. MDN describes Reporting API delivery
  through `Reporting-Endpoints` and `report-to`
  ([https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy),
  verified 2026-08-02).
- **Report collector.** A service that accepts reports, deduplicates noisy
  signals, redacts sensitive fields, and routes actionable findings.

Relationships. The policy author expresses allowed browser powers as
directives. The policy generator serializes those directives into a response
header. The protected response binds policy and document. The browser policy
engine mediates later browser actions. The report collector closes the loop by
showing where the declared policy and real page behavior diverge.

The key structural choice is where policy knowledge lives. In a server-rendered
application, the policy generator can create one nonce per response and pass it
to templates. In a static application, the generator cannot mutate each HTML
response, so hashes or external scripts are a better fit.

## 6. ASCII structure diagram

```text
  +----------------+        policy model        +-------------------+
  | Policy author  | -------------------------> | Policy generator  |
  +----------------+                            +---------+---------+
                                                           |
                                                           | header
                                                           v
  +----------------+       protected response     +--------+--------+
  | HTML template  | ---------------------------> | Browser policy  |
  | or worker body |                             | engine          |
  +-------+--------+                             +--------+--------+
          |                                               |
          | nonce or hash                                 | checks
          v                                               v
  +----------------+                             +-----------------+
  | Trusted script |                             | Resource request|
  | or style       |                             | script, frame   |
  +----------------+                             +--------+--------+
                                                           |
                                                           | violation
                                                           v
                                                  +----------------+
                                                  | Report collector|
                                                  +----------------+
```

## 7. Dynamics

At runtime, CSP is a browser-side mediation loop. The server chooses policy. The
browser applies it to later browser behavior.

```text
Client        Server         Template       Browser CSP       Collector
  |             |               |               |                 |
  | GET /page   |               |               |                 |
  |------------>|               |               |                 |
  |             | create nonce  |               |                 |
  |             |-------------->|               |                 |
  |             | render HTML   |               |                 |
  |             |<--------------|               |                 |
  | 200 + CSP header + HTML     |               |                 |
  |<------------|               |               |                 |
  |             |               | parse policy  |                 |
  |             |               |-------------->|                 |
  |             |               | script load?  |                 |
  |             |               |-------------->|                 |
  |             |               | allow or block|                 |
  |             |               |<--------------|                 |
  |             |               | report if set |                 |
  |             |               |-------------->| POST report     |
  |             |               |               |---------------->|
```

Four details matter in the dynamics.

First, enforcement is per protected resource. A site-wide policy is achieved by
sending a compatible policy on every relevant response, not by setting one
global browser state. CSP Level 2 states that a server supplies policy with each
resource representation when it wants policy for an entire site
([https://www.w3.org/TR/CSP2/](https://www.w3.org/TR/CSP2/), verified
2026-08-02).

Second, report-only mode runs the checks without blocking. MDN documents
`Content-Security-Policy-Report-Only` as a response header for monitoring CSP
violations before an enforced policy is applied
([https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy-Report-Only](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy-Report-Only),
verified 2026-08-02).

Third, multiple policies can be active. MDN states that adding policies can only
further restrict the protected resource, because every active policy must allow
the action
([https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy),
verified 2026-08-02).

Fourth, nonce policies depend on response identity. If a CDN caches HTML with a
nonce and serves it with a different header, trusted scripts will fail. If it
serves both stale HTML and stale header together, the nonce can repeat. OWASP
warns that nonce values should be unique one-time values per HTTP response
([https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html),
verified 2026-08-02).

## 8. Implementation variants

**Strict nonce policy.** The server creates a fresh nonce per HTML response,
adds it to `script-src`, and stamps the same value on trusted script elements.
Google's web.dev guidance recommends a nonce-based strict CSP for server-rendered
HTML pages
([https://web.dev/articles/security-headers](https://web.dev/articles/security-headers),
verified 2026-08-02). This variant fits Rails, Django, Java servlet filters,
Go templates, and edge-rendered pages. It does not fit static cached HTML unless
the edge can rewrite both header and body in the same response.

**Strict hash policy.** The build system computes hashes for stable inline
scripts and emits those hashes in `script-src`. web.dev recommends hash-based
strict CSP when HTML must be served statically or cached
([https://web.dev/articles/security-headers](https://web.dev/articles/security-headers),
verified 2026-08-02). The trade-off is byte sensitivity. Formatting a trusted
inline script changes the hash.

**Host allowlist policy.** The policy lists trusted origins such as the
application origin, asset CDN, font provider, and API endpoints. This variant is
easy to begin and useful for non-script fetches such as images and connections.
It is weaker for script execution because many trusted origins can serve
attacker-influenced script paths or JSONP-like gadgets. The paper "CSP is Dead,
Long Live CSP" was accepted at ACM CCS 2016 and argued that whitelist-based
policies were commonly bypassable, motivating nonce and hash based CSP
([https://www.sigsac.org/ccs/CCS2016/accepted-papers/index.html](https://www.sigsac.org/ccs/CCS2016/accepted-papers/index.html),
verified 2026-08-02).

**Report-only rollout.** The server sends `Content-Security-Policy-Report-Only`
with candidate directives and a reporting endpoint. This variant is for
migration. It is not protection, but it is the normal path to protection because
real pages often load assets that nobody remembered.

**Framework middleware.** Django 6.0 includes
`ContentSecurityPolicyMiddleware`, settings for enforced and report-only
policies, and nonce support through a template context variable
([https://docs.djangoproject.com/en/6.0/howto/csp/](https://docs.djangoproject.com/en/6.0/howto/csp/),
verified 2026-08-02). Rails has a content security policy DSL, report-only
setting, and nonce helpers in its security guide
([https://guides.rubyonrails.org/security.html](https://guides.rubyonrails.org/security.html),
verified 2026-08-02). Middleware reduces drift, but it can hide route-specific
exceptions if configuration becomes too broad.

**Edge or reverse proxy policy.** A CDN, ingress, or reverse proxy adds the
header outside the app. This is useful for static assets, legacy apps, and
central policy ownership. It is dangerous for nonce policies unless the same
component can modify the HTML body or the app supplies the nonce.

**Embedding policy.** A route uses `frame-ancestors` to state who may embed it.
Shopify requires embedded apps rendered in the Shopify admin to set
`frame-ancestors` dynamically for the shop domain and `admin.shopify.com`
([https://shopify.dev/docs/apps/build/security/set-up-iframe-protection](https://shopify.dev/docs/apps/build/security/set-up-iframe-protection),
verified 2026-08-02). This is CSP used for clickjacking control rather than
script trust.

**Trusted Types policy.** CSP can require Trusted Types for DOM XSS injection
sinks through `require-trusted-types-for 'script'`. The Trusted Types W3C draft
defines CSP integration for this directive and `trusted-types`
([https://www.w3.org/TR/trusted-types/](https://www.w3.org/TR/trusted-types/),
verified 2026-08-02). This variant fits large client-heavy applications where
DOM sink use is the main remaining script injection path.

**Policy as route capability.** Some systems model CSP as a capability set on a
route definition. The route declares whether it needs scripts, frames, image
sources, connections, a report-only trial, or an embedding exception. The
central generator turns those route capabilities into directives. This variant
fits products with many route owners because review can focus on a small
declarative diff rather than a raw header string. The trade-off is that the
capability vocabulary must stay small. If the vocabulary grows until it mirrors
the full CSP grammar, the abstraction no longer helps.

**Policy as build artifact.** Static site generators and single-page app builds
can emit a manifest containing script hashes, style hashes, asset origins, and a
policy version. The deploy step reads the manifest and configures the CDN or
server headers. This variant keeps hashes tied to the bytes that generated them.
The risk is split ownership. If one pipeline emits HTML and another pipeline
publishes headers, stale hashes can block a release. Treat the policy manifest
as part of the same artifact as the HTML.

## 9. Known production uses

**GitHub.com.** GitHub published a CSP rollout case study in 2016, describing
early adoption on GitHub.com, an initial policy, later tightened directives, and
bug bounty findings that influenced the policy. The article shows a then-current
policy with `default-src 'none'`, `base-uri 'self'`, `frame-ancestors 'none'`,
and many resource-specific directives
(`https://github.blog/engineering/platform-security/githubs-csp-journey/`,
verified 2026-08-02).

**Shopify storefront and app platform.** Shopify tells app developers that apps
rendered in the Shopify admin must set a proper `frame-ancestors` directive and
that a missing or incorrect directive can cause App Store rejection
([https://shopify.dev/docs/apps/build/security/set-up-iframe-protection](https://shopify.dev/docs/apps/build/security/set-up-iframe-protection),
verified 2026-08-02). Shopify's security best practices also state that Shopify
serves a CSP that limits what browsers load, while warning developers to treat
it as a backstop rather than a hard control for app or theme code
([https://shopify.dev/docs/apps/build/security/following-security-best-practices](https://shopify.dev/docs/apps/build/security/following-security-best-practices),
verified 2026-08-02).

**Google Photos and CSP Evaluator.** Google's web.dev security headers guide
names Google Photos as a nonce-based strict CSP example and CSP Evaluator as
another nonce-based strict CSP example that readers can inspect with DevTools
([https://web.dev/articles/security-headers](https://web.dev/articles/security-headers),
verified 2026-08-02).

**GitLab self-managed.** GitLab Omnibus documents a
`gitlab_rails['content_security_policy']` configuration with `enabled`,
`report_only`, and directive overrides, and states that GitLab supplies secure
default values for directives not explicitly configured
([https://github.com/gitlabhq/omnibus-gitlab/blob/master/doc/settings/configuration.md](https://github.com/gitlabhq/omnibus-gitlab/blob/master/doc/settings/configuration.md),
verified 2026-08-02).

These examples matter because they show different shapes. GitHub is a large
first-party web product. Shopify is a platform with embedded third-party apps.
Google Photos and CSP Evaluator show strict nonce use. GitLab exposes CSP as
operator configuration for a packaged product.

They also show that production CSP is not one uniform header copied between
companies. GitHub's published policy emphasized a first-party application with
asset and rendering domains. Shopify's requirement centers on embedding because
apps run inside the Shopify admin surface. Google's examples emphasize strict
script trust. GitLab's configuration exposes a packaged product knob for
self-managed operators. Engineering judgement. A good entry point for a new
team is to identify which of those shapes matches its product before choosing a
directive set.

## 10. Consequences

Engineering judgement. The benefits are strongest when the policy is narrow,
centralized, and backed by telemetry. The costs are highest on legacy pages with
many inline scripts and diffuse vendor ownership.

Positive consequences.

- Browser execution is constrained even when an injection bug survives review.
- The policy documents expected script, connection, frame, image, style, font,
  worker, and form destinations in a form the browser can enforce.
- Report-only mode gives a migration path and can reveal forgotten dependencies,
  suspicious injection attempts, and browser extension noise.
- `frame-ancestors` can replace older clickjacking controls for modern browsers
  and can express multiple allowed ancestors.
- `base-uri` blocks attacks that inject a `base` element to retarget relative
  links or scripts.
- `object-src 'none'` removes legacy plugin execution from the page.
- `default-src 'none'` changes the policy stance from permissive to explicit.
- Strict nonce or hash policies let teams stop maintaining long script host
  allowlists.

Negative consequences.

- A bad policy can break production pages in a way that looks like random asset
  failure to users.
- A too-broad policy creates false confidence while leaving attacker execution
  paths open.
- Nonce handling interacts poorly with full-page caching unless planned.
- CSP reports can be noisy because browser extensions, injected enterprise
  tools, old clients, and crawlers can trigger reports unrelated to app defects.
- Third-party widgets can force exceptions that weaken the whole page.
- Developers must learn browser-specific behavior and console diagnostics.
- Long policies can hit proxy, CDN, or server header limits.
- Per-route exceptions can become a shadow security model if not reviewed.

## 11. Failure modes and misuse

Engineering judgement. The symptoms below are the ones operators and developers
usually see before they understand the policy mistake.

| Symptom | Cause | Fix |
|---|---|---|
| Users see a blank page after rollout, and console shows blocked script loads. | Enforcement was enabled before report-only findings were triaged. | Return to report-only, identify the blocked script path, then add a nonce, hash, or narrow directive after review. |
| Inline boot code works locally but fails behind CDN. | The HTML nonce and CSP header nonce are generated by different layers, or cached separately. | Generate the nonce in one layer, pass it to both header and template, and disable full-page cache for nonce-bearing HTML unless the edge rewrites both. |
| Reports spike with `blocked-uri` values from browser extensions. | Extensions injected scripts into the page. The reports describe the user's browser, not a server asset. | Tag known extension patterns, sample them, and keep alerting focused on first-party routes and unknown sources. |
| A reflected XSS still executes even though `script-src` lists trusted domains. | The trusted domain has a JSONP endpoint, script gadget, or user-controlled upload path. | Move script trust to nonces or hashes. Treat host allowlists as a weaker legacy mode. |
| A marketing tag addition requires `unsafe-inline` or `unsafe-eval`. | The vendor library depends on dynamic code execution or inline handlers. | Isolate the tag on a lower-risk page, ask for a CSP-compatible version, or reject the tag for sensitive routes. |
| Clickjacking tests pass on one route and fail on another. | `frame-ancestors` was set in app code on some responses but not on error pages, redirects, or server-rendered fallbacks. | Apply embedding directives through shared middleware or edge rules for every HTML response in scope. |
| Report-only stays noisy for months and no policy is enforced. | No owner has authority to close findings and promote directives. | Assign an owner, define a retirement threshold, and remove the report-only header if nobody will act on it. |
| A hash policy breaks after formatting or minification changes. | Hashes are byte-specific and the build step did not update them. | Compute hashes during the same build that emits HTML, or move boot code into external files with Subresource Integrity where appropriate. |
| A policy with `default-src 'none'` still allows data exfiltration through images. | A later `img-src *` directive relaxes the fallback for image loads. | Review the least restrictive directive per exfiltration path. Tighten `img-src`, `connect-src`, `form-action`, and navigation controls. |
| Trusted Types enforcement breaks client rendering. | Existing code passes strings to DOM injection sinks such as `innerHTML`. | Start in report-only, create narrow policies for reviewed sanitizers, then convert sink calls in small batches. |

Common misuse is treating CSP as a scanner score. A header exists, the grade
improves, and the team stops. The useful question is not whether a header is
present. The useful question is which attacker-controlled bytes can still cause
the browser to execute script or exfiltrate data.

Another misuse is hiding policy decisions inside a catch-all exception. A route
breaks, someone adds a broad source to `script-src` or `connect-src`, and the
incident ends. Later that source becomes the path through which sensitive data
leaves the page. The observable symptom is a policy that keeps getting longer
while the report count stays flat. The fix is to tie every exception to an
owner, a route, and a review date. If the source is required by only one route,
it should not appear in the whole-site baseline.

Nonce misuse has its own pattern. A helper scans rendered HTML and adds the
current nonce to every script tag. That makes legacy code appear to work, but it
also grants trust to injected script tags that survive into the rendered output.
The symptom is a policy that blocks hand-written test payloads but fails against
payloads inserted before the helper runs. The fix is to attach nonces only at
trusted template call sites and to make untrusted markup pass through a
sanitizer that removes script-capable nodes and attributes.

## 12. Trade-off matrix

| Force | Content Security Policy | Output Encoding | Trusted Types | iframe Sandbox | Subresource Integrity |
|---|---|---|---|---|---|
| Primary boundary | Browser action policy | Parser context | DOM injection sinks | Embedded document capability | External resource bytes |
| XSS mitigation | Strong as defense in depth when strict | Strong at the injection source | Strong for DOM XSS sinks | Strong for isolated untrusted UI | Narrow, protects fetched asset integrity |
| Latency | Local browser checks, report traffic possible | No browser policy cost | Local browser checks | Extra frame and messaging cost | Hash verification on load |
| Coupling | Header, templates, build, and routes | Data and rendering context | Client code and sanitizer policies | Host and framed app contract | Build and external asset bytes |
| Operability | Needs reports, sampling, rollout | Needs tests and review | Needs sink inventory | Needs frame debugging | Needs asset hash update path |
| Team fit | Platform-owned defaults with route owners | Every feature team | Frontend platform team | Platform or extension team | Build or supply chain team |
| Failure shape | Broken loads, noisy reports | XSS if missed | Runtime TypeError or violation | Broken embedding or messaging | Asset blocked after change |
| Best use | Limit browser power after injection | Prevent injection from becoming code | Stop unsafe DOM string writes | Run untrusted UI apart from host | Pin third-party script bytes |
| Weak use | Broad host allowlist with inline script | Encoding without context awareness | Tiny app with no DOM sink use | Same-origin trusted content | First-party bundles changing often |

CSP composes with every alternative in this table. It replaces none of them.
Output encoding prevents the injected script element. CSP tells the browser what
to do if the element still appears. Trusted Types makes client code use typed
values at risky sinks. iframe sandboxing isolates content into a different
execution context. SRI checks whether a fetched external asset matches expected
bytes.

## 13. Related and incompatible patterns

**Defense in Depth.** CSP is a direct instance of Defense in Depth. The control
assumes some earlier layer can fail, then limits browser behavior after that
failure. The W3C draft uses that framing explicitly
([https://www.w3.org/TR/CSP/](https://www.w3.org/TR/CSP/), verified
2026-08-02).

**Least Privilege.** A good policy gives the document fewer browser powers than
the browser would grant by default. `default-src 'none'` plus narrow directives
is the least privilege expression. A policy with `*` and `unsafe-inline` fights
the pattern.

**Complete Mediation.** The browser policy engine mediates covered loads and
inline execution attempts. It is not complete for all security decisions in the
application, so authorization must stay server-side.

**Secure by Default.** Framework-level CSP defaults move new routes toward a
safe baseline. GitLab's Omnibus documentation says secure default values are
used for directives that are not explicitly configured in its CSP settings
([https://github.com/gitlabhq/omnibus-gitlab/blob/master/doc/settings/configuration.md](https://github.com/gitlabhq/omnibus-gitlab/blob/master/doc/settings/configuration.md),
verified 2026-08-02).

**CSRF Token.** CSP does not stop cross-site form submission to a state-changing
endpoint. `form-action` can restrict where the current page submits forms, but
CSRF tokens still protect server decisions.

**Session Management.** CSP can reduce session theft through injected script,
but it does not set cookie flags, rotate sessions, or authorize requests.

**Incompatible with inline-script-by-default.** A page architecture that treats
inline handlers, string timers, `eval`, and ad hoc script blocks as normal will
fight CSP every day. The conflict is architectural, not syntactic.

**Incompatible with wildcard asset policy.** A policy whose default answer is
`*` does not express least privilege. It may still block inline script in some
cases, but it is a weak variant.

**Incompatible with client-side template injection.** Old template engines that
evaluate attacker-controlled template expressions can bypass naive CSP designs.
web.dev documents old AngularJS template injection as a case where strict CSP
may not protect the app as well
([https://web.dev/articles/strict-csp](https://web.dev/articles/strict-csp),
verified 2026-08-02).

## 14. Refactoring path in and out

Engineering judgement. The safe path is observability first, narrow enforcement
second, then stricter script trust. Avoid a one-shot migration.

Refactoring in.

1. Inventory HTML response paths, including error pages, login flows, embedded
   surfaces, admin pages, static pages, and worker scripts.
2. Add a report collector with sampling, redaction, and route tags. Do this
   before sending reports from real users.
3. Start with `Content-Security-Policy-Report-Only` on a low-risk route group.
   Include `default-src 'none'` in the candidate when the route can tolerate
   explicit directives, so missing fetch types are visible.
4. Add stable non-script directives first: `base-uri`, `object-src`,
   `frame-ancestors`, `form-action`, `img-src`, `font-src`, `connect-src`,
   `style-src`, `worker-src`, and `manifest-src` as appropriate.
5. Remove inline event handlers and string evaluation. Cross reference the
   refactoring family for Extract Function and Replace Inline Code with Named
   Function where a script block can move to a module.
6. Pick nonce or hash script trust. Use nonce for server-rendered HTML. Use hash
   for static HTML with stable inline code.
7. Route the nonce through a single request object or rendering context. Do not
   generate it independently in templates.
8. Promote one route group from report-only to enforcement after reports are
   understood and tests cover the core rendering path.
9. Expand to more route groups. Keep route-specific exceptions close to route
   ownership and review them on a schedule.
10. Add Trusted Types in report-only for client-heavy pages, then enforce after
   sinks are converted.

Refactoring out.

1. Confirm the reason. Valid reasons include a page moving out of browser
   rendering, replacement by a sandboxed cross-origin surface, or retirement of
   the route.
2. Remove route-specific exceptions first. If no one notices, the broad policy
   is likely carrying the value.
3. Keep `frame-ancestors`, `base-uri`, and `object-src 'none'` unless the route
   is gone. They are low-maintenance controls.
4. Remove report-only policies that nobody reads. Unowned telemetry is noise.
5. If removing a nonce system, remove both header generation and template
   attributes in the same change. Half-removal creates confusing failures.
6. Keep tests that assert dangerous inline script is absent, because that
   invariant is valuable with or without CSP.

Migration order matters because each directive has a different blast radius.
`object-src 'none'` and `base-uri 'none'` are usually cheap first moves.
`frame-ancestors` can be cheap for standalone pages and risky for products that
are legitimately embedded. `connect-src` affects telemetry, API calls, feature
flags, error tracking, and WebSocket endpoints. `script-src` carries the largest
breakage risk because it changes code execution. Engineering judgement. Teams
often get better results by enforcing the low-variance directives early, then
using report-only and route-by-route cleanup for scripts.

Vendor cleanup should be explicit work, not background hope. Create an inventory
with vendor name, route, data sent, directive needed, owner, and removal date.
For each vendor, ask whether it needs script execution on sensitive pages, if it
can run after user consent, if it supports nonce-bearing tags, and if a
server-side event can replace browser script. The result is often a smaller
policy and less user data exposed to third parties.

## 15. Testing and verification

Engineering judgement. CSP tests should cover policy construction, response
attachment, browser behavior, and report handling. String snapshot tests alone
are too brittle and too shallow.

Unit tests belong around the policy builder. Given route metadata and a nonce,
the builder should produce sorted, deterministic directives without duplicate
directive names. Test that `default-src 'none'`, `base-uri`, and `object-src`
are present in baseline policies. Test that route exceptions add narrow sources
without weakening unrelated directives.

Integration tests should fetch real routes and inspect headers. Check that the
enforced header appears on HTML, error pages, and auth redirects. Check that
`Content-Security-Policy-Report-Only` appears only where expected. Check that
worker scripts receive their own policy when needed, because MDN documents that
workers generally are not governed by the creating document's policy unless the
worker script has its own header or a special inherited-origin case applies
([https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy),
verified 2026-08-02).

Browser tests should prove behavior, not only headers. Load a fixture page with
an allowed nonce script and a missing-nonce script. Assert that the allowed
script sets a marker and the blocked script does not. Test `frame-ancestors` by
attempting to embed a protected page from an untrusted origin in a headless
browser. Test `form-action` with a form whose action points to an untrusted
origin.

Report collector tests should submit representative JSON reports, extension-like
noise, malformed reports, and oversized bodies. Assert redaction, rate limiting,
deduplication, and routing. Reports are externally supplied data and must be
parsed as hostile input.

Release verification should include a report-only window, browser console review
on top routes, synthetic checks from supported browsers, and a rollback path
that returns enforcement to report-only without redeploying templates.

Negative tests are important. A passing page load proves compatibility, not
protection. Add a fixture that tries an inline event handler, a `javascript:`
URL, a script tag without a nonce, an unexpected `fetch` destination, and an
untrusted frame. The expected result is not a user-facing crash. The expected
result is that the action does not run, the browser records a violation where
configured, and the page keeps its intended function. Those tests make the
policy part of product behavior rather than an inert header.

Review tests should also check deletion. When a route no longer needs a vendor,
the matching directive should disappear. Without deletion tests, CSP only grows.
A simple approach is a fixture route with known dependencies and an assertion
that its policy equals the generator output for that route. For broad products,
store a policy snapshot per route group and require review when a diff broadens
script, connection, form, or frame destinations.

## 16. Observability signals

Engineering judgement. Healthy CSP observability shows a small number of known
blocked events with owners, not a huge feed of raw browser posts.

Log these fields after redaction: route group, effective directive, blocked URI
category, source file origin, line and column if present, disposition, user
agent family, policy version, release version, and sample hash. Avoid logging
full URLs when they may contain user data. The Level 3 draft calls out
violation reports in security and privacy considerations
([https://www.w3.org/TR/CSP/](https://www.w3.org/TR/CSP/), verified
2026-08-02).

Healthy dashboards show low violation rates on enforced routes, declining
report-only findings during migration, no unknown first-party script blocks,
and a stable top list of known browser extension noise. Policy version labels
make releases visible. A route promoted to enforcement should show user-visible
error metrics staying flat.

Failing dashboards show sudden spikes in `script-src` blocks after a deploy,
blocked first-party asset URLs, repeated `connect-src` blocks to a new API
origin, or `frame-ancestors` violations from a legitimate embedding surface.
Another bad sign is report-only volume that never declines. That means CSP is
being used as a mailbox, not as a control.

Alerts should be selective. Page breakage from first-party blocked scripts is
page severity. A new blocked third-party script on a sensitive route is security
triage. Random extension injection from one user is usually not alert-worthy.
Sampling must be explicit, because high-volume reports can create storage cost
and hide useful findings.

A useful dashboard separates enforced and report-only disposition. Enforced
violations tell you what the browser stopped. Report-only violations tell you
what would break if the candidate moved to enforcement. Mixing them hides the
meaning of the signal. Another useful split is first-party, approved third
party, unknown third party, extension-like, and malformed. Each bucket has a
different owner. First-party blocks go to the feature team. Approved third-party
blocks go to the vendor owner. Unknown third-party blocks go to security triage.
Malformed reports go to collector hardening.

## 17. Security and privacy implications

Engineering judgement. CSP closes some browser execution and exfiltration paths,
but it opens an operational surface through policy configuration and report
collection.

Security benefits. A strict script policy can stop many injected scripts because
the browser refuses inline code without a matching nonce or hash. `object-src
'none'` removes legacy plugin execution. `base-uri` blocks injected base tags.
`frame-ancestors` controls who may embed the page. `form-action` limits form
submission targets. `connect-src` and `img-src` can reduce data exfiltration
paths when kept narrow. CSP Level 3 discusses exfiltration and states that a
policy lacking `default-src` cannot mitigate some request types
([https://www.w3.org/TR/CSP/](https://www.w3.org/TR/CSP/), verified
2026-08-02).

Security limits. CSP does not make unsafe HTML safe. It does not authorize API
calls. It does not protect non-browser clients. It does not hide secrets in
HTML. It does not make a trusted third-party script trustworthy. It does not
fix a vulnerable dependency that already runs with a valid nonce. It does not
protect users on browsers that ignore the relevant directives.

Nonce handling is a sensitive subsystem. Reused nonces, attacker-readable
nonces, cached nonce-bearing HTML, or automatic nonce injection into every
script tag can defeat the model. OWASP warns against middleware that stamps a
nonce onto every script tag because attacker-injected scripts would receive the
nonce too
([https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html),
verified 2026-08-02).

Privacy implications sit mostly in reports. A violation report can contain the
document URL, blocked URL, source location, and sometimes a sample. Those values
can reveal page names, tenant identifiers, query strings, or internal hostnames.
Treat report endpoints as ingesting sensitive telemetry. Apply authentication
or abuse controls where feasible, drop cookies, redact URLs, rate-limit clients,
and set retention periods.

CSP also changes incident response. A blocked script report can be an early
signal of an attempted exploit, a compromised tag, or a browser extension. The
security team needs a triage path that separates those cases.

Privacy review should include the policy itself. Hostnames in a policy can
reveal vendors, internal service names, tenant routing patterns, or acquisition
history. Public web responses already expose many of those facts, but a central
policy can make them easier to enumerate. Engineering judgement. Public
hostnames are usually acceptable in CSP when they are required for browser
loads, but internal hostnames and tenant identifiers should not appear in a
browser-delivered policy unless the page already exposes them by design.

## Code examples

The examples are deliberately small. They model the pattern mechanics rather
than a production web framework.

TypeScript. Build a nonce-based strict policy and render a matching script tag.

```typescript
type DirectiveMap = Record<string, string[]>;

function serializePolicy(directives: DirectiveMap): string {
  return Object.entries(directives)
    .map(([name, values]) => `${name} ${values.join(" ")}`)
    .join("; ");
}

export function strictNoncePolicy(nonce: string): string {
  return serializePolicy({
    "default-src": ["'none'"],
    "script-src": [`'nonce-${nonce}'`, "'strict-dynamic'"],
    "object-src": ["'none'"],
    "base-uri": ["'none'"],
    "frame-ancestors": ["'none'"],
  });
}

export function renderPage(nonce: string): string {
  return [
    "<!doctype html>",
    "<html><head><title>CSP sample</title></head><body>",
    `<script nonce="${nonce}">globalThis.ready = true;</script>`,
    "</body></html>",
  ].join("");
}

const policy = strictNoncePolicy("abc123");
if (!policy.includes("'nonce-abc123'")) {
  throw new Error("nonce missing from policy");
}
console.log(policy);
```

Python. Accept CSP violation reports as hostile JSON and summarize only the
fields the collector needs.

```python
import json

MAX_BODY = 4096

def summarize_report(body: str) -> dict[str, str]:
    if len(body.encode("utf-8")) > MAX_BODY:
        raise ValueError("report too large")
    parsed = json.loads(body)
    report = parsed.get("csp-report", parsed)
    if not isinstance(report, dict):
        raise ValueError("bad report")
    return {
        "directive": str(report.get("effective-directive", "unknown")),
        "blocked": str(report.get("blocked-uri", "unknown"))[:120],
        "disposition": str(report.get("disposition", "unknown")),
    }

sample = json.dumps({
    "csp-report": {
        "effective-directive": "script-src",
        "blocked-uri": "inline",
        "disposition": "enforce",
    }
})

assert summarize_report(sample)["directive"] == "script-src"
print(summarize_report(sample))
```

Go. Merge a baseline policy with a route-specific `connect-src` without
weakening the baseline directives.

```go
package main

import (
	"fmt"
	"sort"
	"strings"
)

type Policy map[string][]string

func (p Policy) Set(name string, values ...string) {
	p[name] = append([]string{}, values...)
}

func (p Policy) Header() string {
	names := make([]string, 0, len(p))
	for name := range p {
		names = append(names, name)
	}
	sort.Strings(names)
	parts := make([]string, 0, len(names))
	for _, name := range names {
		parts = append(parts, name+" "+strings.Join(p[name], " "))
	}
	return strings.Join(parts, "; ")
}

func baseline() Policy {
	p := Policy{}
	p.Set("base-uri", "'none'")
	p.Set("default-src", "'none'")
	p.Set("frame-ancestors", "'none'")
	p.Set("object-src", "'none'")
	return p
}

func main() {
	p := baseline()
	p.Set("connect-src", "'self'", "https://api.example.com")
	header := p.Header()
	if !strings.Contains(header, "default-src 'none'") {
		panic("baseline was weakened")
	}
	fmt.Println(header)
}
```

Verification performed for these samples on 2026-08-20 with `npx tsc`,
`python3`, and `go run`.

## 18. References

- W3C, *Content Security Policy Level 3*, Working Draft, 13 August 2026,
  sections 1, 2.2, 3, 6, 7, and 8.
  [https://www.w3.org/TR/CSP/](https://www.w3.org/TR/CSP/), verified
  2026-08-02.
- W3C, *Content Security Policy Level 2*, Recommendation, 15 December 2016,
  introduction and policy delivery discussion.
  [https://www.w3.org/TR/CSP2/](https://www.w3.org/TR/CSP2/), verified
  2026-08-02.
- MDN Web Docs, *Content-Security-Policy (CSP) header*.
  [https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy),
  verified 2026-08-02.
- MDN Web Docs, *Content Security Policy (CSP)*.
  [https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP),
  verified 2026-08-02.
- MDN Web Docs, *Content-Security-Policy-Report-Only header*.
  [https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy-Report-Only](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy-Report-Only),
  verified 2026-08-02.
- OWASP Cheat Sheet Series, *Content Security Policy Cheat Sheet*.
  [https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html),
  verified 2026-08-02.
- Lukas Weichselbaum, *Mitigate cross-site scripting with a strict Content
  Security Policy*, web.dev.
  [https://web.dev/articles/strict-csp](https://web.dev/articles/strict-csp),
  verified 2026-08-02.
- web.dev, *Security headers quick reference*, Content Security Policy section.
  [https://web.dev/articles/security-headers](https://web.dev/articles/security-headers),
  verified 2026-08-02.
- GitHub Engineering, CSP rollout case study.
  `https://github.blog/engineering/platform-security/githubs-csp-journey/`,
  verified 2026-08-02.
- Shopify Developers, *Set up iframe protection*.
  [https://shopify.dev/docs/apps/build/security/set-up-iframe-protection](https://shopify.dev/docs/apps/build/security/set-up-iframe-protection),
  verified 2026-08-02.
- Shopify Developers, *Following security best practices*.
  [https://shopify.dev/docs/apps/build/security/following-security-best-practices](https://shopify.dev/docs/apps/build/security/following-security-best-practices),
  verified 2026-08-02.
- GitLab Omnibus, *Configuration*, Content Security Policy settings.
  [https://github.com/gitlabhq/omnibus-gitlab/blob/master/doc/settings/configuration.md](https://github.com/gitlabhq/omnibus-gitlab/blob/master/doc/settings/configuration.md),
  verified 2026-08-02.
- W3C, *Trusted Types*, Working Draft, CSP integration sections.
  [https://www.w3.org/TR/trusted-types/](https://www.w3.org/TR/trusted-types/),
  verified 2026-08-02.
- ACM CCS 2016, *Accepted papers*, listing "CSP is Dead, Long Live CSP: On the
  Insecurity of Whitelists and the Future of the Content Security Policy".
  [https://www.sigsac.org/ccs/CCS2016/accepted-papers/index.html](https://www.sigsac.org/ccs/CCS2016/accepted-papers/index.html),
  verified 2026-08-02.
