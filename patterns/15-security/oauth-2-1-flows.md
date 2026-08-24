---
name: OAuth 2.1 Flows
slug: oauth-2-1-flows
family: 15-security
category: Authorization
aliases: [OAuth Authorization Flows, OAuth Grant Flows, Authorization Code with PKCE]
first_described: "Hardt 2012, Hardt, Parecki, Lodderstedt 2026 draft"
maturity: established
related: [token-based-authentication, zero-trust, least-privilege, defense-in-depth]
incompatible_with: [password-sharing, implicit-browser-tokens, resource-owner-password-credentials]
verified: 2026-08-02
---

# OAuth 2.1 Flows

## 1. Name, aliases, and lineage

The canonical name in this entry is OAuth 2.1 Flows. In common engineering
speech the same design is called OAuth flows, OAuth grant flows, authorization
flows, auth code flow, device flow, client credentials flow, or authorization
code with PKCE. The name is partly contested because OAuth 2.1 is not a new
product protocol with a new wire shape. It is the consolidation line for OAuth
2.0 practice after more than a decade of deployment, threat research, and
extension RFCs. The OAuth 2.1 Internet-Draft describes the framework as a
replacement for RFC 6749 and narrows the core grant set to two grants plus
extension grants, while carrying forward the role model and HTTP redirection
model from OAuth 2.0 (Hardt, Parecki, Lodderstedt, *The OAuth 2.1
Authorization Framework*, draft-ietf-oauth-v2-1-15, sections 1.1, 1.3, 4.1,
4.2, https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-15,
verified 2026-08-02).

The lineage starts with OAuth 2.0, edited by Dick Hardt and published as RFC
6749 in October 2012. RFC 6749 defined four roles, resource owner, resource
server, client, and authorization server, and defined authorization code,
implicit, resource owner password credentials, client credentials, plus an
extension grant mechanism (Hardt, *The OAuth 2.0 Authorization Framework*, RFC
6749, sections 1.1, 1.3, and 4, https://www.rfc-editor.org/info/rfc6749/,
verified 2026-08-02). Bearer token usage was specified separately in RFC 6750,
which defines bearer tokens as tokens usable by any party in possession of the
token and defines the HTTP Authorization header form for presenting them (Jones
and Hardt, *The OAuth 2.0 Authorization Framework. Bearer Token Usage*, RFC
6750, sections 1.2 and 2.1, https://www.rfc-editor.org/info/rfc6750/,
verified 2026-08-02).

The modern flow shape depends on PKCE. RFC 7636 introduced Proof Key for Code
Exchange to protect public clients using the authorization code grant from
authorization code interception. It does this by having the client create a
one-time verifier, send a derived challenge with the authorization request, and
present the verifier at the token endpoint (Sakimura, Bradley, Agarwal, *Proof
Key for Code Exchange by OAuth Public Clients*, RFC 7636, sections 1 and 4,
https://www.rfc-editor.org/info/rfc7636/, verified 2026-08-02). RFC 9700, the
OAuth 2.0 Security Best Current Practice, states that public clients must use
PKCE for authorization code flows and that confidential clients should use it
as protection against code misuse and injection (Lodderstedt, Bradley,
Labunets, Fett, *Best Current Practice for OAuth 2.0 Security*, RFC 9700,
section 2.1.1, https://www.rfc-editor.org/info/rfc9700/, verified
2026-08-02).

In this repository, the pattern name refers to the architectural pattern of
choosing, implementing, and operating OAuth 2.1 style flows across clients,
authorization servers, and resource servers. It is a security pattern because
the core design separates user credentials from client credentials, confines
authorization to scoped tokens, and places policy decisions at the
authorization server and resource server instead of distributing user passwords
to every caller. Judgement. The valuable pattern is not "add OAuth" as a
checkbox. The value is choosing the right grant for the caller shape and making
each protocol handoff observable and rejectable.

## 2. Problem and context

A service needs to let software access protected resources without giving that
software the resource owner's primary credential. The caller might be a web
application acting for a signed-in user, a mobile application that cannot hide a
client secret, a command-line tool with no browser surface, or a daemon acting
as itself. The protected resource might be a profile endpoint, source-code API,
payment API, calendar API, or internal service API. The common mistake is to
model all of those cases as "login" and pass a password, API key, or long-lived
token through every layer.

OAuth separates that problem into roles. RFC 6749 defines the resource owner as
the entity that can grant access, the client as the application making protected
resource requests, the authorization server as the issuer of access tokens, and
the resource server as the host of protected resources (RFC 6749, section 1.1,
https://www.rfc-editor.org/info/rfc6749/, verified 2026-08-02). That role
split matters because the client is not the resource owner, even when the
client is trusted by the same company. The client receives an access token with
bounded authority. It does not receive the user's password, and the resource
server does not need to know how the user authenticated.

The context that makes OAuth 2.1 flows the right pattern has five parts.

- A resource server must accept delegated access from multiple clients.
- The authorization server can centralize consent, policy, client
  registration, token issuance, and token revocation.
- The client can make HTTP requests and can be classified by its ability to
  keep credentials confidential.
- Access can be represented as scopes, audiences, claims, or server-side token
  state.
- Failure must be explicit. A rejected redirect, wrong state value, reused
  authorization code, unknown audience, or invalid proof must stop the exchange.

OAuth 2.1 flow selection appears in code as a wiring problem. A browser-facing
web app signs users in through authorization code with PKCE. A native app uses
the system browser and a redirect URI suitable for the platform. A device with
limited input uses the device authorization grant from RFC 8628. A workload
that has no user uses client credentials. A middle tier that must preserve
delegation might use token exchange from RFC 8693 rather than passing a
front-end token downstream. Each choice changes where secrets live, how
redirects are validated, how refresh is handled, and which actor appears in
logs.

## 3. Forces

Judgement. These forces are engineering trade-offs drawn from operating OAuth
systems. Sourced citations identify protocol facts, not the weighting.

- **Credential exposure.** Favoured. User passwords remain at the
  authorization server, while clients receive tokens with bounded authority.
  The pattern sacrifices simplicity because a developer must now handle codes,
  state, verifiers, tokens, refresh, and resource server validation.
- **Latency.** Sacrificed for user-facing flows. Authorization code with PKCE
  adds browser redirection and a token endpoint round trip before the API call.
  Client credentials has lower latency because there is no interactive user
  step.
- **Coupling.** Favoured between resource servers and clients, sacrificed
  between clients and the authorization server. Resource servers can reject
  tokens by issuer, audience, expiry, proof, and scope, while clients depend on
  registered redirect URIs, metadata, token endpoint behavior, and grant
  policy.
- **Consistency.** Favoured when one authorization server owns client
  registration and token policy. Sacrificed in federated systems where each
  issuer has different metadata, scope naming, refresh policy, and error
  behavior.
- **Operability.** Favoured if every exchange writes correlation identifiers
  and reasoned denials. Sacrificed if token contents are opaque to clients and
  resource servers require introspection during incidents.
- **Cost.** Sacrificed. A correct deployment needs redirect allowlists,
  metadata publishing, key rotation, token storage, consent UX, client
  lifecycle, replay checks, and incident response playbooks.
- **Team topology.** Favoured for platform organizations. Identity and
  security teams can own the authorization server, product teams can register
  clients, and API teams can validate tokens. Sacrificed in small products
  where the same team owns every role and protocol ceremony may outrun the
  threat model.
- **Cognitive load.** Sacrificed. OAuth names are overloaded: client does not
  mean browser, confidential does not mean trusted by policy, public does not
  mean untrusted user, and token exchange does not mean refresh.
- **Privacy.** Favoured when scopes and audience restrictions narrow disclosure.
  Sacrificed if tokens carry broad claims, if consent screens describe scopes
  poorly, or if logs collect token material.

The pattern favours constrained delegation, central policy, and revocation. It
sacrifices directness, local reasoning, and low setup cost. That is why OAuth is
a poor fit for a single private server with one human operator, and a strong fit
for an API platform with many callers.

## 4. Applicability and non-applicability

Reach for OAuth 2.1 flows when these conditions hold.

- A client needs access to an HTTP API owned by another security boundary.
- Users must authorize access without sharing their primary credentials with
  the client.
- Different clients need different scopes, redirect URIs, grant policies, or
  token lifetimes.
- A public client, such as a mobile app, desktop app, CLI, or browser app, must
  obtain user-delegated access. Use authorization code with PKCE.
- A device has limited input and can ask a user to complete authorization on
  another device. Use the device authorization grant from RFC 8628 (Denniss,
  Bradley, Jones, Lodderstedt, *OAuth 2.0 Device Authorization Grant*, RFC
  8628, section 3, https://www.rfc-editor.org/info/rfc8628/, verified
  2026-08-02).
- A machine identity calls an API without a user. Use client credentials, where
  the client authenticates as itself.
- A middle-tier service must trade one token for another with narrower audience
  or actor semantics. Consider token exchange as specified by RFC 8693 (Jones,
  Nadalin, Campbell, Bradley, Mortimore, *OAuth 2.0 Token Exchange*, RFC 8693,
  section 2, https://www.rfc-editor.org/info/rfc8693/, verified 2026-08-02).
- Clients and authorization servers can agree on metadata, issuer identity,
  supported grant types, token endpoint authentication, and signing keys. RFC
  8414 defines authorization server metadata at a well-known HTTPS location
  (Jones, Sakimura, Bradley, *OAuth 2.0 Authorization Server Metadata*, RFC
  8414, section 3, https://www.rfc-editor.org/info/rfc8414/, verified
  2026-08-02).

Do NOT reach for OAuth 2.1 flows in these cases.

- **Single process authorization.** If the caller and resource live in the same
  deployable unit, use local authorization checks. OAuth adds network protocol
  failure without a boundary payoff.
- **A first-party session cookie is enough.** A web application that only calls
  its own backend from its own browser session can use a session cookie with
  CSRF protection. OAuth becomes useful when the API needs token-based access
  by separately registered clients.
- **You need authentication only.** OAuth is an authorization framework. If the
  product needs user sign-in claims, use OpenID Connect on top and validate ID
  token semantics from that specification. Do not infer identity from an access
  token minted for an API.
- **The client cannot protect redirect handling.** If the platform cannot bind
  the redirect response to the transaction through state, PKCE, issuer checks,
  and exact redirect URI policy, the flow is unsafe.
- **A shared static API key matches the risk.** Internal batch jobs with one
  service account, no user delegation, and no third-party client lifecycle may
  be better served by short-lived service credentials from the infrastructure
  platform.
- **You need authorization inside a resource server after token validation.**
  OAuth can say that a caller has a scope or claim. It does not decide whether
  user 123 can edit invoice 456. That object authorization still belongs in
  the resource server.
- **The only reason is "SSO".** OAuth alone is not a sign-in protocol. Use
  OpenID Connect if the client needs identity, authentication time, nonce
  handling, and ID token validation.
- **Legacy implicit or password grants are the requested shape.** OAuth 2.1
  style practice moves away from browser-delivered access tokens and direct
  collection of resource-owner passwords. RFC 9700 says clients should not use
  implicit grants except under narrow conditions and states that resource owner
  password credentials must not be used (RFC 9700, sections 2.1.2 and 2.4,
  https://www.rfc-editor.org/info/rfc9700/, verified 2026-08-02).
- **The authorization server cannot be operated as security infrastructure.**
  Token issuance, redirect validation, client credentials, keys, and refresh
  token rotation are live security controls, not a library detail.

## 5. Structure

The participants are protocol roles, not classes.

- **Resource Owner.** The person or entity that can grant access to a protected
  resource. In user flows, this is the end user.
- **User Agent.** The browser or system authorization surface through which the
  resource owner interacts with the authorization server.
- **Client.** The application requesting access. It can be confidential if it
  can keep credentials secret, or public if it cannot. It owns redirect
  handling, state storage, PKCE verifier storage, token storage, and API calls.
- **Authorization Server.** The policy authority that authenticates the
  resource owner when needed, authenticates clients when possible, validates
  grants, issues tokens, rotates keys, publishes metadata, and records consent
  or grant state.
- **Resource Server.** The API that accepts protected requests. It validates
  issuer, audience, expiry, token status, proof binding, and scope before
  serving the resource.
- **Authorization Grant.** A credential representing authorization. In the main
  user flow it is an authorization code. In device flow it is a device code
  presented at the token endpoint after user approval. In client credentials it
  is the client's authenticated request.
- **Access Token.** A credential presented to the resource server. With bearer
  tokens, possession is enough unless sender constraints are added.
- **Refresh Token.** A credential used at the token endpoint to obtain another
  access token. RFC 9700 requires public-client refresh tokens to be
  sender-constrained or rotated with replay detection (RFC 9700, section 2.2.2,
  https://www.rfc-editor.org/info/rfc9700/, verified 2026-08-02).
- **Metadata Document.** A published description of authorization server
  endpoints and capabilities. Clients use it to find endpoints and supported
  methods rather than hardcoding every value.

Relationships. The client redirects the user agent to the authorization server,
then receives the authorization response at a pre-registered redirect URI. The
client calls the token endpoint directly. The resource server never accepts the
authorization code. The authorization server never sends access tokens to the
redirect URI in an OAuth 2.1 style authorization code flow. The resource server
does not treat token presence as enough. It validates the token against its
local policy and the issuer's contract.

## 6. ASCII structure diagram

```text
  +----------------+        browser redirect        +------------------+
  | Resource Owner | <----------------------------> | Authorization    |
  | via User Agent |                                | Server           |
  +----------------+                                | - authorize      |
          ^                                         | - token          |
          | redirect_uri with code                  | - metadata       |
          v                                         +---------+--------+
  +----------------+     back-channel token POST              ^
  | Client         | -----------------------------------------+
  | - state store  |      code + code_verifier or client auth |
  | - PKCE store   |                                          |
  | - token store  |      access token                        |
  +-------+--------+ <----------------------------------------+
          |
          | HTTPS request with access token
          v
  +----------------+
  | Resource Server|
  | - issuer check |
  | - audience     |
  | - scope        |
  | - proof check  |
  +----------------+

  The authorization code crosses only through the user agent.
  The access token is returned only through the token endpoint response.
```

## 7. Dynamics

The main OAuth 2.1 user-delegated flow is authorization code with PKCE. The
client starts by making transaction-local state and a PKCE verifier. It stores
both in a place bound to the current user agent. It derives the challenge and
redirects the browser to the authorization endpoint with response type `code`,
client id, redirect URI, scope, state, code challenge, and challenge method. The
authorization server authenticates the resource owner, applies policy, and
returns the browser to the redirect URI with a code and state. The client
compares state before doing any token exchange. It then calls the token endpoint
with the code, redirect URI, client authentication if applicable, and the
original verifier. The authorization server compares the verifier to the stored
challenge, rejects replayed or mismatched codes, and returns tokens. The client
uses the access token at the resource server. The resource server validates the
token before serving the request.

```text
Client            User Agent        Authorization Server      Resource Server
  |                   |                       |                       |
  | create state, PKCE verifier              |                       |
  |------------------>| 302 /authorize       |                       |
  |                   |---------------------->|                       |
  |                   | authenticate user     |                       |
  |                   | authorize scopes      |                       |
  |                   |<----------------------| 302 redirect_uri      |
  |<------------------| code + state          |                       |
  | validate state                            |                       |
  | POST /token code + verifier              |                       |
  |------------------------------------------>|                       |
  |                   |                       | check code, PKCE      |
  |<------------------------------------------| access token          |
  | GET /resource Authorization: Bearer token                         |
  |----------------------------------------------------------------->|
  |                   |                       |                       | check
  |<-----------------------------------------------------------------| data
```

Device authorization changes the first half of the exchange. The client asks
the authorization server for a device code and user code, displays the user
code and verification URI, and polls the token endpoint until the user
authorizes or the code expires. RFC 8628 defines the device authorization
endpoint, the device code response, the user interaction, and the polling token
request (RFC 8628, section 3, https://www.rfc-editor.org/info/rfc8628/,
verified 2026-08-02).

Client credentials removes the user agent. The client authenticates at the
token endpoint and receives an access token representing the client, not a
human user. That token should be audience-restricted and scoped to the resource
server it will call.

Token exchange inserts a second token endpoint exchange. A caller presents a
subject token or actor token and asks for a new token with the target resource,
audience, or delegation semantics. RFC 8693 defines that token exchange request
as an extension grant using
`urn:ietf:params:oauth:grant-type:token-exchange` (RFC 8693, section 2.1,
https://www.rfc-editor.org/info/rfc8693/, verified 2026-08-02).

## 8. Implementation variants

**Authorization code with PKCE for web apps.** The client has a server-side
component, stores state and verifier server-side, and exchanges the code from
the backend. Confidential clients authenticate at the token endpoint. Judgement.
This is the default for new browser-facing apps because access tokens stay out
of the front channel and PKCE binds the code to the transaction.

**Authorization code with PKCE for browser apps.** The JavaScript application
starts the flow and stores transaction state in browser storage or a cookie.
The token endpoint must support the browser's cross-origin request model.
Judgement. A backend-for-frontend often has a better incident profile because
refresh tokens and API tokens can remain server-side.

**Native app authorization code with PKCE.** RFC 8252 specifies OAuth for native
apps and describes initiating authorization requests from the native app using
the authorization code grant with a redirect URI suitable for the app (Denniss
and Bradley, *OAuth 2.0 for Native Apps*, RFC 8252, section 6,
https://www.rfc-editor.org/info/rfc8252/, verified 2026-08-02). The usual
variant uses the system browser rather than an embedded web view, so user
credentials remain in the authorization server's browser context.

**Device authorization grant.** The device gets a device code and user code,
then polls while the user completes authorization elsewhere. It fits televisions,
CLIs, appliances, and constrained shells. The trade-off is delayed completion,
polling load, and phishing risk if the user cannot identify the requesting
device.

**Client credentials.** The client authenticates as itself and receives a token
for service access. The flow is short and automatable. It cannot express user
consent, and using it as a shortcut for user actions removes accountability.

**Pushed Authorization Requests.** RFC 9126 defines a PAR endpoint where the
client posts authorization request parameters to the authorization server and
receives a request URI used in the later authorization request (Lodderstedt,
Campbell, Sakimura, Tonge, Skokan, *OAuth 2.0 Pushed Authorization Requests*,
RFC 9126, sections 2 and 4, https://www.rfc-editor.org/info/rfc9126/,
verified 2026-08-02). Judgement. PAR is worth the extra endpoint when request
contents are large, high-risk, signed, or need server-side validation before
the browser redirect.

**Sender-constrained tokens.** RFC 9700 recommends sender-constraining access
tokens with mechanisms such as mutual TLS or DPoP to reduce replay impact (RFC
9700, section 2.2.1, https://www.rfc-editor.org/info/rfc9700/, verified
2026-08-02). RFC 8705 specifies mutual TLS client authentication and
certificate-bound access tokens (Campbell, Bradley, Sakimura, Lodderstedt,
*OAuth 2.0 Mutual-TLS Client Authentication and Certificate-Bound Access
Tokens*, RFC 8705, sections 2 and 3, https://www.rfc-editor.org/info/rfc8705/,
verified 2026-08-02). RFC 9449 specifies DPoP as a proof-of-possession method
for OAuth access tokens (Fett, Campbell, Bradley, Lodderstedt, Jones, Waite,
*OAuth 2.0 Demonstrating Proof of Possession*, RFC 9449,
https://www.rfc-editor.org/info/rfc9449/, verified 2026-08-02).

**Opaque tokens with introspection.** The resource server calls the
authorization server or an introspection service to learn token status and
claims. Revocation is fast and token contents stay off the client. The cost is
runtime dependency and cache invalidation.

**Self-contained signed tokens.** The resource server validates a signed token
locally. Latency is low and outages in the authorization server do not block
every API call. Revocation and claim drift are harder because the token remains
valid until expiry unless the resource server has a denial cache or
introspection fallback.

## 9. Known production uses

**GitHub OAuth Apps and GitHub Apps.** GitHub documents a web application flow
in which users are redirected to request GitHub identity, redirected back to
the client with a temporary code and state, and the app exchanges that code for
an access token. GitHub's documentation also says its OAuth implementation
supports the standard authorization code grant and the OAuth 2.0 Device
Authorization Grant, and states that implicit grant is not supported for the
web application flow (GitHub Docs, *Authorizing OAuth apps*,
https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps,
verified 2026-08-02).

**Microsoft identity platform and MSAL.** Microsoft documents authorization
code, client credentials, device code, on-behalf-of, and other flows in MSAL.
Its authorization code documentation states that auth code flow paired with
PKCE and OpenID Connect can be used for single-page, server-based, desktop, and
mobile apps (Microsoft Learn, *Authentication flow support in MSAL*,
https://learn.microsoft.com/en-us/entra/identity-platform/msal-authentication-flows,
verified 2026-08-02; Microsoft Learn, *Microsoft identity platform and OAuth
2.0 authorization code flow*,
https://learn.microsoft.com/en-in/entra/identity-platform/v2-oauth2-auth-code-flow,
verified 2026-08-02).

**Spotify Web API.** Spotify documents authorization code, authorization code
with PKCE, and client credentials for its Web API. Its PKCE tutorial describes
creating a code verifier, deriving a challenge, requesting authorization, and
exchanging the authorization code with the verifier for an access token
(Spotify for Developers, *Authorization Code with PKCE Flow*,
https://developer.spotify.com/documentation/web-api/tutorials/code-pkce-flow,
verified 2026-08-02; Spotify for Developers, *Authorization*,
https://developer.spotify.com/documentation/web-api/concepts/authorization,
verified 2026-08-02).

**Google Identity and OAuth 2.0.** Google documents OAuth 2.0 authorization
flows for installed apps, web server apps, JavaScript apps, devices, and
service accounts. Judgement. In production architecture terms, that makes
Google a broad deployment example of the pattern across public clients,
confidential clients, devices, and service-to-service access. Source:
Google Identity, *Using OAuth 2.0 to Access Google APIs*,
https://developers.google.com/identity/protocols/oauth2, verified
2026-08-02.

## 10. Consequences

Positive consequences.

- Resource-owner credentials are not shared with clients.
- Access can be scoped, audience-restricted, time-limited, and revoked.
- Public clients can use authorization code with PKCE without relying on a
  static client secret hidden in app code.
- Resource servers can validate tokens without participating in user
  authentication.
- Authorization policy can be centralized at the authorization server.
- Client registration gives security teams a place to govern redirect URIs,
  grants, token endpoint authentication, and refresh behavior.
- Extension grants allow constrained additions such as device flow and token
  exchange without changing the core role model.

Negative consequences.

- Redirect-based flows create failure states that do not exist in direct API
  key designs: state mismatch, redirect mismatch, issuer mix-up, code replay,
  code expiration, and stale transaction storage.
- The client must protect verifier, state, refresh tokens, and access tokens.
- The resource server must validate token issuer, audience, expiry, signature
  or introspection status, and scope on every protected request.
- Incident response crosses teams. A token abuse incident may involve client
  code, authorization server logs, resource server logs, browser behavior, and
  user consent history.
- Scope naming can become a product contract. Once third-party clients depend
  on a scope, changing it becomes migration work.
- Bearer tokens are replayable if stolen unless sender constraints or short
  lifetimes reduce impact.
- User experience can degrade when consent screens are vague, redirect loops
  occur, or refresh policies force repeated authorization.

Judgement. OAuth 2.1 flows pay off when the organization treats them as
security infrastructure. They fail when a team treats the redirect and token
steps as boilerplate around a login button.

## 11. Failure modes and misuse

Judgement. The following triples are phrased as production symptoms first
because OAuth failures are often misdiagnosed as generic login bugs.

- **Symptom.** Users return from the authorization server and land on an error
  page saying the login expired or cannot be matched. **Cause.** The client
  stores `state` or PKCE verifier in volatile memory, the user has multiple
  tabs, or a load-balanced callback hits a node without the transaction.
  **Fix.** Store transaction state in a shared server-side store or an
  integrity-protected cookie bound to the browser session, with single-use
  deletion after callback.
- **Symptom.** Attack tests can start a flow in one browser session and finish
  it in another. **Cause.** State is absent, predictable, reused, or not bound
  to the initiating user agent. **Fix.** Generate high-entropy state for each
  transaction, bind it to the session, compare it before token exchange, and
  delete it after use.
- **Symptom.** A stolen authorization code can be exchanged from another
  process. **Cause.** PKCE is missing, `plain` challenge method is accepted for
  clients that can use S256, or the token endpoint does not bind the code to
  the verifier. **Fix.** Require S256 PKCE for public clients and use PKCE for
  confidential clients where supported.
- **Symptom.** The same authorization code produces more than one access
  token, or retry storms create duplicate sessions. **Cause.** Code redemption
  is not atomic. **Fix.** Mark codes consumed in a transaction that also issues
  tokens, and return an OAuth error for later use.
- **Symptom.** A resource server accepts a token minted for a different API.
  **Cause.** Audience is missing from the token or ignored by the resource
  server. **Fix.** Issue audience-restricted access tokens and reject tokens
  whose audience does not name the resource server.
- **Symptom.** Logs contain `Authorization: Bearer` values or URL query strings
  with token material. **Cause.** Middleware logs full headers, request bodies,
  or callback URLs. **Fix.** Redact Authorization, cookie, code, state,
  verifier, access token, and refresh token values before log emission.
- **Symptom.** Refresh token replay goes unnoticed and both the attacker and
  legitimate app keep working. **Cause.** Public-client refresh tokens are
  static bearer credentials. **Fix.** Use refresh token rotation with reuse
  detection, or sender-constrain refresh tokens where available.
- **Symptom.** A command-line tool asks users to paste passwords or access
  tokens. **Cause.** The team avoided device flow or local-loopback PKCE.
  **Fix.** Use device authorization grant for limited-input environments, or
  native app authorization code with PKCE where a browser can be opened.
- **Symptom.** Service logs cannot answer whether a request represented a user,
  an app, or delegated middle-tier action. **Cause.** Client credentials,
  user-delegated tokens, and exchanged tokens are all mapped to the same
  internal principal field. **Fix.** Preserve subject, actor, client id, issuer,
  grant type, and audience in authorization context and audit events.
- **Symptom.** Consent screens grant broad access that users do not understand.
  **Cause.** Scope design follows internal API names rather than user-visible
  permissions. **Fix.** Group low-level API scopes behind reviewed user-facing
  permission text and record the internal mapping.
- **Symptom.** Intermittent invalid token errors appear after key rotation.
  **Cause.** Resource servers cache signing keys without respecting key ids,
  cache headers, overlap windows, or emergency rotation paths. **Fix.** Fetch
  issuer metadata and keys by key id, keep old keys during overlap, and expose
  rotation metrics.
- **Symptom.** Browser apps keep access tokens in local storage for long
  periods. **Cause.** Token storage was treated as ordinary app state. **Fix.**
  Prefer backend-held tokens for high-risk APIs, reduce token lifetime, use
  refresh rotation, and apply content security policy and dependency controls.

## 12. Trade-off matrix

| Alternative | Credential exposure | Latency | Operability | Fit |
|---|---|---|---|---|
| OAuth 2.1 authorization code with PKCE | User password stays at authorization server, code is bound to verifier | Browser redirect plus token POST | Strong when state, code, grant, and token events are correlated | User-delegated access for web, native, and browser clients |
| OAuth 2.0 implicit grant | Access token returns through browser front channel | Fewer back-channel steps | Poorer incident profile because tokens appear in browser-facing response | Legacy browser clients only under narrow controls |
| Resource owner password credentials | Client sees the user's password | Low protocol latency | Poor because compromise of client exposes user credential | Legacy migration only, not OAuth 2.1 style practice |
| Static API key | Single secret sent to API | Low | Simple until rotation, attribution, and scope are needed | Internal service or one-party automation |
| Session cookie | Cookie scoped to first-party web app | Low after session exists | Good for one web origin, weak for external API clients | Same-site web app calling its own backend |
| SAML browser SSO | Assertion-based sign-in, not API token delegation | Browser redirect | Mature for enterprise sign-in, not an API authorization pattern | Workforce authentication to web apps |
| Mutual TLS service identity | Private key possession replaces bearer secret | Low after TLS setup | Strong for service mesh and controlled workloads | Server-to-server identity without user delegation |
| Token exchange | Existing token traded for narrower target token | Extra token POST | Good if actor and subject are logged | Middle-tier delegation and audience narrowing |

Judgement. The matrix shows why OAuth 2.1 flows should not replace every
authentication mechanism. They are the pattern for delegated API access across
security boundaries, not the cheapest way to identify one caller.

## 13. Related and incompatible patterns

**Token-Based Authentication** composes directly. OAuth access tokens are one
way to issue and govern tokens, while token-based authentication describes how
protected requests present and validate them. OAuth adds grant acquisition,
client registration, consent, and issuer policy.

**Least Privilege** is the authorization goal. Scopes, audiences, token
lifetimes, and token exchange can narrow authority. They do not create least
privilege by themselves. Resource servers must still map scopes and claims to
object-level permissions.

**Zero Trust** composes at the resource server. A zero-trust API treats each
request as independently verified by issuer, audience, token status, sender
proof, device posture where applicable, and local policy.

**Defense in Depth** appears as PKCE, state, exact redirect URI matching,
issuer checks, sender-constrained tokens, short token lifetimes, refresh
rotation, and log redaction. Each layer catches a different class of error.

**Complete Mediation** is the resource server's obligation. Token validation
must happen for every protected request, not only when a session starts.

**Secure by Default** shapes client registration. New clients should default to
authorization code with PKCE, exact redirect URIs, no implicit grant, short
access token lifetimes, and refresh rotation.

**Incompatible. Password sharing.** Giving a client the user's primary password
defeats the core separation in OAuth.

**Incompatible. Implicit browser tokens as a default.** RFC 9700 advises
clients to use authorization code or another response type that returns access
tokens from the token endpoint rather than the authorization response (RFC 9700,
section 2.1.2, https://www.rfc-editor.org/info/rfc9700/, verified
2026-08-02).

**Incompatible. Ambient bearer trust.** A resource server that accepts any
well-formed token without issuer, audience, expiry, and scope checks is not
using OAuth as an authorization pattern. It is accepting a string.

## 14. Refactoring path in and out

To introduce OAuth 2.1 flows into password-based or API-key-based access:

1. Inventory callers, resource servers, user-delegated operations, machine-only
   operations, token lifetimes, and revocation paths.
2. Draw the role boundary. Pick or build the authorization server and decide
   which APIs are resource servers.
3. Classify clients as public or confidential based on whether they can keep
   credentials secret. Do not classify by business trust.
4. Map each caller to a grant. Use authorization code with PKCE for user flows,
   device grant for limited-input devices, client credentials for machine-only
   callers, and token exchange for middle-tier delegation.
5. Define scopes and audiences from resource-server operations, then review
   them with product and security teams. Judgement. Scope names become an API
   contract, so keep them stable and few.
6. Register clients with exact redirect URIs, allowed grant types, token
   endpoint authentication method, and refresh policy.
7. Add the authorization redirect and callback. Store state and PKCE verifier
   transactionally. Reject mismatches before token exchange.
8. Add token exchange code and token storage. Redact every secret-bearing field
   in logs.
9. Add resource server validation. Reject wrong issuer, wrong audience, expired
   token, inactive token, missing proof, and missing scope.
10. Migrate callers behind a feature flag. Run old and new authorization paths
   in parallel where possible, but avoid accepting both token families forever.
11. Remove password or API-key access after telemetry proves all callers have
   moved.

Named refactorings from the refactoring family often apply. Replace Parameter
with Explicit Methods can split a generic "login type" switch into named flow
entry points. Extract Function helps isolate state generation, callback
validation, and token exchange. Introduce Parameter Object can package issuer,
client id, redirect URI, scopes, and endpoints into a typed client
registration object. Replace Conditional with Polymorphism can move grant
behavior out of a large flow switch when the product supports many grant
families.

To remove OAuth when it stops earning its place:

1. Identify the real boundary that remains. If all clients are same-site and
   first-party, a session cookie may be enough.
2. Preserve audit fields before removing tokens. User id, client id, actor,
   scope, and resource id may need replacements in logs.
3. Shorten token lifetimes and stop issuing new refresh tokens.
4. Move clients to the replacement credential path.
5. Disable grants per client before disabling authorization server endpoints.
6. Keep resource server rejection telemetry during the sunset period.

## 15. Testing and verification

Judgement. OAuth testing is less about happy-path login and more about proving
that each invalid handoff fails closed.

Test the authorization start. The client should generate a new state and PKCE
verifier per attempt, store them with expiry, derive an S256 challenge, and
build the authorization URL with the registered redirect URI. Unit tests can
check URL parameters without contacting an authorization server.

Test the callback. Feed the callback handler missing state, wrong state,
expired state, duplicate state, missing code, duplicate code, wrong issuer when
issuer is expected, and extra unknown parameters. The handler should reject
before token exchange when transaction binding fails.

Test token exchange. Use a fake authorization server that records the token
request. Verify the client sends code, redirect URI, verifier, and client
authentication when required. Simulate invalid grant, slow token endpoint,
network timeout, and retry. The client must not reuse consumed state after a
successful exchange.

Test resource server validation. Create tokens with wrong issuer, wrong
audience, expired `exp`, future `nbf`, missing scope, altered signature, unknown
key id, inactive introspection response, and wrong DPoP or mutual TLS binding.
Every one must be rejected with a controlled error and no protected data.

Test refresh behavior. For rotation, simulate two concurrent refresh attempts
with the same token. One may succeed. The other must trigger reuse handling
according to policy. Test lost-response retry as a separate case because
network failure after successful rotation is a common source of false replay
alarms.

Use these test doubles:

- Fake authorization server for deterministic code and token responses.
- Fake resource server for API client tests.
- Fake clock for expiry, `nbf`, rotation, and polling interval.
- Fake key set with known key ids for signing-key rotation tests.
- Browser callback fixture for redirect URI and query parsing.
- Introspection stub for opaque token active and inactive cases.

Manual verification still matters. Run a full browser flow in a test tenant,
cancel consent, deny a scope, use the back button, open two tabs, retry the
callback URL, rotate signing keys, revoke consent, and observe the resulting
events. The code examples below were run locally with `python3`, `go run`, and
`node`.

## 16. Observability signals

Judgement. A healthy OAuth deployment is visible as a set of low-cardinality
security events and high-cardinality correlation ids, never as token dumps.

Log these events with a correlation id: authorization request created,
authorization response received, state validation failed, code exchange
started, code exchange failed by OAuth error, token issued by grant type,
refresh attempted, refresh reuse detected, resource request denied, resource
request accepted, key set refreshed, client registration changed, redirect URI
changed, and consent revoked.

Metric dimensions should include issuer, client id, grant type, response type,
token endpoint authentication method, resource server, audience, scope family,
error code, and public versus confidential client. Avoid raw user ids in
high-cardinality metrics unless the telemetry system is approved for that data.

Healthy dashboards show stable authorization success rate, low state mismatch
rate, low invalid grant rate, refresh success within expected bounds, resource
server denials clustered by expected policy reasons, key set refresh success,
and no token redaction failures.

Failing dashboards show spikes in state mismatch, repeated invalid grant from
one client version, resource servers accepting tokens with missing audience,
refresh reuse detections, authorization endpoint open redirect attempts, token
endpoint latency, introspection dependency errors, and key id misses after
rotation.

Traces should not carry token values. Use hashes or opaque event identifiers
for joins. A useful trace joins the initial authorization request, callback,
token exchange, and first resource request. That trace answers whether a user
approved access, which client received the code, which grant issued the token,
and why the resource server accepted or denied the call.

## 17. Security and privacy implications

OAuth 2.1 flows close the password-sharing attack surface by keeping resource
owner credentials away from clients. They open a different surface: redirect
URI handling, state binding, code interception, token endpoint authentication,
token storage, refresh rotation, token replay, metadata trust, consent
phishing, and resource server validation.

RFC 9700 states that clients and authorization servers must not expose open
redirectors and that redirect URI matching should use exact string matching
except for specified localhost port behavior in native apps (RFC 9700, section
2.1, https://www.rfc-editor.org/info/rfc9700/, verified 2026-08-02). It also
recommends sender-constraining access tokens to prevent misuse of stolen tokens
and recommends audience restriction (RFC 9700, sections 2.2 and 2.3,
https://www.rfc-editor.org/info/rfc9700/, verified 2026-08-02).

Privacy risk concentrates in scopes, consent screens, token claims, logs, and
third-party client registration. Do not place sensitive profile data in access
tokens unless every resource server receiving the token is allowed to see it.
Prefer audience-specific tokens over one broad token accepted by many APIs.
Avoid logging subject claims when a pseudonymous request id can answer the
operational question.

Bearer tokens need special care because RFC 6750 defines them as usable by any
party in possession of the token (RFC 6750, section 1.2,
https://www.rfc-editor.org/info/rfc6750/, verified 2026-08-02). The practical
rules are strict: use TLS, prefer Authorization headers over URLs, redact
tokens, keep access tokens short-lived, rotate refresh tokens for public
clients, and use DPoP or mutual TLS when replay resistance is worth the
operational cost.

OAuth is silent about resource-level authorization after token validation. A
valid token with `invoice.write` does not prove that the caller may edit this
invoice. The resource server must still evaluate ownership, tenant boundary,
policy, legal hold, and data residency. Judgement. The most damaging OAuth
misuse is treating token validation as the final authorization decision.

## 18. References

- Dick Hardt, ed., *The OAuth 2.0 Authorization Framework*, RFC 6749,
  sections 1.1, 1.3, 4, and 4.1, October 2012,
  https://www.rfc-editor.org/info/rfc6749/, verified 2026-08-02.
- Michael B. Jones and Dick Hardt, *The OAuth 2.0 Authorization Framework.
  Bearer Token Usage*, RFC 6750, sections 1.2, 2.1, and 5.3, October 2012,
  https://www.rfc-editor.org/info/rfc6750/, verified 2026-08-02.
- Nat Sakimura, John Bradley, and Naveen Agarwal, *Proof Key for Code Exchange
  by OAuth Public Clients*, RFC 7636, sections 1 and 4, September 2015,
  https://www.rfc-editor.org/info/rfc7636/, verified 2026-08-02.
- William Denniss and John Bradley, *OAuth 2.0 for Native Apps*, RFC 8252,
  section 6, October 2017, https://www.rfc-editor.org/info/rfc8252/, verified
  2026-08-02.
- Michael B. Jones, Nat Sakimura, and John Bradley, *OAuth 2.0 Authorization
  Server Metadata*, RFC 8414, section 3, June 2018,
  https://www.rfc-editor.org/info/rfc8414/, verified 2026-08-02.
- William Denniss, John Bradley, Michael B. Jones, and Torsten Lodderstedt,
  *OAuth 2.0 Device Authorization Grant*, RFC 8628, section 3, August 2019,
  https://www.rfc-editor.org/info/rfc8628/, verified 2026-08-02.
- Michael B. Jones, Anthony Nadalin, Brian Campbell, John Bradley, and
  Charles Mortimore, *OAuth 2.0 Token Exchange*, RFC 8693, section 2, January
  2020, https://www.rfc-editor.org/info/rfc8693/, verified 2026-08-02.
- Brian Campbell, John Bradley, Nat Sakimura, and Torsten Lodderstedt, *OAuth
  2.0 Mutual-TLS Client Authentication and Certificate-Bound Access Tokens*,
  RFC 8705, sections 2 and 3, February 2020,
  https://www.rfc-editor.org/info/rfc8705/, verified 2026-08-02.
- Brian Campbell, John Bradley, and Hannes Tschofenig, *Resource Indicators
  for OAuth 2.0*, RFC 8707, February 2020,
  https://www.rfc-editor.org/info/rfc8707/, verified 2026-08-02.
- Torsten Lodderstedt, Brian Campbell, Nat Sakimura, Dave Tonge, and Filip
  Skokan, *OAuth 2.0 Pushed Authorization Requests*, RFC 9126, sections 2 and
  4, September 2021, https://www.rfc-editor.org/info/rfc9126/, verified
  2026-08-02.
- Daniel Fett, Brian Campbell, John Bradley, Torsten Lodderstedt, Michael B.
  Jones, and David Waite, *OAuth 2.0 Demonstrating Proof of Possession*, RFC
  9449, September 2023, https://www.rfc-editor.org/info/rfc9449/, verified
  2026-08-02.
- Torsten Lodderstedt, John Bradley, Andrii Labunets, and Daniel Fett, *Best
  Current Practice for OAuth 2.0 Security*, RFC 9700, sections 2.1, 2.2, 2.3,
  and 2.4, January 2025, https://www.rfc-editor.org/info/rfc9700/, verified
  2026-08-02.
- Dick Hardt, Aaron Parecki, and Torsten Lodderstedt, *The OAuth 2.1
  Authorization Framework*, draft-ietf-oauth-v2-1-15, sections 1.1, 1.3, 4.1,
  and 4.2, March 2026,
  https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-15, verified
  2026-08-02.
- GitHub Docs, *Authorizing OAuth apps*,
  https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps,
  verified 2026-08-02.
- Microsoft Learn, *Authentication flow support in MSAL*,
  https://learn.microsoft.com/en-us/entra/identity-platform/msal-authentication-flows,
  verified 2026-08-02.
- Microsoft Learn, *Microsoft identity platform and OAuth 2.0 authorization
  code flow*,
  https://learn.microsoft.com/en-in/entra/identity-platform/v2-oauth2-auth-code-flow,
  verified 2026-08-02.
- Spotify for Developers, *Authorization Code with PKCE Flow*,
  https://developer.spotify.com/documentation/web-api/tutorials/code-pkce-flow,
  verified 2026-08-02.
- Spotify for Developers, *Authorization*,
  https://developer.spotify.com/documentation/web-api/concepts/authorization,
  verified 2026-08-02.
- Google Identity, *Using OAuth 2.0 to Access Google APIs*,
  https://developers.google.com/identity/protocols/oauth2, verified
  2026-08-02.

## Code examples

The examples are deliberately small. They model local invariants that must be
true before any production OAuth library is trusted: PKCE challenge generation,
transaction binding, and resource server claim checks.

```typescript
const { createHash, randomBytes } = require("crypto");

type Pending = {
  state: string;
  verifier: string;
  redirectUri: string;
};

function b64url(input: any): string {
  return input.toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}

function beginAuth(redirectUri: string): Pending & { challenge: string } {
  const verifier = b64url(randomBytes(32));
  const state = b64url(randomBytes(16));
  const challenge = b64url(createHash("sha256").update(verifier).digest());
  return { state, verifier, redirectUri, challenge };
}

function finishAuth(pending: Pending, returnedState: string): string {
  if (pending.state !== returnedState) {
    throw new Error("state_mismatch");
  }
  return pending.verifier;
}

const pending = beginAuth("https://client.example/callback");
console.log(pending.challenge.length > 40);
console.log(finishAuth(pending, pending.state).length > 40);
```

```python
from dataclasses import dataclass
import hmac
import secrets


@dataclass
class Callback:
    code: str
    state: str


class TransactionStore:
    def __init__(self) -> None:
        self._states: set[str] = set()

    def start(self) -> str:
        state = secrets.token_urlsafe(24)
        self._states.add(state)
        return state

    def consume(self, callback: Callback) -> str:
        matched = any(hmac.compare_digest(callback.state, item)
                      for item in self._states)
        if not matched:
            raise ValueError("state_mismatch")
        self._states.remove(callback.state)
        if not callback.code:
            raise ValueError("missing_code")
        return callback.code


store = TransactionStore()
state = store.start()
print(store.consume(Callback(code="abc123", state=state)))
```

```go
package main

import (
	"errors"
	"fmt"
	"time"
)

type Claims struct {
	Issuer   string
	Audience string
	Scope    map[string]bool
	Expiry   time.Time
}

func Authorize(c Claims, issuer string, audience string, scope string,
	now time.Time) error {
	if c.Issuer != issuer {
		return errors.New("wrong_issuer")
	}
	if c.Audience != audience {
		return errors.New("wrong_audience")
	}
	if now.After(c.Expiry) {
		return errors.New("expired")
	}
	if !c.Scope[scope] {
		return errors.New("insufficient_scope")
	}
	return nil
}

func main() {
	claims := Claims{
		Issuer:   "https://as.example",
		Audience: "https://api.example",
		Scope:    map[string]bool{"invoice.read": true},
		Expiry:   time.Now().Add(time.Minute),
	}
	fmt.Println(Authorize(claims, "https://as.example",
		"https://api.example", "invoice.read", time.Now()) == nil)
}
```
