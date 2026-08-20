---
name: OpenID Connect
slug: openid-connect
family: 15-security
category: Security
aliases: [OIDC, OpenID Connect 1.0, OpenID Connect Core]
first_described: "OpenID Foundation OpenID Connect Core 1.0, 2014"
maturity: established
related: [oauth-2-1-flows, token-based-authentication, complete-mediation, zero-trust, secure-by-default]
incompatible_with: [homegrown-login-protocol, password-per-request, implicit-session-authority]
verified: 2026-08-02
---

# OpenID Connect

## 1. Name, aliases, and lineage

The canonical name is OpenID Connect. In code, tickets, and vendor consoles it
is usually shortened to OIDC. The formal specification name is OpenID Connect
Core 1.0. The OpenID Foundation published OpenID Connect Core 1.0 as a final
specification in February 2014, and the currently fetched Core page identifies
the errata set 2 version as dated December 15, 2023
([https://openid.net/specs/openid-connect-core-1_0.html](https://openid.net/specs/openid-connect-core-1_0.html),
verified 2026-08-02). The named editors on the fetched Core document are
Nat Sakimura, John Bradley, Michael B. Jones, Breno de Medeiros, and Chuck
Mortimore.

OpenID Connect is the authentication layer built on top of OAuth 2.0. Core
states that OAuth 2.0 defines a framework for obtaining and using access tokens
for protected resources, but does not define standard methods to provide
identity information about an authenticated end user. OpenID Connect adds that
missing identity protocol by requesting the `openid` scope and returning an ID
Token, a JSON Web Token that carries claims about the authentication event and
the subject
([https://openid.net/specs/openid-connect-core-1_0.html](https://openid.net/specs/openid-connect-core-1_0.html),
verified 2026-08-02). OAuth 2.0 itself is specified by RFC 6749
([https://www.rfc-editor.org/rfc/rfc6749](https://www.rfc-editor.org/rfc/rfc6749),
verified 2026-08-02). JWT is specified by RFC 7519
([https://www.rfc-editor.org/rfc/rfc7519](https://www.rfc-editor.org/rfc/rfc7519),
verified 2026-08-02).

The lineage matters because several systems still treat OAuth as if it were a
login protocol. That is the wrong boundary. OAuth answers whether a client may
call a resource server with a grant. OpenID Connect answers who authenticated,
which issuer made that assertion, which client the assertion was meant for, and
when the assertion expires. The shared wire shape is intentional, but the trust
decision is different.

The main aliases in real use are these.

- **OIDC.** The everyday operational abbreviation.
- **OpenID Connect 1.0.** The specification family.
- **OpenID Provider, OP.** The identity provider role that authenticates the
  end user and issues ID Tokens.
- **Relying Party, RP.** The client that relies on the OP's identity assertion.
- **ID Token login.** A common vendor phrase, imprecise but recognizable.

The older OpenID 2.0 protocol is a predecessor with a different wire design.
OpenID Connect kept the OpenID name but uses OAuth 2.0 flows, JSON, JWT, JWS,
and HTTPS endpoints rather than the earlier OpenID 2.0 message set. This entry
treats OpenID Connect as an established security pattern because it is a stable
standard with live deployments in consumer identity, enterprise identity,
developer platforms, and cluster authentication.

## 2. Problem and context

The problem appears when an application needs to sign in users through an
external identity system without copying passwords, duplicating multi-factor
logic, or inventing its own browser redirect protocol. The application needs a
machine-checkable assertion that a user authenticated at a trusted issuer. It
also needs a stable subject identifier, a bounded token lifetime, a way to bind
the response to the client that started the flow, and a way to retrieve provider
metadata and signing keys without hand-editing endpoint URLs.

The context is a distributed system with at least three parties. The end user
operates a browser or app. The relying party is the application that wants a
local session. The OpenID Provider owns the authentication ceremony and token
signing keys. In the common authorization code flow, the RP redirects the user
to the OP, receives a one-time code on a registered redirect URI, exchanges the
code at the token endpoint, validates the ID Token, and then creates its own
local session.

This is not the same problem as API authorization. A resource server validating
an access token is deciding whether an API call is allowed. A relying party
validating an ID Token is deciding whether to create or refresh an application
session for a subject. Mixing those decisions creates common defects. An access
token might be meant for an API audience, not for the RP. An ID Token might be
meant for a client, not for a resource server. The OIDC pattern gives each token
a job and makes the receiving component validate the claims tied to that job.

The pressure to use this pattern usually comes from one of these situations.

- A product supports enterprise single sign-on and must accept identities from
  Microsoft Entra ID, Okta, Google, or another OP.
- A platform wants social login without storing user passwords.
- A Kubernetes or cloud control plane wants human login through a corporate
  identity provider instead of long-lived local credentials.
- A mobile or browser app needs a standard redirect flow with replay defenses,
  issuer metadata, key rotation, and audience binding.
- A company wants one authentication policy surface for passwordless login,
  multi-factor authentication, risk signals, and account recovery.

The pattern is a protocol pattern, not a library pattern. A library can hide
request construction and token validation, but the design decision is still the
same: authentication is delegated to an issuer, the RP trusts only validated ID
Tokens from that issuer, and the RP maps the external subject to local account
state under rules it owns.

## 3. Forces

This section is engineering judgement, grounded in the cited protocol contracts
but weighing trade-offs from implementation practice.

- **Coupling.** Favoured. The RP is coupled to the OIDC contract rather than to
  each provider's private login API. The remaining coupling is provider
  configuration, claim conventions, and operational policy.
- **Latency.** Sacrificed at sign-in. Browser redirects, the token exchange,
  key discovery, and sometimes UserInfo calls add network hops. Cached metadata
  and keys keep normal validation local after startup.
- **Consistency.** Favoured for authentication semantics. Every RP validates
  issuer, audience, expiry, signature, state, and nonce under the same protocol
  model. Consistency is weaker for custom claims because each provider and
  tenant can shape them differently.
- **Operability.** Favoured when discovery, JWKS rotation, and structured logs
  are implemented well. Sacrificed when teams hide all protocol state inside a
  vendor SDK and cannot explain a failed login without packet traces.
- **Cost.** Favoured relative to building identity features in every app.
  Sacrificed relative to a single local login form, because OIDC requires
  provider registration, redirect URI management, token validation, key
  rotation, and incident playbooks.
- **Team topology.** Favoured. Identity teams can own OP policy, app teams can
  own RP integration, and security teams can audit a standard flow. The cost is
  a shared contract for claims and account linking.
- **Cognitive load.** Sacrificed. Teams must distinguish ID Tokens from access
  tokens, front-channel from back-channel messages, issuer from audience, and
  authentication from authorization.
- **Privacy.** Favoured when pairwise subject identifiers and narrow scopes are
  used. Sacrificed when RPs request broad profile claims or log tokens and
  claims without retention controls.
- **Availability.** Mixed. The RP no longer stores password verification logic,
  but fresh sign-in depends on the OP and on network paths to it. Existing RP
  sessions can keep working if their own session policy allows it.

The pattern gives a cleaner trust boundary, but it does not make login simple.
It moves the hardest parts into a standard ceremony whose failure modes are
known, observable, and testable.

## 4. Applicability and non-applicability

Reach for OpenID Connect when these conditions hold.

- Users already exist in an external identity provider, and the application
  should rely on that provider for authentication.
- The product must support enterprise single sign-on across many customer
  tenants and providers.
- The application needs a standard browser, native app, or device-facing
  authentication flow with signed identity assertions.
- The relying party can validate issuer metadata, keys, signatures, audience,
  expiry, state, and nonce before creating a session.
- The team can operate redirect URI registration, client credentials, key
  rotation, and incident response for login failures.
- The system benefits from provider-side policy such as multi-factor
  authentication, account recovery, conditional access, or social identity.
- The application needs a stable subject identifier and maybe selected profile
  claims, not the user's password.

Non-applicability list.

- **Do not use OIDC as a replacement for local authorization.** OIDC can tell
  the RP that a subject authenticated at an issuer. It does not decide whether
  that subject may approve a wire transfer, read a document, or administer a
  tenant. Keep local authorization policy local.
- **Do not use an ID Token as an API bearer token.** The ID Token audience is
  the client. A resource server needs an access token whose audience and scope
  match that API.
- **Do not use OIDC when both caller and receiver are backend services with no
  end user.** Client credentials, mTLS, SPIFFE, workload identity, or signed
  service tokens fit machine-to-machine calls better.
- **Do not adopt it only to avoid password storage for a tiny internal tool.**
  A reverse proxy with SSO, a managed identity-aware gateway, or platform
  access control may be cheaper than embedding an RP into the tool.
- **Do not use it with an issuer you cannot trust operationally.** The issuer
  controls authentication policy and signing keys. If issuer governance is
  unknown, the RP cannot treat its tokens as login evidence.
- **Do not accept dynamic issuer URLs from untrusted input.** Discovery is for
  retrieving metadata from a configured issuer, not for letting attackers choose
  the OP for a login callback.
- **Do not use the implicit flow for new browser apps.** OAuth 2.0 Security
  Best Current Practice warns against token exposure patterns in browser-based
  flows and recommends authorization code with PKCE for public clients
  ([https://www.rfc-editor.org/rfc/rfc9700](https://www.rfc-editor.org/rfc/rfc9700),
  verified 2026-08-02).
- **Do not confuse login with account linking.** If two issuers claim the same
  email address, that does not prove the same local user. Use issuer plus
  subject as the stable identity key unless an explicit linking flow says
  otherwise.
- **Do not use OIDC where the relying party cannot protect its redirect URI
  handling.** Open redirects, weak state binding, and callback confusion turn a
  standard protocol into an account takeover path.

## 5. Structure

The participants are named by security role.

- **End User.** The human subject who authenticates at the OP. The subject is
  represented in the ID Token by the `sub` claim.
- **User Agent.** Usually a browser or system browser tab. It carries
  front-channel redirects between RP and OP.
- **Relying Party.** The application that starts the authentication request,
  receives the callback, exchanges the code, validates the ID Token, and creates
  a local session.
- **OpenID Provider.** The issuer that authenticates the user and issues ID
  Tokens. Core also calls this an OAuth 2.0 authorization server implementing
  OpenID Connect.
- **Authorization Endpoint.** The OP endpoint that receives the front-channel
  authentication request.
- **Token Endpoint.** The OP endpoint used by the RP to exchange an
  authorization code for tokens.
- **JWKS Endpoint.** The endpoint that publishes public signing keys used by
  the RP to validate token signatures.
- **Discovery Document.** The provider metadata document, commonly retrieved
  from `/.well-known/openid-configuration`. OpenID Connect Discovery defines
  issuer discovery and provider metadata
  ([https://openid.net/specs/openid-connect-discovery-1_0.html](https://openid.net/specs/openid-connect-discovery-1_0.html),
  verified 2026-08-02).
- **ID Token.** A signed JWT containing claims about the authentication event,
  the issuer, the subject, the audience, and expiry. Core section 2 defines the
  ID Token role
  ([https://openid.net/specs/openid-connect-core-1_0.html](https://openid.net/specs/openid-connect-core-1_0.html),
  verified 2026-08-02).
- **Access Token.** A token for resource access, returned by OAuth flows. It is
  not the login assertion.
- **Local Session.** The RP's own session cookie, mobile session record, or
  application credential created after validation. OIDC does not define the
  RP's local session format.

The relationships are trust relationships. The RP trusts a configured issuer,
not the browser. The RP trusts an ID Token only after signature and claim
validation. The OP trusts a registered redirect URI and client configuration.
The user agent is treated as a delivery channel for front-channel values, not as
an authority.

## 6. ASCII structure diagram

```text
  +-----------+        front channel         +-----------------------+
  | End User  | <--------------------------> |     User Agent        |
  +-----------+                              +-----------+-----------+
                                                          |
                                                          | redirects
                                                          v
  +-----------------------+     back channel    +-------------------+
  |     Relying Party     | <-----------------> |   OpenID Provider |
  |-----------------------|                     |-------------------|
  | client_id             |  token request      | authorization     |
  | redirect_uri          |  JWKS fetch         | token endpoint    |
  | issuer allowlist      |  metadata fetch     | JWKS endpoint     |
  | local session store   |                     | user auth policy  |
  +-----------+-----------+                     +---------+---------+
              |                                           |
              | validates                                 | signs
              v                                           v
  +-----------------------+                     +-------------------+
  |      ID Token         |                     |    Signing Keys   |
  |-----------------------|                     |-------------------|
  | iss, sub, aud, exp    |                     | kid -> public key |
  | iat, nonce, auth_time |                     +-------------------+
  +-----------------------+

  The RP creates its own local session after ID Token validation.
```

## 7. Dynamics

The common runtime flow is authorization code with back-channel token exchange.
PKCE adds a verifier and challenge so a stolen code is not enough for a public
client. RFC 7636 specifies Proof Key for Code Exchange
([https://datatracker.ietf.org/doc/html/rfc7636](https://datatracker.ietf.org/doc/html/rfc7636),
verified 2026-08-02).

```text
End User      User Agent          Relying Party            OpenID Provider
   |              |                     |                         |
   | login        |                     |                         |
   |------------->|                     |                         |
   |              |  start login        |                         |
   |              |-------------------->|                         |
   |              |                     | create state, nonce,    |
   |              |                     | PKCE verifier           |
   |              |  redirect to auth endpoint                    |
   |              |<--------------------|                         |
   |              |---------------------------------------------->|
   |              |                     |                         |
   | authenticate |                     |                         |
   |<============>|                     |                         |
   |              | callback with code and state                  |
   |              |<----------------------------------------------|
   |              |-------------------->|                         |
   |              |                     | check state             |
   |              |                     | exchange code, verifier |
   |              |                     |------------------------>|
   |              |                     |                         |
   |              |                     | ID Token, access token  |
   |              |                     |<------------------------|
   |              |                     | fetch or use cached JWKS|
   |              |                     | validate ID Token       |
   |              |                     | create local session    |
   |              | app session cookie  |                         |
   |              |<--------------------|                         |
   | signed in    |                     |                         |
   |<-------------|                     |                         |
```

Important runtime checks happen after the callback. The RP compares `state` to
the value stored before redirect. It verifies the ID Token signature using the
issuer's key, checks `iss` against the configured issuer, checks `aud` against
its client ID, checks `exp` and `iat` against local time with a small clock
skew allowance, and checks `nonce` when a nonce was sent. If the ID Token has
multiple audiences, OIDC Core defines `azp` for the authorized party
([https://openid.net/specs/openid-connect-core-1_0.html](https://openid.net/specs/openid-connect-core-1_0.html),
verified 2026-08-02).

Logout dynamics are separate. RP-Initiated Logout defines a way for the RP to
ask the OP to log out an end user
([https://openid.net/specs/openid-connect-rpinitiated-1_0.html](https://openid.net/specs/openid-connect-rpinitiated-1_0.html),
verified 2026-08-02). Back-Channel Logout defines a server-to-server logout
notification from OP to RP
([https://openid.net/specs/openid-connect-backchannel-1_0.html](https://openid.net/specs/openid-connect-backchannel-1_0.html),
verified 2026-08-02). Treat logout as a separate integration, not as a property
that appears automatically when login works.

## 8. Implementation variants

**Authorization code with confidential client.** The RP is a backend web
application that can keep a client secret. It sends the user through the
authorization endpoint, receives a code, and exchanges that code from the server
side. This is the common enterprise web shape. The trade-off is a backend
dependency for login, which is usually acceptable because the backend is also
where the local session is created.

**Authorization code with PKCE for public clients.** The app cannot keep a
client secret, so it binds the code exchange to a verifier created before the
redirect. Native apps, command-line tools, and browser-based clients use this
shape. The trade-off is extra state management and stricter handling of the
verifier.

**Backend-for-frontend.** A browser app delegates OIDC to a small backend that
stores tokens server-side and gives the browser an HTTP-only session cookie.
Judgement. This is often the cleanest browser security shape because access and
refresh tokens do not live in JavaScript memory. The trade-off is an extra
backend component and cookie policy work.

**Federated enterprise tenant model.** The product stores issuer and client
configuration per customer tenant. The RP chooses configuration before starting
login, often from a tenant slug or email domain. The trade-off is operational
complexity. Issuer allowlists, domain proof, and safe account linking become
part of the product, not a library detail.

**Static provider configuration.** The RP stores endpoints and JWKS URLs in
configuration. This is simple for a single issuer. The trade-off is manual
updates when providers rotate metadata endpoints or add capabilities.

**Discovery-backed provider configuration.** The RP fetches
`/.well-known/openid-configuration`, then follows `jwks_uri` for keys. This
matches the Discovery specification. The trade-off is a startup and cache
failure surface. Cache metadata with a bounded lifetime, pin the issuer, and
fail closed when metadata does not match the configured issuer.

**UserInfo enrichment.** The RP calls the UserInfo endpoint with an access token
to fetch claims not present in the ID Token. Core defines the UserInfo endpoint
in section 5.3
([https://openid.net/specs/openid-connect-core-1_0.html](https://openid.net/specs/openid-connect-core-1_0.html),
verified 2026-08-02). The trade-off is another network call and a broader data
surface. Prefer stable local profile state when the claim is not needed during
login.

**Pairwise subject identifiers.** The OP returns a different `sub` per RP or
sector identifier. Core defines public and pairwise subject identifier types in
section 8
([https://openid.net/specs/openid-connect-core-1_0.html](https://openid.net/specs/openid-connect-core-1_0.html),
verified 2026-08-02). The trade-off is better privacy against RP correlation at
the cost of harder cross-application account correlation.

**Front-channel and back-channel logout.** Logout can be browser-mediated or
server-to-server. Front-channel logout has browser delivery limits. Back-channel
logout has cleaner server delivery but requires an endpoint, token validation,
and local session lookup.

## 9. Known production uses

**Google Sign-In.** Google's developer documentation says Google's OAuth 2.0
APIs support authentication and authorization, conform to the OpenID Connect
specification, and are OpenID Certified. The same page documents ID Tokens,
state validation, discovery, and Google Identity Services as built on the
OpenID Connect protocol
([https://developers.google.com/identity/openid-connect/openid-connect](https://developers.google.com/identity/openid-connect/openid-connect),
verified 2026-08-02).

**Microsoft identity platform and Microsoft Entra ID.** Microsoft documents
OpenID Connect on the Microsoft identity platform and describes it as an
authentication protocol built on OAuth 2.0 that can sign in users through the
v2.0 endpoint
([https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols-oidc](https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols-oidc),
verified 2026-08-02). This is the protocol surface used by Microsoft Entra ID
applications that choose OIDC sign-in.

**Kubernetes API server authentication.** Kubernetes documentation has a section
for OpenID Connect tokens. It describes the API server as able to validate
OIDC-issued tokens and map claims such as username and groups into Kubernetes
user info
([https://kubernetes.io/docs/reference/access-authn-authz/authentication/](https://kubernetes.io/docs/reference/access-authn-authz/authentication/),
verified 2026-08-02).

**Okta.** Okta's developer documentation explains OAuth 2.0 and OpenID Connect,
states that OIDC adds an ID Token to OAuth 2.0, and presents Okta authorization
servers as providers for these flows
([https://developer.okta.com/docs/concepts/oauth-openid/](https://developer.okta.com/docs/concepts/oauth-openid/),
verified 2026-08-02).

These uses are not proof that every integration is sound. They prove the
pattern is a real production contract across consumer identity, enterprise
identity, cloud-native control planes, and identity-as-a-service providers.

## 10. Consequences

Positive.

- Password verification, account recovery, multi-factor policy, and risk checks
  can live with the OP instead of being rebuilt in every relying party.
- RPs receive a signed, audience-bound identity assertion instead of scraping
  identity from an access token or a profile endpoint.
- Provider discovery and JWKS key publication give a standard path for endpoint
  and signing-key rotation.
- Enterprise customers can bring their identity provider without the product
  storing customer passwords.
- Subject identifiers give a durable account key when the RP resists using
  email address as identity.
- Standard flows make security review more concrete. Reviewers can inspect
  state, nonce, redirect URI, issuer, audience, expiry, and key validation.
- Multiple RPs can share one identity policy surface while keeping local
  authorization rules separate.

Negative.

- Login now depends on a remote issuer, browser redirects, and correct client
  registration.
- The RP must handle protocol state carefully. Weak state or nonce logic can
  turn a correct OP into a vulnerable login.
- Claim mapping becomes a product contract. Email, group, tenant, and role
  claims differ across providers and customer tenants.
- Account linking can become dangerous when teams equate email equality with
  identity equality.
- Debugging failed login requires cross-system visibility into RP logs, OP logs,
  redirect URI configuration, token contents, and clocks.
- Logout remains hard. RP session logout, OP logout, and upstream provider
  logout are different events.
- A vendor SDK can hide protocol details so thoroughly that the team cannot
  reason about failure or attack paths.

The main consequence is a shift of responsibility. The OP owns authentication,
but the RP still owns validation, session creation, account mapping,
authorization, and telemetry.

## 11. Failure modes and misuse

**Access token accepted as login proof.** Symptom. Users can sign in when the
RP receives a token whose audience is an API, or a token from another client is
accepted by the login callback. Cause. The RP treats any bearer token from the
issuer as identity proof. Fix. Accept only ID Tokens at the login boundary and
validate `iss`, `aud`, `exp`, `iat`, signature, and nonce.

**Issuer confusion.** Symptom. A token from a test tenant, malicious tenant, or
unexpected regional issuer creates a production session. Cause. The RP discovers
or accepts issuer metadata from user-controlled input. Fix. Pin issuers per
tenant, compare the metadata issuer value to the configured issuer, and reject
callbacks that do not map to a started login transaction.

**Weak state binding.** Symptom. Login callbacks fail intermittently, or a
security test can bind an attacker's authorization response to a victim's
browser session. Cause. `state` is predictable, missing, reused, or not tied to
the user's pre-login session. Fix. Generate high-entropy state, store it
server-side or in an integrity-protected cookie, and consume it once.

**Nonce skipped in flows that return ID Tokens through the front channel.**
Symptom. A replayed ID Token from an earlier login is accepted during a new
login attempt. Cause. The RP did not send or validate a nonce where the flow
needs replay binding. Fix. Generate nonce with the login transaction and compare
the returned claim before creating a session.

**Email used as the account key.** Symptom. A user loses access after changing
email, or two providers with the same email claim collide into one local
account. Cause. The RP treats email as a stable identity key. Fix. Store the
compound key `(issuer, subject)` and treat email as contact data unless an
explicit account-linking flow joins identities.

**JWKS cache never refreshes.** Symptom. Logins fail for many users after an OP
key rotation, with errors naming an unknown `kid`. Cause. The RP cached signing
keys forever or failed to refetch on key miss. Fix. Cache keys with expiry,
refetch on unknown key ID with rate limiting, and alert on sustained misses.

**JWKS cache refreshes too freely.** Symptom. Login latency spikes or the OP is
hit with many metadata requests during traffic bursts. Cause. Every token
validation fetches metadata or keys. Fix. Cache metadata and keys, respect cache
headers where present, and protect refresh with single-flight behavior.

**Redirect URI mismatch in production.** Symptom. Users see an OP error page
after sign-in, often only for one environment or custom domain. Cause. The RP
generates a callback URI that differs from the registered URI by scheme, host,
path, or trailing slash. Fix. Build callback URLs from trusted external
configuration and test every deployed domain.

**Group claim treated as current authorization truth.** Symptom. A removed
admin keeps access until the next login or token refresh. Cause. The RP uses
login-time group claims as a long-lived authorization cache. Fix. Set short
session lifetimes for privileged actions, refresh authorization data on demand,
or store local grants with revocation.

**Clock skew too strict or too loose.** Symptom. Fresh tokens fail around
deployment, or expired tokens remain valid far longer than policy allows.
Cause. RP clocks drift or validation allows excessive skew. Fix. Run clock
synchronization, monitor skew, and use a small bounded allowance.

**Tokens written to logs.** Symptom. Incident review finds ID Tokens or access
tokens in request logs, exception reports, or analytics events. Cause. Callback
URLs, headers, or decoded token payloads are logged without redaction. Fix.
Redact token values, avoid query logging on callback paths, and log token
metadata such as issuer, audience, and key ID instead.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | OpenID Connect | SAML 2.0 Web SSO | Local password login | OAuth 2.0 access token only | Reverse proxy SSO | SPIFFE workload identity |
|---|---|---|---|---|---|---|
| Coupling | Standard JSON and OAuth-based flow, provider config remains | XML assertions and federation metadata | Tight to local user store | Coupled to API authorization semantics | App coupled to proxy headers | Coupled to workload trust domain |
| Latency | Redirect plus token exchange at login | Redirect plus assertion processing | Local check can be fast | Depends on OAuth flow, no login claim | Proxy absorbs login cost | No browser login path |
| Consistency | Strong ID Token validation model | Strong assertion model, heavier profile set | Varies by app | Weak for authentication | Strong at perimeter, weaker inside app | Strong for services, not users |
| Operability | Needs issuer, JWKS, client, callback telemetry | Needs metadata, cert, assertion telemetry | Needs password and MFA operations | Needs token audience and scope telemetry | Central logs at proxy | Needs workload attestation telemetry |
| Cost | Medium integration, lower identity feature build | Higher federation skill cost | Low start, high security program cost | Low if OAuth exists, wrong login boundary | Low per app, proxy platform cost | High platform setup |
| Team topology | Identity team plus app teams share a standard | Federation specialists often required | Every app team owns auth risk | API team model bleeds into login | Platform team owns edge auth | Platform security owns workloads |
| Cognitive load | Medium to high | High | Low at first | High because semantics are wrong | Low for app teams | Medium for platform teams |
| Privacy | Pairwise subject and scopes available | Attribute release policies available | Local app sees all account data | Often overexposes API claims | Proxy may pass broad headers | No user profile concern |
| Availability | Fresh login depends on OP | Fresh login depends on IdP | Local store dependency | Authorization server dependency | Proxy and IdP dependency | Control-plane dependency |
| Best fit | User login for web, mobile, and federated apps | Enterprise federation with SAML estate | Small standalone systems | API authorization, not login | Internal apps behind a common edge | Service-to-service identity |

Reading of the table. OIDC wins where user authentication must cross
organizational or product boundaries and the application can validate tokens
correctly. SAML 2.0 remains common where enterprise federation contracts already
exist. Local password login is smallest at first but pushes every security
feature into the app. OAuth access-token-only designs are the wrong tool for
login. Reverse proxy SSO is often the better path for simple internal apps.
SPIFFE is for workloads, not human sign-in.

## 13. Related and incompatible patterns

- **OAuth 2.0 authorization code flow.** OIDC composes directly with it. OIDC
  adds the `openid` scope and ID Token semantics to an OAuth authorization
  flow.
- **Token-based Authentication.** OIDC uses tokens, but it is narrower. The
  pattern here is about identity assertions for login, not every bearer token.
- **Complete Mediation.** The RP must validate every callback and every token
  before session creation. A previously seen issuer or key does not remove the
  need to check audience, expiry, and transaction binding.
- **Secure by Default.** Default RP configuration should prefer authorization
  code with PKCE, exact redirect URIs, issuer pinning, signed tokens, and narrow
  scopes.
- **Zero Trust.** OIDC can establish user identity for a request, but each
  downstream authorization decision still needs context, policy, and resource
  checks.
- **SAML 2.0 Web SSO.** A substitute for browser federation. Use SAML where the
  customer estate or product surface is already SAML-first. Use OIDC where
  modern app, mobile, API, or developer platform integration is the main case.
- **Session Cookie.** Composes below OIDC. After validating the ID Token, most
  web RPs create a local session cookie. The cookie is the app session, not the
  OIDC assertion.
- **Service Locator.** Conflicts when used to fetch a global current user from
  decoded tokens anywhere in the codebase. Keep token validation at the edge and
  pass an authenticated principal object inward.
- **Homegrown login protocol.** Actively incompatible. If the team is inventing
  redirect parameters, token formats, issuer metadata, or signing-key rotation,
  it is re-creating a weaker OIDC.

## 14. Refactoring path in and out

Introducing OIDC into an application with local login.

1. Inventory current account identifiers, login session creation, password
   reset, MFA, and authorization checks. Separate authentication from
   authorization before touching protocol code.
2. Add a new external identity table keyed by `(issuer, subject)`, with a
   foreign key to the local user. Do not key it by email.
3. Register a relying party client with the provider for each environment. Use
   exact HTTPS redirect URIs and record client ID, issuer, and metadata URL in
   deployment configuration.
4. Add a login transaction store for state, nonce, PKCE verifier, return URL,
   tenant, and expiry. Make the transaction single-use.
5. Implement the authorization request. Start with authorization code plus
   PKCE, even for a confidential client, unless a provider constraint says
   otherwise.
6. Implement callback handling. Validate state before any token exchange. Then
   exchange the code and validate the ID Token before account lookup.
7. Create or link the local user only under explicit product rules. For
   enterprise tenants, prefer an administrator-controlled linking policy over
   automatic email matching.
8. Create the local session using the same session hardening as local login:
   HTTP-only cookie, secure cookie flag, session rotation after login, idle
   timeout, and privileged-action reauthentication where needed.
9. Add observability from dimension 16 before launch. Login systems fail in
   configuration-heavy ways, and the first production failure should not require
   adding logs.
10. Migrate users by allowing both login paths during a planned period, then
   remove password reset and password verification only after support and
   account recovery paths are ready.

Refactoring named moves. Extract Function helps isolate local session creation
from password verification. Replace Conditional with Polymorphism can be useful
when each enterprise tenant has provider-specific claim mapping. Introduce
Parameter Object fits token validation options such as issuer, client ID,
clock skew, and required claims. Replace Magic Literal with Symbolic Constant
fits claim names such as `iss`, `sub`, `aud`, and `exp`.

Removing OIDC when it no longer earns its place.

1. Identify which RPs, tenants, and local users depend on external identities.
2. Add an alternate authentication path and a migration path for each external
   account. This may be local password setup, passkeys, proxy SSO, or another
   federation protocol.
3. Stop offering new OIDC links while preserving existing sessions until their
   normal expiry.
4. Disable refresh or re-login through the provider. Keep read-only audit data
   for issuer and subject mappings as long as retention policy allows.
5. Delete provider credentials and redirect URIs from the OP console after all
   users have migrated.
6. Remove callback endpoints, discovery code, JWKS caches, and token validation
   code. Keep local authorization code untouched unless it was wrongly coupled
   to provider claims.

## 15. Testing and verification

This section is engineering judgement about practice, with protocol facts tied
to the cited specifications.

Unit tests should cover the validator as a pure component. Feed it generated
JWTs signed by test keys, and assert rejection for wrong issuer, wrong audience,
expired tokens, future `iat` outside skew, missing nonce, mismatched nonce,
unknown `kid`, unsupported algorithm, malformed claims, and multiple audiences
without expected `azp`. The test should not call a live OP.

Callback tests should cover the transaction boundary. A callback with missing
state fails before token exchange. A repeated state fails on the second use. A
callback for tenant A cannot complete tenant B's login. An invalid return URL
does not become an open redirect. A code exchange failure does not create a
session.

Integration tests should use a local fake OP or a test tenant. The fake OP must
serve discovery metadata, JWKS, authorization, and token endpoints. It should
rotate keys during a test so the RP proves that unknown `kid` handling works.
For test tenants, keep separate clients per environment so redirect URI drift is
caught before production.

Contract tests should cover claim mapping. Given a provider payload, assert the
local principal fields. Include absent optional claims, group overflow, nested
claim shapes, email changes, unverified email, and issuer-specific group naming.
This catches the common bug where a developer tests one tenant and then assumes
all providers shape claims the same way.

Security tests should cover browser behavior. Use an actual browser test for
SameSite cookie handling, callback routes, return URL validation, and session
rotation after login. Use negative tests for code injection into query
parameters and fragments. Verify that logs and error pages never contain full
tokens.

What became easier. The app no longer needs to test password hashing, password
reset token flows, MFA enrollment, and account recovery if those are fully
delegated to the OP.

What became harder. The app now needs protocol validation tests, provider
configuration tests, clock behavior tests, key rotation tests, and account
linking tests. These are more distributed than a local password check, but they
are also more standard and easier to automate once the test rig exists.

## 16. Observability signals

This section is engineering judgement about operating the pattern.

Log one structured event for login start, callback received, state validation
failure, code exchange failure, ID Token validation failure, account-linking
decision, and local session creation. Do not log full tokens, authorization
codes, refresh tokens, or raw callback URLs. Use a correlation ID created at
login start and store it with the transaction so callback logs join cleanly.

Useful labels and fields.

- `issuer`, normalized to a configured issuer ID rather than free text.
- `client_id`, or a safe hash of it when logs cross tenant boundaries.
- `tenant_id`, if the product has tenants.
- `kid` and signing algorithm from the token header.
- validation error code, such as `issuer_mismatch`, `audience_mismatch`,
  `expired`, `nonce_mismatch`, or `signature_key_missing`.
- token age at validation, not token value.
- redirect URI ID, not the full URL when it might contain sensitive query data.
- account-linking outcome, such as `existing_link`, `new_link_pending`,
  `blocked_email_collision`, or `admin_approval_required`.

Metrics that matter.

- Login starts, callbacks, successful local sessions, and failure rate by
  issuer and tenant.
- State mismatch count and repeated-state count.
- Token validation failures by reason.
- Unknown `kid` count and JWKS refresh attempts.
- Discovery and JWKS fetch latency, success, and cache age.
- Code exchange latency and error class.
- Account-linking blocks and manual approvals.
- Logout notification count and local session invalidation count, if logout is
  integrated.

A healthy dashboard shows a stable ratio from login starts to successful
sessions, low state mismatch, no repeated-state events outside tests, near-zero
unknown key IDs except during planned provider rotation, and token validation
latency that is local-cache fast. A failing dashboard shows callback volume
without matching login starts, one issuer with rising `redirect_uri_mismatch`,
unknown key IDs after an OP rotation, state mismatches after a cookie policy
change, or one tenant with account-linking blocks after a claim mapping change.

Alerts should be narrow. Alert on login failure rate by issuer, not on every
single failed login. Alert on repeated state reuse, unknown issuer, and token
logging detection because those point at attack paths or serious defects. Alert
on JWKS refresh failures only when cached keys are near expiry or unknown key
IDs are also rising.

## 17. Security and privacy implications

OpenID Connect closes one large attack surface by removing password handling
from the RP, but opens a protocol boundary that must be implemented with care.
The security model rests on exact issuer trust, redirect URI control,
transaction binding, token signature validation, and claim validation.

The RP must treat the user agent as hostile transport. Values returning through
the browser can be copied, replayed, omitted, or mixed with another transaction.
`state` binds the callback to a login transaction. `nonce` binds an ID Token to
the request where the flow requires it. PKCE binds an authorization code to the
client that started the flow. Redirect URI registration limits where the OP
sends responses. None of these fields is decorative.

Token validation is a complete mediation point. The RP should reject unsigned
tokens, unexpected algorithms, unknown keys, wrong issuer, wrong audience,
expired tokens, missing required claims, and claims that do not match the stored
login transaction. JWT Best Current Practice, RFC 8725, updates JWT security
guidance and is referenced by the RFC 7519 info page as an update to JWT
([https://www.rfc-editor.org/rfc/rfc7519](https://www.rfc-editor.org/rfc/rfc7519),
verified 2026-08-02). OAuth 2.0 Security Best Current Practice, RFC 9700,
documents current OAuth security recommendations that affect OIDC flows built
on OAuth
([https://www.rfc-editor.org/rfc/rfc9700](https://www.rfc-editor.org/rfc/rfc9700),
verified 2026-08-02).

Account linking is the high-risk product surface. A verified email claim can be
useful contact data, but it is not the same as the stable subject identifier.
Google's own OIDC documentation warns not to use the `email` field as the
unique user identifier and points to `sub` as the unique Google Account
identifier
([https://developers.google.com/identity/openid-connect/openid-connect](https://developers.google.com/identity/openid-connect/openid-connect),
verified 2026-08-02). For a multi-issuer RP, use `(issuer, subject)` as the
external identity key and require explicit policy for linking identities across
issuers.

Privacy concerns are direct. ID Tokens and UserInfo responses can contain
profile claims, group claims, tenant hints, email addresses, and authentication
context. Request only scopes and claims needed for the RP's function. Prefer
pairwise subject identifiers where cross-RP correlation is not needed. Do not
store raw tokens unless a clear operational requirement exists, and if tokens
are stored, protect them as credentials. Logs should contain validation metadata
and redacted claim summaries, not raw token bodies.

Logout has privacy and security consequences. If the user logs out of the RP
but remains logged in at the OP, the next sign-in may complete silently. If the
OP sends back-channel logout but the RP cannot map the logout token to local
sessions, stale sessions survive. Document which logout semantics the product
promises, then build and test those semantics explicitly.

## Code examples

These samples are intentionally small. They do not implement full JWT
cryptography or an HTTP server. They show the RP-side validation decisions and
transaction binding that application code must preserve around a real OIDC
library.

### TypeScript

```typescript
type Claims = {
  iss: string;
  sub: string;
  aud: string | string[];
  exp: number;
  iat: number;
  nonce?: string;
};

type LoginTransaction = {
  issuer: string;
  clientId: string;
  nonce: string;
  now: number;
};

function hasAudience(claims: Claims, clientId: string): boolean {
  const aud = Array.isArray(claims.aud) ? claims.aud : [claims.aud];
  return aud.includes(clientId);
}

function validateIdTokenClaims(
  claims: Claims,
  tx: LoginTransaction
): string {
  if (claims.iss !== tx.issuer) return "issuer mismatch";
  if (!hasAudience(claims, tx.clientId)) return "audience mismatch";
  if (claims.exp <= tx.now) return "expired";
  if (claims.iat > tx.now + 60) return "issued in the future";
  if (claims.nonce !== tx.nonce) return "nonce mismatch";
  if (claims.sub.length === 0) return "missing subject";
  return `${claims.iss}|${claims.sub}`;
}

const tx: LoginTransaction = {
  issuer: "https://issuer.example",
  clientId: "client-123",
  nonce: "n-456",
  now: 1_700_000_000,
};

const claims: Claims = {
  iss: "https://issuer.example",
  sub: "user-789",
  aud: ["client-123"],
  exp: 1_700_000_600,
  iat: 1_699_999_990,
  nonce: "n-456",
};

console.log(validateIdTokenClaims(claims, tx));
```

### Python

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Claims:
    iss: str
    sub: str
    aud: str | list[str]
    exp: int
    iat: int
    nonce: str | None = None


@dataclass(frozen=True)
class LoginTransaction:
    issuer: str
    client_id: str
    nonce: str
    now: int


def audiences(value: str | list[str]) -> list[str]:
    return value if isinstance(value, list) else [value]


def validate_id_token_claims(claims: Claims, tx: LoginTransaction) -> str:
    if claims.iss != tx.issuer:
        return "issuer mismatch"
    if tx.client_id not in audiences(claims.aud):
        return "audience mismatch"
    if claims.exp <= tx.now:
        return "expired"
    if claims.iat > tx.now + 60:
        return "issued in the future"
    if claims.nonce != tx.nonce:
        return "nonce mismatch"
    if not claims.sub:
        return "missing subject"
    return f"{claims.iss}|{claims.sub}"


if __name__ == "__main__":
    tx = LoginTransaction(
        issuer="https://issuer.example",
        client_id="client-123",
        nonce="n-456",
        now=1_700_000_000,
    )
    claims = Claims(
        iss="https://issuer.example",
        sub="user-789",
        aud=["client-123"],
        exp=1_700_000_600,
        iat=1_699_999_990,
        nonce="n-456",
    )
    print(validate_id_token_claims(claims, tx))
```

### Go

```go
package main

import "fmt"

type Claims struct {
	Issuer   string
	Subject  string
	Audience []string
	Expires  int64
	IssuedAt int64
	Nonce    string
}

type LoginTransaction struct {
	Issuer   string
	ClientID string
	Nonce    string
	Now      int64
}

func contains(values []string, wanted string) bool {
	for _, value := range values {
		if value == wanted {
			return true
		}
	}
	return false
}

func validateIDTokenClaims(claims Claims, tx LoginTransaction) string {
	if claims.Issuer != tx.Issuer {
		return "issuer mismatch"
	}
	if !contains(claims.Audience, tx.ClientID) {
		return "audience mismatch"
	}
	if claims.Expires <= tx.Now {
		return "expired"
	}
	if claims.IssuedAt > tx.Now+60 {
		return "issued in the future"
	}
	if claims.Nonce != tx.Nonce {
		return "nonce mismatch"
	}
	if claims.Subject == "" {
		return "missing subject"
	}
	return claims.Issuer + "|" + claims.Subject
}

func main() {
	tx := LoginTransaction{
		Issuer:   "https://issuer.example",
		ClientID: "client-123",
		Nonce:    "n-456",
		Now:      1700000000,
	}
	claims := Claims{
		Issuer:   "https://issuer.example",
		Subject:  "user-789",
		Audience: []string{"client-123"},
		Expires:  1700000600,
		IssuedAt: 1699999990,
		Nonce:    "n-456",
	}
	fmt.Println(validateIDTokenClaims(claims, tx))
}
```

## 18. References

1. Nat Sakimura, John Bradley, Michael B. Jones, Breno de Medeiros, Chuck
   Mortimore. *OpenID Connect Core 1.0 incorporating errata set 2*. OpenID
   Foundation, December 15, 2023. Sections 1, 2, 3, 5, 8, 9, 10, 16, and 17.
   [https://openid.net/specs/openid-connect-core-1_0.html](https://openid.net/specs/openid-connect-core-1_0.html).
   Verified 2026-08-02.
2. Nat Sakimura, John Bradley, Michael B. Jones, Edmund Jay. *OpenID Connect
   Discovery 1.0 incorporating errata set 2*. OpenID Foundation, December 15,
   2023. Sections 3 and 4.
   [https://openid.net/specs/openid-connect-discovery-1_0.html](https://openid.net/specs/openid-connect-discovery-1_0.html).
   Verified 2026-08-02.
3. D. Hardt, editor. *RFC 6749. The OAuth 2.0 Authorization Framework*. IETF,
   October 2012. Sections 1, 1.1, 1.4, and 4.1.
   [https://www.rfc-editor.org/rfc/rfc6749](https://www.rfc-editor.org/rfc/rfc6749).
   Verified 2026-08-02.
4. M. Jones, J. Bradley, N. Sakimura. *RFC 7519. JSON Web Token*. IETF, May
   2015. Sections 1, 3, 4, 7, 11, and 12.
   [https://www.rfc-editor.org/rfc/rfc7519](https://www.rfc-editor.org/rfc/rfc7519).
   Verified 2026-08-02.
5. N. Sakimura, J. Bradley, N. Agarwal. *RFC 7636. Proof Key for Code Exchange
   by OAuth Public Clients*. IETF, September 2015. Sections 1 and 4.
   [https://datatracker.ietf.org/doc/html/rfc7636](https://datatracker.ietf.org/doc/html/rfc7636).
   Verified 2026-08-02.
6. T. Lodderstedt, J. Bradley, A. Labunets, D. Fett. *RFC 9700. Best Current
   Practice for OAuth 2.0 Security*. IETF, January 2025.
   [https://www.rfc-editor.org/rfc/rfc9700](https://www.rfc-editor.org/rfc/rfc9700).
   Verified 2026-08-02.
7. OpenID Foundation. *OpenID Connect RP-Initiated Logout 1.0*. September 12,
   2022.
   [https://openid.net/specs/openid-connect-rpinitiated-1_0.html](https://openid.net/specs/openid-connect-rpinitiated-1_0.html).
   Verified 2026-08-02.
8. OpenID Foundation. *OpenID Connect Back-Channel Logout 1.0 incorporating
   errata set 1*. September 12, 2022.
   [https://openid.net/specs/openid-connect-backchannel-1_0.html](https://openid.net/specs/openid-connect-backchannel-1_0.html).
   Verified 2026-08-02.
9. Google. *OpenID Connect, Sign in with Google*. Google for Developers.
   [https://developers.google.com/identity/openid-connect/openid-connect](https://developers.google.com/identity/openid-connect/openid-connect).
   Verified 2026-08-02.
10. Microsoft. *OpenID Connect on the Microsoft identity platform*. Microsoft
   Learn.
   [https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols-oidc](https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols-oidc).
   Verified 2026-08-02.
11. Kubernetes project. *Authenticating, OpenID Connect tokens*. Kubernetes
   documentation.
   [https://kubernetes.io/docs/reference/access-authn-authz/authentication/](https://kubernetes.io/docs/reference/access-authn-authz/authentication/).
   Verified 2026-08-02.
12. Okta. *OAuth 2.0 and OpenID Connect overview*. Okta Developer.
   [https://developer.okta.com/docs/concepts/oauth-openid/](https://developer.okta.com/docs/concepts/oauth-openid/).
   Verified 2026-08-02.
