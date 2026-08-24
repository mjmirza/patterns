---
name: CSRF Token
slug: csrf-token
family: 15-security
category: Security
aliases: [Anti-CSRF Token, XSRF Token, Request Verification Token, Authenticity Token, Synchronizer Token]
first_described: "OWASP community guidance, early 2000s"
maturity: established
related: [session-management, complete-mediation, secure-by-default, defense-in-depth, fail-securely, token-based-authentication]
incompatible_with: [bearer-only-browser-session, state-changing-get, wildcard-credentialed-cors]
verified: 2026-08-02
---

# CSRF Token

## 1. Name, aliases, and lineage

The canonical name in this entry is **CSRF Token**. The token is a secret,
unpredictable request value that a browser must echo with a state-changing
request, while an attacker site cannot read or predict that value. OWASP's
Cross-Site Request Forgery Prevention Cheat Sheet names the synchronizer token
pattern and says stateful software should use it, while stateless software can
use double-submit cookies
([https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
verified 2026-08-02).

Common aliases vary by framework. Rails calls the form value an
`authenticity_token` and emits related `csrf` meta tags
([https://guides.rubyonrails.org/security.html](https://guides.rubyonrails.org/security.html),
verified 2026-08-02). Django documents the `{% csrf_token %}` template tag,
the `csrftoken` cookie, and the `X-CSRFToken` request header
([https://docs.djangoproject.com/en/stable/howto/csrf/](https://docs.djangoproject.com/en/stable/howto/csrf/),
verified 2026-08-02). Laravel uses a hidden `_token` input, the `X-CSRF-TOKEN`
header, and an `XSRF-TOKEN` cookie for JavaScript clients
([https://laravel.com/docs/12.x/csrf](https://laravel.com/docs/12.x/csrf),
verified 2026-08-02). Spring Security names `CsrfToken`, `CsrfFilter`, and
`CsrfTokenRepository`
([https://docs.spring.io/spring-security/reference/7.0/servlet/exploits/csrf.html](https://docs.spring.io/spring-security/reference/7.0/servlet/exploits/csrf.html),
verified 2026-08-02).

The attack name is Cross-Site Request Forgery, abbreviated CSRF or XSRF.
OWASP's community page records other names, including session riding, hostile
linking, and one-click attack
([https://owasp.org/www-community/attacks/csrf](https://owasp.org/www-community/attacks/csrf),
verified 2026-08-02). The lineage is the confused deputy problem adapted to web
browsers. A browser is the deputy. It holds ambient credentials, such as cookies
or HTTP authentication data, and can be induced by another site to send a
credentialed request to the target origin. OWASP describes the attack as making
the target system perform attacker-chosen actions through the victim's browser
while the victim is authenticated
([https://owasp.org/www-community/attacks/csrf](https://owasp.org/www-community/attacks/csrf),
verified 2026-08-02).

This entry treats CSRF Token as a security pattern, not as a general token
format. It is not JWT, not an access token, not a session id, and not a
capability URL. The value has one job. It proves that the request came through
an application-controlled rendering or JavaScript path that was able to obtain
the per-session or per-request secret.

## 2. Problem and context

A web application uses browser-sent ambient credentials for authentication.
Cookies are the common case. RFC 6265 defines cookies as state stored by a user
agent and returned later in the `Cookie` header to servers under the cookie's
scope
([https://www.rfc-editor.org/info/rfc6265/](https://www.rfc-editor.org/info/rfc6265/),
verified 2026-08-02). Because the browser attaches eligible cookies to a
request without asking page JavaScript for permission, a hostile page can submit
a form, load an image, set `window.location`, or trigger other browser
navigation behavior toward the target site. If the target accepts that request
as an intentional user action, the attacker has borrowed the victim's browser
and session.

The problem appears in ordinary product code. A user is signed in to
`bank.example`. In another tab, the user visits `evil.example`. The hostile page
posts a form to `https://bank.example/transfer` with an attacker-controlled
recipient and amount. If the browser sends the bank session cookie and the bank
checks only the cookie, the bank sees an authenticated request but lacks a
signal that the request was initiated by the bank's own page. OWASP describes
CSRF as targeting state-changing functions such as changing an email address,
changing a password, purchasing, or transferring funds
([https://owasp.org/www-community/attacks/csrf](https://owasp.org/www-community/attacks/csrf),
verified 2026-08-02).

The context is narrower than "all HTTP APIs." CSRF Token is for browser clients
where authentication rides on cookies or other credentials the browser sends
with little application participation. It is most natural for server-rendered
forms and browser JavaScript that uses cookies for session continuity. It is
not the main defense for bearer tokens stored outside cookies and attached by
explicit application code, because a cross-site form cannot attach an
`Authorization` header of its own.

HTTP method semantics matter. RFC 9110 defines GET, HEAD, OPTIONS, and TRACE as
safe methods, and states that if a resource uses URI parameters to select an
unsafe action, the owner must disable that action when accessed with a safe
method
([https://www.ietf.org/ietf-ftp/rfc/rfc9110.html](https://www.ietf.org/ietf-ftp/rfc/rfc9110.html),
verified 2026-08-02). CSRF Token does not repair a design where GET performs a
money transfer. It can reject unsafe requests, but the first repair is to stop
using safe methods for state change.

## 3. Forces

Engineering judgement. CSRF Token trades server checks and client plumbing for
clearer intent on state-changing browser requests.

- **Latency.** Mildly sacrificed. A synchronizer token lookup normally reads
  session state and compares one value. That is cheap, but it is still work on
  every protected unsafe request.
- **Coupling.** Mixed. The server, templates, JavaScript clients, caches, and
  test helpers must agree on token names and transport. The security check
  reduces coupling to weaker signals such as `Referer` alone.
- **Consistency.** Favoured when the token is bound to the login session. A
  request presented under one session cannot reuse a token minted for another
  session.
- **Operability.** Sacrificed unless planned. Token failures can come from real
  attacks, stale forms, missing meta tags, bad cache keys, domain mistakes, or
  front-end routes that forgot to attach the header.
- **Cost.** Favoured against incident cost. The direct compute and storage cost
  is small for stateful web sessions. The larger cost is integration across
  pages, clients, tests, and API gateways.
- **Team topology.** Favoured when one platform layer owns middleware and helper
  tags. Sacrificed when each feature team invents token fields, exemption rules,
  or CORS exceptions.
- **Cognitive load.** Sacrificed. Developers must know which routes mutate
  state, where tokens are emitted, how JavaScript attaches them, and why token
  cookies differ from session cookies.
- **Privacy.** Favoured if tokens stay out of URLs and logs. OWASP warns that
  CSRF tokens should not be sent in URLs because they can leak through browser
  history, logs, and referrer data
  ([https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
  verified 2026-08-02).
- **User experience.** Mixed. Per-request tokens reduce replay windows, but
  OWASP notes that they can break back-button flows when old pages submit stale
  tokens
  ([https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
  verified 2026-08-02).

The pattern favours explicit request intent and auditability. It sacrifices
some simplicity in clients and route configuration.

## 4. Applicability and non-applicability

Reach for CSRF Token when the following hold.

- The application authenticates browser requests with cookies or another
  credential that the browser sends without per-request JavaScript control.
- A route changes server state with POST, PUT, PATCH, DELETE, or another unsafe
  method.
- Server-rendered pages include forms that submit back to the same site.
- Browser JavaScript calls same-origin APIs using cookie authentication.
- A framework provides built-in CSRF middleware and helper tags. OWASP advises
  checking for framework support before building a custom token mechanism
  ([https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
  verified 2026-08-02).
- The application can store a token in session state, or can bind a stateless
  double-submit token to the session with a server-side MAC.
- The team can log rejects without logging token values.

Do NOT reach for CSRF Token in these cases.

- **The route is a public webhook or third-party callback.** The sender cannot
  know the user's CSRF token. Use sender signatures, mTLS, replay windows, and
  a separate endpoint outside the browser session surface.
- **The API uses bearer tokens in `Authorization` headers and never accepts
  cookie credentials.** A hostile HTML form cannot set that header. Use CORS
  allow-lists, token audience checks, and storage rules for bearer tokens.
- **The route changes state through GET.** First move the action to an unsafe
  method. RFC 9110 assigns safety meaning to GET, and CSRF Token is not a
  license to keep unsafe GET endpoints
  ([https://www.ietf.org/ietf-ftp/rfc/rfc9110.html](https://www.ietf.org/ietf-ftp/rfc/rfc9110.html),
  verified 2026-08-02).
- **The application has active XSS in the same origin.** OWASP warns that XSS
  can defeat CSRF mitigations because same-origin script can read or submit the
  token
  ([https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
  verified 2026-08-02). Fix script injection and apply content security policy
  as a separate control.
- **The client is a native mobile app or CLI using explicit credentials.** CSRF
  is a browser ambient credential issue. A CSRF token may become fake security
  theatre for non-browser clients.
- **Cross-site credentialed CORS is open to broad origins.** If any attacker
  origin can send credentialed requests with custom headers, a header token
  loses its same-origin value. OWASP warns against broad subdomain CORS rules
  for credentialed CSRF-protected APIs
  ([https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
  verified 2026-08-02).
- **The operation already requires fresh user interaction, such as WebAuthn,
  reauthentication, or a transaction confirmation code.** Keep the stronger
  ceremony. A CSRF token can remain as a baseline guard, but it is not the main
  authorization proof.
- **The token would be exposed in URLs, analytics, or third-party form targets.**
  Django warns not to place its CSRF token in POST forms targeting external
  URLs because that leaks the token
  ([https://docs.djangoproject.com/en/stable/howto/csrf/](https://docs.djangoproject.com/en/stable/howto/csrf/),
  verified 2026-08-02).

## 5. Structure

The participants are security roles rather than classes.

- **Browser session.** Holds the authenticated cookie and receives pages or
  scripts from the protected origin.
- **Token issuer.** Creates a cryptographically random token. In the stateful
  variant it stores that token, or a derived value, in the server-side session.
  In the signed double-submit variant it creates a MAC over session-bound data.
- **Token carrier.** Places the token where same-origin code or markup can send
  it back. Common carriers are hidden form fields, HTML meta tags, JSON
  bootstrap data, or a JavaScript-readable CSRF cookie.
- **Protected request.** Carries the token back in a form field, request header,
  or JSON body. OWASP describes hidden fields and custom headers as common
  transports
  ([https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
  verified 2026-08-02).
- **CSRF verifier.** Runs before the state-changing handler. It checks method,
  route exemption, session binding, token presence, token equality or MAC, and
  origin defense rules, then either passes the request or returns a rejection.
- **Mutation handler.** Performs the business action only after the verifier
  passes.
- **Failure recorder.** Logs reason codes and request context without token
  values. Django logs CSRF failures to `django.security.csrf`
  ([https://docs.djangoproject.com/en/stable/howto/csrf/](https://docs.djangoproject.com/en/stable/howto/csrf/),
  verified 2026-08-02).
- **Defense-in-depth signals.** SameSite cookies, Origin or Referer checks,
  Fetch Metadata, and user interaction checks can narrow the attack surface.
  MDN documents SameSite cookie modes and says the attribute controls whether
  cookies are sent with cross-site requests
  ([https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie),
  verified 2026-08-02).

The core relationship is simple. The protected origin gives the browser a value
the attacker origin cannot read. The browser returns that value through a path
that an attacker origin cannot synthesize. The server rejects when the value is
absent, wrong, stale, or bound to another session.

The session binding is the part many weak designs miss. A random value by
itself says only that somebody produced a random-looking value. The verifier
needs to know that the value belongs to the current authenticated browser
session. In a synchronizer design, that relationship is stored server side. In
a signed double-submit design, the relationship is encoded by a MAC over
session-specific material. If the verifier compares only a cookie value with a
form value, then any path that lets an attacker set both values can collapse the
defense. OWASP warns against the naive double-submit cookie pattern for this
reason
([https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
verified 2026-08-02).

Cookie scope is also structural. MDN documents that a cookie with a `Domain`
attribute is sent to that domain and its subdomains, while omitting `Domain`
creates a host-only cookie
([https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie),
verified 2026-08-02). Engineering judgement. Host-only scope is the safer
default for CSRF helper cookies, because sibling subdomains are often owned by
different teams, vendors, preview systems, or retired products. If a parent
domain cookie is required, treat every subdomain that can set cookies as part
of the security boundary.

## 6. ASCII structure diagram

```text
  +------------------+        renders token        +------------------+
  | Protected Origin | --------------------------> | Browser Session  |
  |------------------|                             |------------------|
  | Token Issuer     |                             | Session cookie   |
  | Session Store    |                             | HTML or JS state |
  | CSRF Verifier    |                             +---------+--------+
  +---------+--------+                                       |
            ^                                                |
            | validated token                                |
            |                                                |
  +---------+--------+         unsafe request        +--------v---------+
  | Mutation Handler | <---------------------------- | Token Carrier    |
  |------------------|  form field or request header |------------------|
  | account change   |                               | hidden input     |
  | transfer action  |                               | X-CSRF header    |
  +------------------+                               +------------------+

  +------------------+
  | Attacker Origin  |
  |------------------|
  | can submit form  |
  | cannot read token|
  +------------------+
```

## 7. Dynamics

Runtime behavior is a gate in front of every unsafe browser request. The gate
must fail closed for missing tokens. PortSwigger lists common bypass classes,
including validation that only runs for one method, validation that passes when
the token is absent, and tokens not tied to the user session
([https://portswigger.net/web-security/csrf/bypassing-token-validation](https://portswigger.net/web-security/csrf/bypassing-token-validation),
verified 2026-08-02).

```text
User Browser       Protected Origin       Session Store       Handler
     |                    |                    |                |
     |-- GET /form ------>|                    |                |
     |                    |-- load token ----->|                |
     |                    |<-- token ----------|                |
     |<-- form + token ---|                    |                |
     |                    |                    |                |
     |-- POST token ----->|                    |                |
     |                    |-- expected token ->|                |
     |                    |<-- expected -------|                |
     |                    | compare constant time               |
     |                    | origin and method checks            |
     |                    |------------------------------ POST ->|
     |<-- 200 or redirect-|                    |<-------- result-|

Attacker Origin    User Browser           Protected Origin
     |                    |                    |
     |-- hidden form ---->|                    |
     |                    |-- POST no token -->|
     |                    |<-- 403 ------------|
```

The exact point of token creation varies. A server-rendered application often
creates a token when rendering the first form. Django notes that the CSRF cookie
may not be set when a view does not render a template containing the token tag,
and provides `ensure_csrf_cookie()` for that case
([https://docs.djangoproject.com/en/stable/howto/csrf/](https://docs.djangoproject.com/en/stable/howto/csrf/),
verified 2026-08-02). A JavaScript application may fetch bootstrap data, read a
same-origin cookie, or read a meta tag and attach a header to unsafe calls.
Rails documents meta tags created by `csrf_meta_tags`, and Turbo reads them for
the `X-CSRF-Token` header
([https://guides.rubyonrails.org/security.html](https://guides.rubyonrails.org/security.html),
verified 2026-08-02).

The rejection path is part of the design. A missing token should not fall
through to a handler. A malformed token should not trigger token regeneration
and retry. A mismatch should return a denial, clear enough for debugging, but
not so detailed that it helps attackers tune requests.

A deployed verifier usually performs checks in a stable order. It first decides
whether the route and method require CSRF protection. It then confirms that an
authenticated session exists when the endpoint is session-backed. It evaluates
coarse request context, such as Origin, Referer, SameSite expectations, or Fetch
Metadata. It resolves the submitted token from the configured carriers. It
loads or derives the expected value. It compares without early exit. It then
passes a typed principal and request to the handler, or returns a denial with a
reason code. Spring Security's reference breaks its `CsrfFilter` processing
into comparable steps, including deciding whether protection is required,
loading the persisted token, resolving the client token, comparing values, and
passing denial to an access denied handler
([https://docs.spring.io/spring-security/reference/7.0/servlet/exploits/csrf.html](https://docs.spring.io/spring-security/reference/7.0/servlet/exploits/csrf.html),
verified 2026-08-02).

Token refresh timing is a product decision as much as a security decision.
Rotating on login, logout, and session regeneration is ordinary. Rotating after
every successful unsafe request is much harder for multi-tab applications,
long-lived forms, autosave editors, and mobile browsers that suspend tabs.
Engineering judgement. A strong default is one token per login session, masked
or rewrapped per response when the framework supports that, plus separate
step-up confirmation for the small set of actions where replay within the
session would still be unacceptable.

## 8. Implementation variants

**Synchronizer token.** The server stores a token in the authenticated session
and emits the same value, or a masked representation of it, to the browser. On
unsafe requests the verifier compares the submitted value with the session
value. OWASP names this as the preferred stateful approach
([https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
verified 2026-08-02). Engineering judgement. This is the default for
server-rendered applications with existing session storage because the binding
to the login session is direct.

**Per-session token.** One token lasts for the authenticated session. It is
simple, has few stale-form problems, and is enough when XSS is out of scope for
this control. The cost is that a leaked token remains useful until rotation or
logout.

**Per-request token.** A new token is minted for each rendered form or unsafe
request step. OWASP says per-request tokens reduce the attack time window but
can create back-button usability issues
([https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
verified 2026-08-02). Engineering judgement. Use this only for high-risk
workflows where stale-form handling has been designed.

**Masked token.** The browser receives a value derived from the canonical token
and a mask, rather than the canonical secret by itself. Django documents that
the DOM token is masked and recommends the masked form for BREACH resistance
([https://docs.djangoproject.com/en/stable/howto/csrf/](https://docs.djangoproject.com/en/stable/howto/csrf/),
verified 2026-08-02). The verifier accepts the unmasked or masked form,
depending on framework rules.

**Signed double-submit cookie.** The server sends a CSRF cookie and the client
copies the value into a header or form field. The server verifies that the
submitted value matches and that a MAC binds it to session-specific data. OWASP
recommends the signed, session-bound variant and warns that the naive variant
is vulnerable to cookie injection
([https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
verified 2026-08-02). This variant is useful when server-side CSRF storage is
hard, but it adds key rotation and cookie scope concerns.

**Cookie-to-header for SPA clients.** The server sets a JavaScript-readable
CSRF cookie, and same-origin JavaScript copies it into a custom header. Laravel
documents an `XSRF-TOKEN` cookie used with the `X-XSRF-TOKEN` header, including
automatic support by libraries such as Axios
([https://laravel.com/docs/12.x/csrf](https://laravel.com/docs/12.x/csrf),
verified 2026-08-02). The security property is that an attacker origin can
cause cookies to be sent, but cannot read a same-origin cookie or set a custom
header unless CORS allows it.

**Header-only custom request check.** OWASP describes custom request headers as
a CSRF defense for API-driven sites because custom headers are subject to
same-origin and CORS rules
([https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
verified 2026-08-02). Engineering judgement. Treat header presence alone as a
lighter pattern than CSRF Token. It fits same-origin JSON APIs, but does not
cover classic HTML form posts unless those posts are absent by design.

**SameSite-assisted token.** SameSite reduces how often cookies accompany
cross-site requests. MDN documents `Strict`, `Lax`, and `None`, and states that
`None` also requires `Secure`
([https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie),
verified 2026-08-02). Engineering judgement. Use SameSite as a second line,
not as the sole check for high-risk actions, because site and origin are not the
same boundary.

**Fetch Metadata gate.** Fetch Metadata request headers tell servers about the
request context. The W3C draft defines `Sec-Fetch-Site` values including
`same-origin`, `same-site`, `cross-site`, and `none`
([https://www.w3.org/TR/fetch-metadata/](https://www.w3.org/TR/fetch-metadata/),
verified 2026-08-02). Engineering judgement. Fetch Metadata is useful at a
gateway or middleware layer, but legacy clients and intentional cross-site flows
need explicit policy.

**Origin and Referer verification.** Origin and Referer checks compare request
provenance with the protected origin. They are useful when tokens are absent
from an old client or when a global gateway wants a cheap first pass. They are
not a full replacement for tokens because headers may be absent in privacy
contexts, and because product flows such as redirects, embedded browsers, or
corporate proxies can alter what arrives. OWASP includes origin verification
among defense-in-depth mitigations, while still centering token-based
mitigation for stateful applications
([https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
verified 2026-08-02).

**User interaction token.** High-risk flows can bind the token check to a fresh
interaction, such as a password prompt, WebAuthn assertion, signed transaction
summary, or one-time confirmation code. This is not a replacement for the
normal CSRF gate. It is an extra proof that the user saw and accepted the
specific action. Engineering judgement. Use it for money movement, credential
changes, role grants, and destructive administration. Do not spread it across
low-risk forms, because users learn to approve prompts without reading them.

## 9. Known production uses

**Django.** Django's CSRF middleware is active by default in the `MIDDLEWARE`
setting, and the documentation instructs templates with internal POST forms to
use the `{% csrf_token %}` tag
([https://docs.djangoproject.com/en/stable/howto/csrf/](https://docs.djangoproject.com/en/stable/howto/csrf/),
verified 2026-08-02). Django also documents AJAX use through the `X-CSRFToken`
header and offers a test client option that enforces CSRF checks.

**Ruby on Rails.** Rails documents required security tokens for forged-request
protection, `protect_from_forgery with: :exception`, security tokens in Rails
forms, and `csrf_meta_tags` for JavaScript clients
([https://guides.rubyonrails.org/security.html](https://guides.rubyonrails.org/security.html),
verified 2026-08-02). The Rails name `authenticity_token` is one of the most
widely recognized aliases in web application code.

**Spring Security.** Spring Security documents `CsrfFilter` as the component
that makes a `CsrfToken` available, checks whether a request requires
protection, loads the token, compares the submitted token, and handles denial
when the token is invalid or missing
([https://docs.spring.io/spring-security/reference/7.0/servlet/exploits/csrf.html](https://docs.spring.io/spring-security/reference/7.0/servlet/exploits/csrf.html),
verified 2026-08-02). Its API documentation says `CsrfFilter` applies CSRF
protection using the synchronizer token pattern
([https://docs.spring.io/spring-security/reference/api/java/org/springframework/security/web/csrf/CsrfFilter.html](https://docs.spring.io/spring-security/reference/api/java/org/springframework/security/web/csrf/CsrfFilter.html),
verified 2026-08-02).

**Laravel.** Laravel documents automatic CSRF token generation for each active
user session, validation by `ValidateCsrfToken` middleware in the `web`
middleware group, hidden `_token` form fields, and headers for JavaScript
clients
([https://laravel.com/docs/12.x/csrf](https://laravel.com/docs/12.x/csrf),
verified 2026-08-02). It also documents URI exclusions for cases such as Stripe
webhooks, which is a production example of route scoping.

## 10. Consequences

Engineering judgement. The value of the pattern is not the token string. The
value is a clear server-side proof that an unsafe browser request passed
through application-controlled code.

Positive consequences.

- Unsafe browser requests gain an intent check separate from ambient cookies.
- Framework middleware can apply one policy across many handlers.
- Hidden form fields and headers make missing protection visible in tests.
- Per-session binding makes token replay across accounts fail.
- Token failure logs can reveal stale clients, broken caches, cross-site probes,
  and CORS mistakes.
- SameSite, Origin checks, and Fetch Metadata compose well with the token gate.
- High-risk handlers can add user interaction without changing the baseline
  guard.

Negative consequences.

- Pages and JavaScript clients need token plumbing.
- Caches must vary on cookies or avoid caching token-bearing responses across
  users. Django documents `Vary: Cookie` behavior when a token is used
  ([https://docs.djangoproject.com/en/stable/howto/csrf/](https://docs.djangoproject.com/en/stable/howto/csrf/),
  verified 2026-08-02).
- Test clients often bypass CSRF by default, so security tests need a mode that
  turns checks back on.
- Per-request tokens can create stale form failures.
- Token cookies that are JavaScript-readable cannot be `HttpOnly`, so XSS has a
  path to them.
- Exemption lists tend to grow unless ownership is strict.
- A mismatch can look like a login timeout to users unless the product handles
  recovery cleanly.

## 11. Failure modes and misuse

Engineering judgement. These failure modes are written as production symptoms,
causes, and fixes so a team can diagnose the pattern in logs and tests.

| Symptom | Cause | Fix |
|---|---|---|
| Cross-site POST succeeds in a security test with no token field. | Middleware validates only when a token parameter exists. | Reject unsafe requests when the token is absent, malformed, or mismatched. |
| GET link changes account state and works from an email. | Unsafe business action is bound to a safe method. | Move the action to POST, PUT, PATCH, or DELETE, then protect it. |
| Users see 403 after pressing Back and resubmitting. | Per-request tokens expired after navigation history retained an old form. | Use per-session tokens for normal forms, or add one-time token recovery for high-risk flows. |
| Only one front-end route gets 403 in production. | That route's JavaScript client does not attach the CSRF header. | Centralize unsafe request helpers and add integration tests for every mutating endpoint. |
| A cache serves one user's token to another user. | Token-bearing HTML was cached without a cookie-aware key. | Mark pages private, vary on cookie, or inject tokens outside shared cache output. |
| Attack works after a subdomain takeover. | Naive double-submit cookie accepts attacker-planted cookie values. | Use a session-bound MAC and host-only cookie scope, preferably a `__Host-` cookie where suitable. |
| CSRF protection passes from an untrusted origin using AJAX. | Credentialed CORS allow-list is broad or regex-based across subdomains. | Pin exact allowed origins and block credentials for unknown origins. |
| Logs contain token values. | Rejection handler logs request bodies or headers verbatim. | Redact CSRF fields and headers before access logs, traces, and error events. |
| Real customers fail after login in embedded browsers. | SameSite or Fetch Metadata behavior differs from the tested browser set. | Keep token validation as the main gate and add compatibility telemetry before blocking on newer headers. |
| Token validation fails after session rotation. | The client keeps an old token after login, logout, or privilege change. | Rotate token with the session and refresh bootstrapped client state after auth transitions. |

PortSwigger's CSRF material lists bypass classes that match several rows here,
including method-dependent checks, validation that passes when the token is
missing, and tokens not tied to a user session
([https://portswigger.net/web-security/csrf/bypassing-token-validation](https://portswigger.net/web-security/csrf/bypassing-token-validation),
verified 2026-08-02).

## 12. Trade-off matrix

Engineering judgement. Scores are relative for browser applications with
cookie-backed sessions.

| Pattern | Latency | Coupling | Consistency | Operability | User fit | Main cost |
|---|---|---|---|---|---|---|
| CSRF Token, synchronizer | Low extra server work | Medium across server and client | High when session-bound | Good with reason-code logs | Strong for forms and same-origin JS | Token plumbing and cache rules |
| Signed double-submit cookie | Low server work, no CSRF store | Medium plus key management | Medium to high with session MAC | Medium, cookie scope matters | Strong for SPA clients | Cookie injection risk if built poorly |
| SameSite cookie only | No application lookup | Low | Medium, browser-dependent | Medium, hard to explain failures | Good baseline for modern browsers | Same-site gadgets and compatibility |
| Origin or Referer check | Low | Low | Medium | Medium, privacy and proxy gaps | Useful fallback | Missing or altered headers |
| Fetch Metadata gate | Very low at edge | Low to medium | Medium | Good for dashboards | Strong for broad cross-site blocks | Legacy clients and cross-site exceptions |
| Reauthentication or step-up | High user and server cost | Medium | Very high for one action | Good audit value | Strong for high-risk actions | Friction |
| Bearer token outside cookies | Low for CSRF | Medium in client storage | Depends on token policy | Medium | Strong for APIs, weaker for classic forms | XSS and storage theft trade-offs |

CSRF Token is not the only control. It is the most direct control for classic
cookie-authenticated browser mutation. SameSite and Fetch Metadata reduce the
number of hostile requests that reach application code. Step-up checks protect
the most dangerous actions even after a token passes.

## 13. Related and incompatible patterns

**Session Management** composes directly. CSRF tokens are normally bound to a
session id, login epoch, or server-side session record. If the session rotates,
the CSRF token should rotate or be rederived with the new session binding.

**Complete Mediation** supplies the rule that every state-changing request must
pass the verifier. A token on one controller is not enough when a second
controller performs the same mutation without the gate.

**Fail Securely** controls rejection. Missing token, malformed token, absent
session, and mismatched origin should deny by default.

**Defense in Depth** supplies SameSite, Origin checks, Referer checks, Fetch
Metadata, rate limiting, and step-up confirmation around the token.

**Secure by Default** is the framework posture. Django, Rails, Laravel, and
Spring Security all provide framework-level CSRF machinery in their web stacks,
with different defaults and integration points
([https://docs.djangoproject.com/en/stable/howto/csrf/](https://docs.djangoproject.com/en/stable/howto/csrf/),
verified 2026-08-02;
[https://guides.rubyonrails.org/security.html](https://guides.rubyonrails.org/security.html),
verified 2026-08-02;
[https://laravel.com/docs/12.x/csrf](https://laravel.com/docs/12.x/csrf),
verified 2026-08-02;
[https://docs.spring.io/spring-security/reference/7.0/servlet/exploits/csrf.html](https://docs.spring.io/spring-security/reference/7.0/servlet/exploits/csrf.html),
verified 2026-08-02).

**XSS Prevention** is a prerequisite control, not a replacement. OWASP states
that XSS can defeat CSRF mitigation techniques
([https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
verified 2026-08-02).

Incompatible patterns and practices include state-changing GET, bearer-only
browser sessions that are also accepted from cookies, wildcard credentialed
CORS, shared token-bearing HTML caches, and broad CSRF exemption lists. These
do not merely weaken the pattern. They erase the request-intent signal the
pattern is meant to add.

## 14. Refactoring path in and out

Engineering judgement. Introduce the pattern by narrowing the mutation surface
first, then adding the gate. Removing it safely means changing the credential
model, not deleting middleware.

Refactoring in.

1. Inventory every route by method and side effect. Mark account, billing,
   permission, content creation, and administrative routes as unsafe.
2. Move state changes away from GET. Keep redirects and reads on safe methods.
3. Enable the framework CSRF middleware globally for browser routes.
4. Add template helpers for every internal POST form.
5. Add a single JavaScript request helper that reads a meta tag or CSRF cookie
   and attaches the configured header.
6. Bind tokens to the login session. If using double-submit, add a session-bound
   MAC rather than plain equality alone.
7. Add route exemptions only for endpoints that cannot receive a user token,
   such as webhooks. Put those routes outside browser session routing where
   possible.
8. Add security tests that submit unsafe requests with no token, bad token,
   token from another session, and correct token.
9. Add logs and metrics with reason codes, but redact token values.
10. Roll out in report-only mode only if a legacy application has unknown
   clients. Then switch to blocking after false positives are understood.

Large applications need one more path before step 10. Build an exemption
register with owner, reason, expiry date, sender authentication mechanism, and
last traffic date. A route should not be exempt because it was hard to fix in
the first pass. It should be exempt because the protocol cannot carry a user
CSRF token, as with a webhook, an inbound identity provider response, or a
third-party payment callback. Laravel's documentation uses Stripe webhooks as
an example of routes that may need exclusion from CSRF protection
([https://laravel.com/docs/12.x/csrf](https://laravel.com/docs/12.x/csrf),
verified 2026-08-02). Engineering judgement. Every exemption should have a
stronger route-specific authentication story than the token it bypasses.

Refactoring out.

1. Confirm the endpoint no longer accepts browser ambient credentials.
2. Require explicit bearer credentials outside cookies, or require a stronger
   user interaction ceremony for the action.
3. Remove token fields from clients for that endpoint only.
4. Keep SameSite and Origin policy unless there is a protocol reason to alter
   them.
5. Delete the exemption after the old route is gone. Do not leave dead bypass
   patterns in middleware configuration.

The cleanest way out is often a route split. Keep browser pages and
cookie-authenticated form posts in a web route group with CSRF middleware.
Move machine-to-machine callbacks into an API route group that rejects cookies
and uses sender signatures. Move token-authenticated JSON APIs into a group
that requires `Authorization` and denies cookie fallback. Engineering judgement.
Mixing these credential models in one route group causes policy drift because a
future handler can accidentally accept the weaker credential path.

Named refactorings that often apply are Extract Function for duplicated token
attachment code, Move Method when checks sit in controllers instead of
middleware, Replace Conditional with Polymorphism when route policy branches
grow by endpoint family, and Consolidate Duplicate Conditional Fragments when
many handlers perform the same unsafe-method checks.

## 15. Testing and verification

Engineering judgement. CSRF tests should prove both acceptance and denial. A
single happy-path form test proves little.

Unit tests should cover token generation length, randomness source selection,
constant-time comparison wrappers, session binding, MAC verification, parser
failure, and redaction. Property-style tests can generate malformed base64,
empty strings, duplicate token fields, wrong session ids, and old login epochs.

Integration tests should exercise real middleware. Django documents that its
normal test client relaxes CSRF checks, and that `Client(enforce_csrf_checks=True)`
turns checks on
([https://docs.djangoproject.com/en/stable/howto/csrf/](https://docs.djangoproject.com/en/stable/howto/csrf/),
verified 2026-08-02). Laravel documents that CSRF middleware is disabled for
all routes when running tests
([https://laravel.com/docs/12.x/csrf](https://laravel.com/docs/12.x/csrf),
verified 2026-08-02). Those framework choices make ordinary controller tests
faster, but they also mean security coverage must opt into the real gate.

Minimum verification cases.

- Unsafe request with no token returns denial.
- Unsafe request with a random token returns denial.
- Unsafe request with a token from another session returns denial.
- Unsafe request with the correct token and session reaches the handler.
- Safe read route does not require a token and does not mutate state.
- Exempt webhook route rejects unsigned third-party input through its own
  sender-authentication rule.
- Shared cache never serves a token-bearing response across sessions.
- JavaScript helper attaches the header for POST, PUT, PATCH, and DELETE.
- Rejection logs contain reason codes but not token values.
- SameSite and Fetch Metadata policies do not block planned cross-site entry
  flows, such as top-level navigation to public pages.

Manual security testing should include a hostile-origin HTML page that posts a
form to the target. It should fail with a token reason. A second test should
attempt a credentialed CORS request with a custom header from an untrusted
origin. It should fail at CORS or at the CSRF gate.

Test data should cover route shape as well as token value. Many bypasses are
caused by alternate encodings and fallback parsers, not by guessing the token.
Send the token in the wrong field name, send duplicate token fields with one
valid and one invalid value, send JSON with `text/plain`, send `_method=DELETE`
through a POST form when the framework supports method override, and send a
valid token with a session cookie from another login. PortSwigger documents
method-dependent validation and missing-token validation as common CSRF token
bypass classes
([https://portswigger.net/web-security/csrf/bypassing-token-validation](https://portswigger.net/web-security/csrf/bypassing-token-validation),
verified 2026-08-02). Engineering judgement. These tests belong in a security
integration suite that runs against the same middleware stack as production,
not only in isolated controller tests.

Browser compatibility tests should exercise the actual cookie attributes used
by the application. MDN documents that `SameSite=None` requires `Secure`, and
that `Lax` has special behavior for top-level safe navigations
([https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie),
verified 2026-08-02). Test login, form submit, expired session recovery,
multi-tab submit, back-button submit, and embedded webview flows. The goal is
to find usability breakage before users learn to retry dangerous actions.

## 16. Observability signals

Engineering judgement. CSRF observability should separate likely attacks from
integration defects without exposing token material.

Log fields.

- `csrf.decision`, with values such as `pass`, `missing`, `mismatch`,
  `malformed`, `session_absent`, `origin_denied`, `fetch_metadata_denied`, and
  `exempt`.
- `http.method`, route name, status code, and handler family.
- Session presence as a boolean, not a session id.
- Token source, such as form field, header, or none.
- Origin host and Referer host after allow-list normalization.
- `Sec-Fetch-Site`, `Sec-Fetch-Mode`, and `Sec-Fetch-Dest` when present.
- User agent family and client version for first-party applications.

Dashboard signals.

- Reject rate by route and reason.
- Reject rate after deploy by client version.
- Top routes with `missing` tokens.
- Any `pass` event from a route expected to be read-only, which may show a
  misclassified mutation.
- Exemption count and request volume by exempt route.
- Token-bearing page cache hit ratio by cache key type.
- Credentialed CORS failures by origin.

A healthy system has near-zero mismatches on ordinary forms, low missing-token
rates after the first release, and a small, reviewed exemption list. A failing
system shows sharp spikes after front-end deploys, one route dominating misses,
or external origins producing `origin_denied` and `fetch_metadata_denied`
bursts. Those bursts can indicate probing, but they can also be partner
integration drift. Treat reason codes as triage input, not proof by themselves.

## 17. Security and privacy implications

Engineering judgement. CSRF Token closes one attack path created by ambient
browser credentials. It does not authenticate the user, authorize the action,
or sanitize input.

Security benefits.

- A hostile origin cannot normally read a token from the protected origin due to
  the same-origin policy.
- A hostile origin cannot normally add arbitrary custom headers to a
  credentialed browser request unless the target's CORS policy permits it.
- A token bound to the server-side session blocks reuse across accounts.
- SameSite cookies can lower exposure to cross-site requests. MDN says
  `SameSite=Strict` sends cookies only for same-site-originating requests, while
  `Lax` allows selected top-level safe navigations
  ([https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie),
  verified 2026-08-02).

Security limits.

- XSS can read a DOM token or JavaScript-readable CSRF cookie and can send same
  origin requests with the right header.
- Login CSRF and client-side CSRF need specific analysis because the attacker
  may abuse client code or authentication flow behavior rather than a classic
  form post. OWASP discusses client-side CSRF as a variant where attacker input
  causes the victim's JavaScript to send forged requests
  ([https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
  verified 2026-08-02).
- Naive double-submit cookies can be bypassed if an attacker can plant matching
  cookie and request values. OWASP and PortSwigger both describe this class of
  weakness
  ([https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
  verified 2026-08-02;
  [https://portswigger.net/web-security/csrf/bypassing-token-validation](https://portswigger.net/web-security/csrf/bypassing-token-validation),
  verified 2026-08-02).
- SameSite is a site boundary, not an origin boundary. PortSwigger notes that a
  cross-origin request can still be same-site
  ([https://portswigger.net/web-security/csrf/bypassing-samesite-restrictions](https://portswigger.net/web-security/csrf/bypassing-samesite-restrictions),
  verified 2026-08-02).

Privacy rules are concrete. Do not put tokens in URLs. Do not log token values.
Do not send tokens to external form actions. Do not store long-lived CSRF
tokens in analytics-visible page state. Treat CSRF tokens as secrets even when
they are not authorization credentials by themselves, because disclosure removes
the pattern's protection for the bound session.

The `HttpOnly` trade-off deserves explicit handling. A synchronizer token
stored only in server session state can keep the session cookie `HttpOnly`.
A cookie-to-header design uses a JavaScript-readable CSRF cookie so client code
can copy it into a header. That cookie should not contain the session id, user
profile data, or authorization claims. It should contain only a CSRF value or a
wrapped value that is useless outside the session binding. Engineering
judgement. If a front-end framework asks for a readable `XSRF-TOKEN` cookie,
keep the real session cookie separate, `HttpOnly`, `Secure`, and narrowly
scoped.

The pattern is silent on business authorization. A valid CSRF token proves that
the request came through an allowed browser path for this session. It does not
prove that the user may transfer this amount, edit this tenant, grant this
role, or delete this record. Authorization must run after CSRF validation and
must use server-side policy, not form fields. Treating CSRF pass as permission
is a category error.

## 18. References

- OWASP Cheat Sheet Series, "Cross-Site Request Forgery Prevention Cheat
  Sheet." URL:
  [https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
  verified 2026-08-02.
- OWASP Foundation, "Cross Site Request Forgery (CSRF)." URL:
  [https://owasp.org/www-community/attacks/csrf](https://owasp.org/www-community/attacks/csrf),
  verified 2026-08-02.
- OWASP Foundation, "Reviewing Code for Cross-Site Request Forgery Issues."
  URL:
  [https://owasp.org/www-project-code-review-guide/reviewing-code-for-csrf-issues](https://owasp.org/www-project-code-review-guide/reviewing-code-for-csrf-issues),
  verified 2026-08-02.
- Adam Barth, "RFC 6265. HTTP State Management Mechanism." IETF, April 2011.
  URL:
  [https://www.rfc-editor.org/info/rfc6265/](https://www.rfc-editor.org/info/rfc6265/),
  verified 2026-08-02.
- Roy T. Fielding, Mark Nottingham, and Julian Reschke, "RFC 9110. HTTP
  Semantics." IETF, June 2022. URL:
  [https://www.ietf.org/ietf-ftp/rfc/rfc9110.html](https://www.ietf.org/ietf-ftp/rfc/rfc9110.html),
  verified 2026-08-02.
- MDN Web Docs, "Set-Cookie header." URL:
  [https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie),
  verified 2026-08-02.
- W3C Web Application Security Working Group, "Fetch Metadata Request Headers,"
  Working Draft, 1 April 2025. URL:
  [https://www.w3.org/TR/fetch-metadata/](https://www.w3.org/TR/fetch-metadata/),
  verified 2026-08-02.
- Django Software Foundation, "How to use Django's CSRF protection." URL:
  [https://docs.djangoproject.com/en/stable/howto/csrf/](https://docs.djangoproject.com/en/stable/howto/csrf/),
  verified 2026-08-02.
- Ruby on Rails Guides, "Securing Rails Applications." URL:
  [https://guides.rubyonrails.org/security.html](https://guides.rubyonrails.org/security.html),
  verified 2026-08-02.
- Spring Security Reference, "Cross Site Request Forgery (CSRF)." URL:
  [https://docs.spring.io/spring-security/reference/7.0/servlet/exploits/csrf.html](https://docs.spring.io/spring-security/reference/7.0/servlet/exploits/csrf.html),
  verified 2026-08-02.
- Spring Security API, "CsrfFilter." URL:
  [https://docs.spring.io/spring-security/reference/api/java/org/springframework/security/web/csrf/CsrfFilter.html](https://docs.spring.io/spring-security/reference/api/java/org/springframework/security/web/csrf/CsrfFilter.html),
  verified 2026-08-02.
- Laravel Documentation, "CSRF Protection." URL:
  [https://laravel.com/docs/12.x/csrf](https://laravel.com/docs/12.x/csrf),
  verified 2026-08-02.
- PortSwigger Web Security Academy, "Bypassing CSRF token validation." URL:
  [https://portswigger.net/web-security/csrf/bypassing-token-validation](https://portswigger.net/web-security/csrf/bypassing-token-validation),
  verified 2026-08-02.
- PortSwigger Web Security Academy, "Bypassing SameSite cookie restrictions."
  URL:
  [https://portswigger.net/web-security/csrf/bypassing-samesite-restrictions](https://portswigger.net/web-security/csrf/bypassing-samesite-restrictions),
  verified 2026-08-02.

## Code examples

The following examples are intentionally framework-free. They model the token
gate that a framework middleware would normally provide.

```python
import hmac
import secrets


def new_session() -> dict[str, str]:
    return {"csrf": secrets.token_urlsafe(32)}


def render_form(session: dict[str, str]) -> str:
    token = session["csrf"]
    return f'<input type="hidden" name="csrf" value="{token}">'


def accept_post(session: dict[str, str], form: dict[str, str]) -> bool:
    sent = form.get("csrf", "")
    expected = session.get("csrf", "")
    return bool(sent) and hmac.compare_digest(sent, expected)


session = new_session()
field = render_form(session)
assert "csrf" in field
assert accept_post(session, {"csrf": session["csrf"]})
assert not accept_post(session, {"csrf": "attacker"})
print("python csrf token ok")
```

```java
import java.security.SecureRandom;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;

public class CsrfTokenDemo {
    static final SecureRandom RNG = new SecureRandom();

    static String token() {
        byte[] bytes = new byte[32];
        RNG.nextBytes(bytes);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
    }

    static boolean constantTimeEquals(String left, String right) {
        byte[] a = left.getBytes(java.nio.charset.StandardCharsets.UTF_8);
        byte[] b = right.getBytes(java.nio.charset.StandardCharsets.UTF_8);
        int diff = a.length ^ b.length;
        for (int i = 0; i < Math.max(a.length, b.length); i++) {
            byte x = i < a.length ? a[i] : 0;
            byte y = i < b.length ? b[i] : 0;
            diff |= x ^ y;
        }
        return diff == 0;
    }

    static boolean accept(Map<String, String> session, Map<String, String> form) {
        String sent = form.getOrDefault("csrf", "");
        String expected = session.getOrDefault("csrf", "");
        return !sent.isEmpty() && constantTimeEquals(sent, expected);
    }

    public static void main(String[] args) {
        Map<String, String> session = new HashMap<>();
        session.put("csrf", token());
        Map<String, String> form = Map.of("csrf", session.get("csrf"));
        if (!accept(session, form) || accept(session, Map.of("csrf", "bad"))) {
            throw new IllegalStateException("csrf check failed");
        }
        System.out.println("java csrf token ok");
    }
}
```

```go
package main

import (
	"crypto/hmac"
	"crypto/rand"
	"encoding/base64"
	"fmt"
)

func newToken() string {
	buf := make([]byte, 32)
	if _, err := rand.Read(buf); err != nil {
		panic(err)
	}
	return base64.RawURLEncoding.EncodeToString(buf)
}

func accept(session map[string]string, form map[string]string) bool {
	sent := form["csrf"]
	expected := session["csrf"]
	if sent == "" || expected == "" {
		return false
	}
	return hmac.Equal([]byte(sent), []byte(expected))
}

func main() {
	session := map[string]string{"csrf": newToken()}
	if !accept(session, map[string]string{"csrf": session["csrf"]}) {
		panic("valid token rejected")
	}
	if accept(session, map[string]string{"csrf": "attacker"}) {
		panic("bad token accepted")
	}
fmt.Println("go csrf token ok")
}
```

```swift
import Foundation

func token() -> String {
    UUID().uuidString + UUID().uuidString
}

func accept(session: [String: String], form: [String: String]) -> Bool {
    guard let sent = form["csrf"], let expected = session["csrf"] else {
        return false
    }
    return !sent.isEmpty && sent.utf8.elementsEqual(expected.utf8)
}

let session = ["csrf": token()]

if !accept(session: session, form: ["csrf": session["csrf"]!]) {
    fatalError("valid token rejected")
}

if accept(session: session, form: ["csrf": "attacker"]) {
    fatalError("bad token accepted")
}

print("swift csrf token ok")
```
