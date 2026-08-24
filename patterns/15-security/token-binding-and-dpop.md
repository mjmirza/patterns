---
name: Token Binding and DPoP
slug: token-binding-and-dpop
family: 15-security
category: Security
aliases: [DPoP, Demonstrating Proof of Possession, Sender-Constrained Tokens, Proof-of-Possession Tokens, Holder-of-Key Tokens, Token Binding]
first_described: "Popov, Nystroem, Balfanz, Hodges 2018. Fett, Campbell, Bradley, Lodderstedt, Jones, Waite 2023"
maturity: established
related: [bearer-token, mutual-tls, oauth-2, proof-key-for-code-exchange, jwk-thumbprint, replay-cache, nonce, certificate-bound-token]
incompatible_with: [bearer-only-api, token-in-url, shared-signing-key, client-secret-in-public-client]
verified: 2026-08-02
---

# Token Binding and DPoP

## 1. Name, aliases, and lineage

The canonical name in this entry is **Token Binding and DPoP**. It covers the
security pattern where a token is not accepted because the caller has the token
alone. The caller must also prove control of a private key or certificate that
the token issuer associated with that token.

Two lineages matter because the words have shifted over time.

**Token Binding** was the name of an IETF protocol suite for binding cookies
and other security tokens to key material associated with the TLS connection.
RFC 8471, *The Token Binding Protocol Version 1.0*, was published in October
2018 by Andrei Popov, Magnus Nystroem, Dirk Balfanz, and Jeff Hodges. It
defines a protocol that lets applications bind security tokens to the TLS
layer by using Token Binding identifiers
([https://www.rfc-editor.org/info/rfc8471/](https://www.rfc-editor.org/info/rfc8471/),
verified 2026-08-02). RFC 8473, *Token Binding over HTTP*, was published in
the same month and describes the `Sec-Token-Binding` HTTP request header for
carrying Token Binding messages in HTTP
([https://www.rfc-editor.org/info/rfc8473/](https://www.rfc-editor.org/info/rfc8473/),
verified 2026-08-02).

**DPoP** means Demonstrating Proof of Possession. RFC 9449, *OAuth 2.0
Demonstrating Proof of Possession (DPoP)*, was published in September 2023 by
Daniel Fett, Brian Campbell, John Bradley, Torsten Lodderstedt, Michael Jones,
and David Waite. It standardizes an application-layer method for
sender-constraining OAuth access tokens and refresh tokens using a DPoP proof
JWT in an HTTP header
([https://www.rfc-editor.org/info/rfc9449/](https://www.rfc-editor.org/info/rfc9449/),
verified 2026-08-02).

The broader vocabulary includes **proof-of-possession token**, **PoP token**,
**holder-of-key token**, **key-bound token**, and **sender-constrained token**.
RFC 7800 defines JWT proof-of-possession key semantics through the `cnf`
confirmation claim
([https://www.rfc-editor.org/info/rfc7800/](https://www.rfc-editor.org/info/rfc7800/),
verified 2026-08-02). RFC 9700, the OAuth 2.0 security best current practice,
uses the phrase sender-constrained access token and names mutual TLS and DPoP
as methods for token replay prevention
([https://www.rfc-editor.org/info/rfc9700/](https://www.rfc-editor.org/info/rfc9700/),
verified 2026-08-02).

This entry uses **Token Binding** as the architectural idea and **DPoP** as the
current OAuth application-layer realization. It does not claim that the older
HTTP Token Binding protocol is the preferred deployment path. Chromium's 2018
Intent to Remove thread said Token Binding had not shipped by default in
Chrome and cited low adoption as part of the removal rationale
([https://groups.google.com/a/chromium.org/g/blink-dev/c/OkdLUyYmY1E](https://groups.google.com/a/chromium.org/g/blink-dev/c/OkdLUyYmY1E),
verified 2026-08-02). Engineering judgement. In new OAuth systems, the
decision is usually between DPoP and mutual TLS certificate-bound tokens, not
between DPoP and the old browser Token Binding stack.

## 2. Problem and context

Bearer tokens are convenient because a resource server can authorize a request
by checking the token. That same convenience is the core risk. RFC 6750 defines
a bearer token as a security token that any party in possession of it can use
without proving control of cryptographic key material
([https://www.rfc-editor.org/info/rfc6750/](https://www.rfc-editor.org/info/rfc6750/),
verified 2026-08-02). If an access token leaks through a log, browser bug,
misconfigured proxy, compromised resource server, mobile backup, extension, or
crash report, another process can replay it unless other controls stop the
request.

The context for this pattern is an OAuth or session-token system where the
token must cross a boundary that cannot be made fully trusted. The client asks
an authorization server for a token. The authorization server binds the token
to a public key or certificate. Later, the resource server accepts the token
only when the request carries a fresh proof made with the matching private key.
The token alone is no longer enough.

DPoP makes that proof at the HTTP application layer. The client signs a DPoP
proof JWT. The proof names the HTTP method through `htm`, the target URI
through `htu`, a unique proof identifier through `jti`, an issuance time
through `iat`, and, when the request carries an access token, the access-token
hash through `ath`. The proof header carries a public JWK. The resource server
verifies the proof signature, checks that the request matches the proof, checks
replay state, checks that the proof key thumbprint matches the token's
confirmation claim, and only then lets authorization policy read the token.
Those proof fields and validation rules are specified in RFC 9449 sections 4
and 7
([https://www.rfc-editor.org/info/rfc9449/](https://www.rfc-editor.org/info/rfc9449/),
verified 2026-08-02).

Mutual TLS certificate-bound access tokens solve the same replay problem at a
different layer. RFC 8705 defines OAuth mutual-TLS client authentication and
certificate-bound access tokens, including resource-server validation that the
certificate used on the TLS connection matches the certificate associated with
the access token
([https://www.rfc-editor.org/rfc/rfc8705.html](https://www.rfc-editor.org/rfc/rfc8705.html),
verified 2026-08-02). DPoP exists for cases where client certificates or TLS
layer binding are not practical, such as browser-based clients, mobile apps,
or deployments where the application cannot see the TLS client certificate.

## 3. Forces

Engineering judgement. These forces explain when the pattern earns its cost.

- **Replay resistance.** Favoured. A stolen token cannot be used from a
  different process unless the attacker also controls the bound private key or
  can make the legitimate client sign malicious requests.
- **Transport independence.** Favoured by DPoP. The proof is an HTTP header,
  so it can survive load balancers and service meshes that terminate TLS before
  the application. Mutual TLS favours stronger channel binding but binds the
  design to certificate plumbing.
- **Latency.** Sacrificed. Each protected request adds signature creation on
  the client and signature verification on the server. Nonce challenges can add
  a retry round trip.
- **State.** Sacrificed. Replay detection needs a `jti` cache, a nonce store,
  or both. Stateless bearer-token validation becomes partly stateful.
- **Client complexity.** Sacrificed. Clients now manage key generation, key
  storage, proof construction, nonce retry, and token-type handling.
- **Resource-server coupling.** Sacrificed. Resource servers must understand
  the token confirmation claim and the DPoP proof. They can no longer treat the
  access token as the only artifact.
- **Operability.** Sacrificed unless built in. A DPoP failure can come from
  clock skew, URI normalization, a bad hash, stale nonce, unsupported
  algorithm, duplicate `jti`, or a key mismatch. Operators need labels that
  separate those causes.
- **Privacy.** Mixed. Binding reduces stolen-token blast radius, but stable
  keys can become correlation handles if scoped too broadly. RFC 8471 discusses
  privacy limits for Token Binding keys and says key scope should not be
  broader than token scope
  ([https://www.rfc-editor.org/info/rfc8471/](https://www.rfc-editor.org/info/rfc8471/),
  verified 2026-08-02).
- **Team topology.** Mixed. A platform identity team can publish one proof
  contract, but every API team must enforce it consistently. Partial rollout
  creates confusing failures when one resource server accepts bearer tokens and
  another requires DPoP.

The pattern favours replay resistance and defense in depth. It sacrifices the
simplicity that made bearer tokens attractive.

## 4. Applicability and non-applicability

Reach for Token Binding and DPoP when the following hold.

- Access tokens or refresh tokens protect high-value operations and replay from
  a different device, process, or resource server is in the threat model.
- Public clients need stronger protection than bearer tokens but cannot keep a
  client secret. RFC 9449 describes DPoP as usable for public clients and says
  DPoP is not client authentication by itself
  ([https://www.rfc-editor.org/info/rfc9449/](https://www.rfc-editor.org/info/rfc9449/),
  verified 2026-08-02).
- The deployment cannot rely on mutual TLS end to end, because TLS terminates
  before the application, certificates create user-experience or operations
  problems, or the client is a browser-based or mobile app.
- The authorization server and resource servers can share binding semantics,
  either through self-contained JWT access tokens with `cnf.jkt` or through
  introspection that returns the confirmation information.
- The team can operate replay storage and can tolerate a small validation state
  footprint per proof.
- The client has access to non-exportable or hard-to-export key storage. DPoP
  still works with software keys, but the payoff is larger when the private key
  cannot be copied with the token.
- Regulatory or ecosystem profiles require sender-constrained tokens. The FAPI
  2.0 Security Profile requires sender-constrained access tokens and permits
  either MTLS from RFC 8705 or DPoP from RFC 9449
  ([https://openid.net/specs/fapi-security-profile-2_0.html](https://openid.net/specs/fapi-security-profile-2_0.html),
  verified 2026-08-02).

Do NOT reach for it in these cases.

- **Low-value, low-risk APIs.** The replay store, nonce logic, and client key
  handling cost more than the protected operation warrants. Short-lived bearer
  tokens with narrow audiences may be the better control.
- **No resource-server enforcement.** Binding a token at issuance but accepting
  it as `Bearer` at the API is ceremony without protection. The resource server
  is where replay is stopped.
- **Clients cannot protect keys at all.** If the private key and token are
  exported together, DPoP only changes the attacker's request format. It can
  still help against accidental token leakage, but it does not stop full client
  compromise.
- **XSS is the dominant browser threat and remains untreated.** RFC 9449 says
  script running inside the browser client can use the signing key through the
  legitimate context, so DPoP is not a substitute for preventing XSS
  ([https://www.rfc-editor.org/info/rfc9449/](https://www.rfc-editor.org/info/rfc9449/),
  verified 2026-08-02).
- **Every hop already requires mutual TLS with stable client certificate
  identity.** RFC 8705 certificate-bound tokens may be simpler because the proof
  is already in the TLS layer
  ([https://www.rfc-editor.org/rfc/rfc8705.html](https://www.rfc-editor.org/rfc/rfc8705.html),
  verified 2026-08-02).
- **The API gateway strips or rewrites the target URI without a canonical form
  contract.** DPoP validation compares `htu` and `htm` with the received
  request. Unstable canonicalization causes false rejects or accidental accepts.
- **Replay storage cannot be made shared across validating nodes.** Per-node
  caches let the same proof succeed once on each node unless routing pins all
  requests for a proof key to the same validator.
- **The client ecosystem cannot be upgraded.** A server that turns on DPoP for
  old clients without capability negotiation creates an outage.
- **The token is sent in URLs.** RFC 6750 warns against passing bearer tokens in
  page URLs because URLs leak through logs and history
  ([https://www.rfc-editor.org/info/rfc6750/](https://www.rfc-editor.org/info/rfc6750/),
  verified 2026-08-02). Binding does not make URL transport acceptable.

## 5. Structure

The participants are named by security role, not by class name.

- **Authorization Server.** Receives the token request. It validates the first
  DPoP proof when DPoP is used at the token endpoint. It binds the issued token
  to the proof key, usually by placing the JWK thumbprint in a `cnf.jkt` claim
  or making that value available through introspection. RFC 7638 defines JWK
  thumbprint computation
  ([https://www.rfc-editor.org/info/rfc7638/](https://www.rfc-editor.org/info/rfc7638/),
  verified 2026-08-02).
- **DPoP Client.** Owns the private key. It creates a fresh proof for the token
  request and for each protected resource request. It stores the nonce supplied
  by a server when nonce mode is used.
- **Bound Access Token.** Carries ordinary authorization claims plus a
  confirmation value that identifies the bound key. In DPoP this is commonly
  the `cnf.jkt` JWK thumbprint. In mutual TLS it can be a certificate thumbprint
  such as `x5t#S256` under `cnf`, as specified by RFC 8705
  ([https://www.rfc-editor.org/rfc/rfc8705.html](https://www.rfc-editor.org/rfc/rfc8705.html),
  verified 2026-08-02).
- **DPoP Proof JWT.** A short-lived signed JWT sent in the `DPoP` HTTP header.
  Its JOSE header carries `typ`, `alg`, and the public `jwk`. Its claims bind
  the proof to the request method, target URI, issuance time, unique proof ID,
  optional nonce, and access-token hash where required.
- **Resource Server.** Verifies both token and proof. It checks signature,
  method, URI, access-token hash, nonce, replay state, and key binding before
  running business authorization.
- **Replay Store.** Records accepted proof identifiers for their validity
  window. It rejects reuse. A distributed store is needed when validation runs
  on more than one node without sticky routing.
- **Nonce Issuer.** Optional but common in stronger deployments. It challenges
  stale or nonce-free proofs with a server-provided value. RFC 9449 section 8
  defines the nonce mechanism
  ([https://www.rfc-editor.org/info/rfc9449/](https://www.rfc-editor.org/info/rfc9449/),
  verified 2026-08-02).

The important relationship is two-step binding. First, the token issuer binds
the token to the public key. Second, the resource server checks a fresh proof
from the private key holder before accepting the token.

## 6. ASCII structure diagram

```
+-------------+
| DPoP Client |
| private key |
| nonce cache |
+-------------+
     | proof at token request
     v
+----------------------+
| Authorization Server |
| cnf.jkt issuer       |
+----------------------+
     | returns a DPoP access token
     v
(client now holds the token, back to DPoP Client)

DPoP Client sends a protected request:
  Authorization: DPoP <token>
  DPoP: <proof jwt>

+-----------------+
| Resource Server |
| proof verifier  |
| binding checker |
| replay checker  |
+-----------------+
     | token claims or introspection
     v
+------------------------+
| Token Metadata or JWKS |
+------------------------+

Resource Server also records jti, key, time to:

+--------------+
| Replay Store |
+--------------+

The token says which public key is bound. The proof
shows the caller holds the matching private key for
this HTTP request.
```

## 7. Dynamics

The flow has two phases. Issuance creates the binding. Resource access proves
that the presenter still controls the bound key.

```text
Client          Authorization Server       Resource Server       Replay Store
  |                      |                         |                    |
  | make key pair        |                         |                    |
  | sign proof           |                         |                    |
  | DPoP header          |                         |                    |
  |--------------------->|                         |                    |
  |                      | verify proof            |                    |
  |                      | compute JWK thumbprint  |                    |
  |                      | issue cnf.jkt token     |                    |
  |<---------------------|                         |                    |
  |                      |                         |                    |
  | sign proof for GET /accounts                  |                    |
  | Authorization: DPoP token                     |                    |
  | DPoP: proof with htm, htu, iat, jti, ath      |                    |
  |---------------------------------------------->|                    |
  |                      |                         | verify token       |
  |                      |                         | verify proof sig   |
  |                      |                         | htm and htu match  |
  |                      |                         | ath matches token  |
  |                      |                         | cnf.jkt matches    |
  |                      |                         |---- put jti ------>|
  |                      |                         |<- accepted --------|
  |<----------------------------------------------| allow request      |
  |                      |                         |                    |
  | replay same proof                              |                    |
  |---------------------------------------------->|                    |
  |                      |                         |---- put jti ------>|
  |                      |                         |<- duplicate -------|
  |<----------------------------------------------| 401 invalid_token  |
```

Nonce dynamics add one branch. A server may reject a request with
`use_dpop_nonce` and a `DPoP-Nonce` response header. The client then signs a
new proof that includes the nonce claim and retries. Okta documents this
server-provided nonce flow for its DPoP guide
([https://developer.okta.com/docs/guides/dpop/-/main/](https://developer.okta.com/docs/guides/dpop/-/main/),
verified 2026-08-02).

## 8. Implementation variants

**DPoP-bound OAuth access tokens.** This is the main variant for public clients
and API clients that cannot use client certificates. The proof is a JWT in the
`DPoP` header. The access token is sent with the `DPoP` authorization scheme,
not `Bearer`, when the resource server enforces DPoP. RFC 9449 specifies this
scheme
([https://www.rfc-editor.org/info/rfc9449/](https://www.rfc-editor.org/info/rfc9449/),
verified 2026-08-02). Trade-off. Application code must verify JWT proofs and
operate replay state.

**DPoP with server-provided nonces.** The server challenges proofs that lack a
fresh nonce. This reduces the value of precomputed proofs and lets the server
tighten freshness without trusting client clocks alone. Trade-off. The first
request can fail and retry, and clients must persist nonce state per issuer or
resource server.

**Mutual TLS certificate-bound tokens.** RFC 8705 binds tokens to a TLS client
certificate and requires the resource server to compare the presented
certificate with the token binding
([https://www.rfc-editor.org/rfc/rfc8705.html](https://www.rfc-editor.org/rfc/rfc8705.html),
verified 2026-08-02). Trade-off. The cryptographic proof is strong and handled
by TLS, but certificate lifecycle, proxy forwarding, and client UX become part
of the API security design.

**Legacy HTTP Token Binding.** RFC 8471 and RFC 8473 define a TLS-associated
Token Binding protocol and HTTP header
([https://www.rfc-editor.org/info/rfc8471/](https://www.rfc-editor.org/info/rfc8471/),
verified 2026-08-02;
[https://www.rfc-editor.org/info/rfc8473/](https://www.rfc-editor.org/info/rfc8473/),
verified 2026-08-02). Trade-off. It is useful lineage for the pattern, but
browser deployment did not become the common path. Engineering judgement. Treat
it as prior art unless your platform stack already exposes it.

**Private-key JWT client authentication plus DPoP.** A confidential client can
authenticate to the authorization server with one key and bind tokens to a DPoP
proof key. RFC 9449 says DPoP can be used regardless of client authentication
method and is not itself client authentication
([https://www.rfc-editor.org/info/rfc9449/](https://www.rfc-editor.org/info/rfc9449/),
verified 2026-08-02). Trade-off. Separating authentication and token binding
avoids overloading one key, but key inventory doubles.

**Gateway verification.** An API gateway validates the proof and passes a
trusted internal header or claims object to services. Trade-off. This reduces
duplicated library work, but every service must reject direct traffic that
bypasses the gateway. The internal header must be stripped at the edge before
the gateway adds its own value.

**Library-side proof generation.** SDKs hide proof construction and nonce
retry. Trade-off. Client developers make fewer protocol mistakes, but debugging
requires library events that expose nonce, algorithm, and binding failures
without logging tokens or private material.

## 9. Known production uses

**Okta custom authorization servers.** Okta documents configuration for OAuth
2.0 DPoP, including the client setting
`dpop_bound_access_tokens: true`, nonce handling, the `DPoP` authorization
scheme at a protected resource, and resource-server comparison of token `jkt`
with the DPoP header key thumbprint
([https://developer.okta.com/docs/guides/dpop/-/main/](https://developer.okta.com/docs/guides/dpop/-/main/),
verified 2026-08-02).

**Curity Identity Server.** Curity documents DPoP for its Identity Server and
states that version 11.4 implements RFC 9449 for all client types. Its docs
show `token_type: "DPoP"`, `cnf.jkt`, server-provided nonces, and protected
endpoints such as userinfo, SCIM, and GraphQL APIs accepting DPoP-bound access
tokens
([https://curity.io/docs/identity-server/profiles/token-profile/clients/client-config/dpop/](https://curity.io/docs/identity-server/profiles/token-profile/clients/client-config/dpop/),
verified 2026-08-02).

**Duende IdentityServer.** Duende documents Proof-of-Possession access tokens
and says DPoP is supported from version 6.3. The documentation shows the
`RequireDPoP` client setting, `cnf.jkt` in access tokens, and URL comparison
rules for `htu`
([https://docs.duendesoftware.com/identityserver/tokens/pop/](https://docs.duendesoftware.com/identityserver/tokens/pop/),
verified 2026-08-02).

**Auth0 enterprise connections.** Auth0 documents configuring DPoP for Okta and
OIDC enterprise connections, including dashboard configuration, Management API
configuration through `dpop_signing_alg`, discovery of
`dpop_signing_alg_values_supported`, and log fields that confirm DPoP-bound
userinfo calls
([https://auth0.com/docs/authenticate/enterprise-connections/enable-dpop-enterprise-connections](https://auth0.com/docs/authenticate/enterprise-connections/enable-dpop-enterprise-connections),
verified 2026-08-02).

## 10. Consequences

Engineering judgement.

Positive.

- Stolen access tokens are less useful because replay requires the matching
  private key or an ability to make the legitimate client sign requests.
- Resource servers get a cryptographic signal that the token presenter matches
  the token binding, not only that the token validates.
- Access tokens can remain opaque or self-contained as long as the binding
  metadata is available to the resource server.
- Public clients gain a sender constraint without client secrets.
- Nonce mode gives servers a way to force recent proof construction.
- Binding failures create a measurable security signal that can reveal token
  theft attempts, bad SDKs, and misrouted traffic.

Negative.

- Every protected request is heavier. There is one proof signature and one
  proof verification, plus token validation.
- Validation becomes partly stateful because replay detection needs memory of
  recent `jti` values.
- URI canonicalization bugs cause outages. The proof and request must agree on
  what URI is being protected.
- Client-side key lifecycle becomes product logic. Rotation, loss, backup, and
  device migration need explicit decisions.
- API teams now share a cross-cutting security contract. If one service skips
  proof validation, the weakest service can become the replay target.
- XSS and malware inside the legitimate client context are not solved. The
  attacker can ask the real client to sign.

## 11. Failure modes and misuse

Engineering judgement. Each entry names an observable symptom, likely cause,
and fix.

**Bearer fallback stays enabled.** Symptom. Requests with
`Authorization: Bearer` still succeed for an API that was meant to require
DPoP. Cause. The gateway or resource server validates the token but does not
enforce the `DPoP` authorization scheme and proof header. Fix. Reject bearer
scheme for clients or audiences configured as DPoP-bound, and add a canary test
that sends a valid token without a proof.

**Replay cache is local to each node.** Symptom. The same proof succeeds once
per API pod during a load test, then starts failing as duplicates. Cause.
Replay state is stored in process memory while requests are load-balanced
across validators. Fix. Use a shared store, deterministic routing by proof key,
or gateway-level validation before fanout.

**URI mismatch behind a proxy.** Symptom. Valid clients receive intermittent
`invalid_dpop_proof` errors after a load balancer or route rewrite change.
Cause. The client signs the public URL while the application validates against
an internal host, scheme, or path. Fix. Define the canonical external URI at
the gateway and pass it through a trusted request attribute that validators use.

**Access-token hash missing.** Symptom. Token endpoint calls work, but resource
requests fail with an `ath` claim error. Cause. The client reused token-request
proof code for resource requests and omitted the access-token hash. Fix. Split
proof builders by endpoint type and require `ath` whenever an access token is
present.

**Algorithm confusion.** Symptom. Proofs signed with an unexpected algorithm
pass in one environment and fail in another. Cause. A JWT library accepts the
algorithm from the JOSE header instead of enforcing a configured allowlist. Fix.
Pin acceptable asymmetric algorithms and reject `none` and symmetric MAC
algorithms for DPoP. RFC 8725 requires callers to specify supported algorithms
for JWT cryptographic operations
([https://www.rfc-editor.org/info/rfc8725/](https://www.rfc-editor.org/info/rfc8725/),
verified 2026-08-02).

**Nonce retry loop.** Symptom. Clients alternate between `use_dpop_nonce` and
new proofs until they hit retry limits. Cause. The client stores the nonce
under the wrong issuer, resource origin, or tenant key, or a proxy strips the
`DPoP-Nonce` response header. Fix. Scope nonce caches by issuer and resource
server, preserve the nonce response header, and log nonce age without logging
the nonce value.

**Key rotation breaks refresh.** Symptom. Access works until refresh, then the
authorization server rejects the refresh-token request. Cause. The refresh
token is bound to the old proof key and the client discarded that key before
using or rotating the refresh token. Fix. Keep the old key until bound refresh
tokens expire or provide an explicit rebind flow.

**Binding checked after authorization.** Symptom. Business logs show denied
actions or side effects for requests that later fail DPoP validation. Cause.
The service parses and acts on token claims before proof validation finishes.
Fix. Make proof validation part of authentication middleware and expose claims
only after all proof checks pass.

**Stable key over-scoped.** Symptom. Privacy review flags that the same public
key thumbprint appears across unrelated relying parties. Cause. A client uses
one long-lived key for all issuers and audiences. Fix. Scope keys to issuer,
client, device, and audience policy, and rotate according to token sensitivity.

## 12. Trade-off matrix

| Force | DPoP-bound token | MTLS certificate-bound token | Bearer token with short TTL | Audience-restricted bearer token | HTTP Message Signatures |
|---|---|---|---|---|---|
| Replay resistance after token theft | Strong if key is not stolen | Strong if certificate key is not stolen | Limited to token lifetime | Good only outside intended audience | Strong for signed requests, token binding is separate |
| Public-client fit | Good | Often poor in browsers | Good | Good | Mixed, key handling still needed |
| TLS proxy compatibility | Good | Hard unless certificate data is trusted through the proxy | Good | Good | Good |
| Per-request cost | JWT signing and verification | TLS client auth plus token check | Low | Low | Signing and verification |
| Server-side state | Replay cache and optional nonce | Usually lower at application layer | None beyond token validation | None beyond token validation | Replay defense needed if freshness is enforced |
| Client operations | Key pair, nonce, proof builder | Certificate issuance and renewal | Token storage | Token storage and audience selection | Key pair and signature builder |
| Standard OAuth fit | RFC 9449 | RFC 8705 | RFC 6750 | OAuth JWT or introspection profiles | RFC 9421 signs HTTP messages, not OAuth binding by itself |
| Best for | Public clients and APIs behind proxies | Enterprise server-to-server with certificate infrastructure | Low-risk APIs | Preventing cross-resource replay | Non-OAuth request authenticity |
| Failure clarity | Many protocol-specific errors | Certificate and TLS errors plus token errors | Simple expiry errors | Audience errors | Signature-base errors |

Reading the table. DPoP is the strongest fit when the client can hold a private
key but cannot use mutual TLS cleanly. Mutual TLS wins in controlled
server-to-server networks with certificate operations already in place. Short
TTL bearer tokens reduce exposure time but do not change bearer semantics.
Audience restriction blocks replay to the wrong resource, but the right
resource can still replay unless sender-constrained. HTTP Message Signatures
sign requests and can compose with tokens, but they do not define OAuth token
confirmation semantics by themselves.

## 13. Related and incompatible patterns

- **Bearer Token.** The pattern replaces pure bearer semantics. DPoP still
  carries an access token, but the token is no longer sufficient by itself.
- **Mutual TLS.** A sibling sender-constraining pattern. RFC 9700 names both
  mutual TLS and DPoP as token replay prevention mechanisms
  ([https://www.rfc-editor.org/info/rfc9700/](https://www.rfc-editor.org/info/rfc9700/),
  verified 2026-08-02).
- **Proof Key for Code Exchange.** PKCE protects the authorization-code
  exchange. DPoP protects later token presentation. They compose because they
  cover different replay points.
- **JWT Confirmation Claim.** The `cnf` claim is the token-side binding
  carrier. RFC 7800 defines proof-of-possession key semantics for JWTs
  ([https://www.rfc-editor.org/info/rfc7800/](https://www.rfc-editor.org/info/rfc7800/),
  verified 2026-08-02).
- **Replay Cache.** A required companion when validating `jti` uniqueness. The
  cache is part of the security boundary, not an optimization.
- **Nonce.** A companion freshness pattern. A server-provided nonce limits
  precomputed proof usefulness and reduces dependence on client clocks.
- **HTTP Message Signatures.** Related at the HTTP layer. RFC 9421 standardizes
  signatures over selected HTTP components
  ([https://www.rfc-editor.org/info/rfc9421/](https://www.rfc-editor.org/info/rfc9421/),
  verified 2026-08-02). DPoP is narrower and OAuth-specific.
- **Token in URL.** Incompatible. Binding does not repair leakage through
  browser history, referer headers, and logs.
- **Shared Client Secret in Public Client.** Incompatible. DPoP uses asymmetric
  proof for public clients because a shared secret embedded in a public client
  cannot remain secret.
- **Service Locator for Security Context.** Conflicts in practice. Proof
  validation must be explicit in the request pipeline. Hidden global access to a
  partially validated token makes ordering bugs more likely.

## 14. Refactoring path in and out

Introducing DPoP into a bearer-token API.

1. Inventory clients, token issuers, resource servers, gateways, and SDKs that
   touch the protected audience.
2. Add token metadata support. For JWT access tokens, add `cnf.jkt`. For opaque
   tokens, extend introspection to return the binding value.
3. Add a DPoP proof verifier that runs before authorization policy. It should
   parse the proof, enforce the allowed algorithm list, verify signature,
   compare `htm` and `htu`, check `iat`, check `ath`, compare `cnf.jkt`, and
   record `jti`.
4. Put the verifier in report-only mode for selected clients. Log reject
   reasons and compare with successful bearer traffic.
5. Update SDKs to generate per-request proofs and handle nonce challenges.
6. Turn on DPoP-bound token issuance for a small client set. Keep bearer tokens
   for other clients during migration, but never issue one token that can be
   accepted as both bearer and DPoP for the same audience.
7. Require the `DPoP` authorization scheme for bound clients. Reject missing
   proof, duplicate proof, bad `ath`, and key mismatch.
8. Add operational runbooks for nonce retry loops, URI mismatch, and replay
   cache failure.
9. Remove bearer fallback after clients have moved and metrics show no valid
   bearer traffic for that audience.

Removing the pattern when it stops earning its place.

1. Confirm that replay risk is now handled by another named control, such as
   mutual TLS certificate-bound tokens, or that the protected operation no
   longer requires sender-constraining.
2. Stop issuing new DPoP-bound tokens for the client cohort and shorten the
   lifetime of outstanding bound tokens.
3. Keep resource-server DPoP validation until all bound access tokens and
   refresh tokens have expired or been revoked.
4. Remove SDK proof generation only after servers no longer challenge for DPoP.
5. Delete replay-store keys after their retention window. Do not delete
   security logs that may be needed for incident review.
6. Simplify authorization middleware so token parsing and authentication order
   remain clear after proof checks disappear. Cross reference Inline Function
   and Remove Dead Code in the refactoring family.

## 15. Testing and verification

Engineering judgement.

Unit tests should cover the proof validation decision table. A valid proof must
pass only when every condition is true: supported asymmetric algorithm,
signature verified with the header JWK, `typ` is `dpop+jwt`, method matches,
canonical URI matches, `iat` is inside skew, `jti` has not been seen, `ath`
matches the access token, and token binding matches the JWK thumbprint.

Contract tests should run against every resource server that accepts the same
audience. The same invalid proof corpus should produce the same class of
reject at the gateway, at a service, and at a local developer server. Include
cases for lowercase HTTP methods, query strings, default ports, encoded path
segments, missing `ath`, wrong `ath`, duplicate `jti`, old `iat`, future `iat`,
bad nonce, missing nonce, and mismatched `cnf.jkt`.

Integration tests should include the token endpoint and resource endpoint. The
test client should request a DPoP-bound token, call a resource, replay the same
proof, call the resource with a new proof signed by another key, and call the
resource with the right key but wrong method. Only the first resource call
should succeed.

Property tests are useful for canonicalization. Generate URLs with case,
default ports, query strings, percent encoding, and forwarded host data. The
validator should accept only the canonical form agreed for the deployment.

Negative security tests matter more than happy-path tests. A bearer-only request
with a valid bound token must fail. A DPoP proof without a token must not create
an authenticated user. A valid proof over one access token must fail with a
different access token because the `ath` claim changes.

## 16. Observability signals

Engineering judgement.

Record these signals at the validator boundary.

- Count accepted and rejected DPoP validations by client ID, audience, issuer,
  resource server, and reject reason.
- Count bearer fallback attempts for clients configured as DPoP-bound.
- Measure proof verification duration by algorithm.
- Count duplicate `jti` rejections. Split first seen on same node from first
  seen in the shared replay store when possible.
- Count nonce challenges, nonce retries, stale nonce rejects, and missing nonce
  rejects.
- Count `htu` and `htm` mismatches, with a safe route template label rather
  than raw URLs.
- Count `ath` mismatches without logging tokens or token hashes.
- Count binding mismatches where token `cnf.jkt` does not match the proof JWK
  thumbprint.
- Track replay-store latency, error rate, and eviction count.

A healthy deployment has a stable low reject rate, near-zero bearer fallback
for DPoP clients, replay-store latency well below request latency, and nonce
challenge rates that match the configured nonce lifetime. DPoP validation
duration should be visible but not dominate endpoint latency.

A failing deployment often shows one sharp label. A spike in `htu_mismatch`
after a routing release points to proxy canonicalization. A spike in
`invalid_ath` after an SDK release points to proof-builder reuse. A spike in
`duplicate_jti` from many IP addresses can indicate replay of captured proofs.
A sudden drop in DPoP traffic with a rise in bearer attempts can mean clients
lost DPoP configuration.

## 17. Security and privacy implications

This pattern closes one specific attack surface: replay of a stolen token by a
party that does not also control the proof key. RFC 9449 states that DPoP is a
defense in depth for token leakage and must be used with HTTPS
([https://www.rfc-editor.org/info/rfc9449/](https://www.rfc-editor.org/info/rfc9449/),
verified 2026-08-02). It is not a replacement for TLS, audience restriction,
authorization checks, token expiry, XSS prevention, or device security.

Private keys become high-value assets. A non-exportable key in a platform
keystore, WebCrypto key, secure enclave, TPM, or HSM gives stronger protection
than a PEM file next to the token cache. Engineering judgement. If the key and
token can be copied together by the expected attacker, this pattern may still
reduce accidental replay but should not be sold as strong compromise
containment.

Replay stores are security infrastructure. If they fail open, repeated proofs
can pass. If they fail closed, valid traffic can stop. The store needs capacity
planning, expiry, and alarms. The value stored should be a digest or tuple that
does not reveal tokens or private keys.

Header trust is part of the boundary. If a gateway verifies DPoP and forwards
identity to services, it must remove inbound internal-auth headers before
adding its own. Services must reject direct traffic or repeat verification.

Privacy depends on key scope. A stable JWK thumbprint reused across unrelated
issuers can correlate a client across contexts. RFC 8471 says Token Binding key
scope should not be broader than token scope
([https://www.rfc-editor.org/info/rfc8471/](https://www.rfc-editor.org/info/rfc8471/),
verified 2026-08-02). Engineering judgement. For DPoP, scope proof keys by
issuer, client installation, and audience unless a narrower or broader scope is
explicitly approved.

Logs must avoid token material. Do not log access tokens, proof JWTs, nonce
values, private keys, or full public JWKs. Log thumbprints, key IDs, route
templates, reject categories, and correlation IDs.

## Code examples

The examples model the resource-server check after JWT signature verification
and token validation have already produced trusted claim objects. They focus on
binding, freshness, method, URI, access-token hash, and replay behavior. This
keeps the samples runnable without framework scaffolding.

TypeScript, runnable with `npx tsc` and `node`.

```typescript
const { createHash } = require("node:crypto");

type Proof = {
  htm: string;
  htu: string;
  iat: number;
  jti: string;
  ath: string;
  jkt: string;
};

type Token = {
  value: string;
  cnf: { jkt: string };
};

class ReplayStore {
  private seen = new Set<string>();

  remember(key: string): boolean {
    if (this.seen.has(key)) return false;
    this.seen.add(key);
    return true;
  }
}

function base64url(bytes: { toString: (encoding: string) => string }): string {
  return bytes.toString("base64url");
}

function accessTokenHash(token: string): string {
  return base64url(createHash("sha256").update(token).digest());
}

function authorize(
  method: string,
  uri: string,
  token: Token,
  proof: Proof,
  now: number,
  replay: ReplayStore
): boolean {
  if (proof.htm !== method.toUpperCase()) return false;
  if (proof.htu !== uri) return false;
  if (Math.abs(now - proof.iat) > 300) return false;
  if (proof.ath !== accessTokenHash(token.value)) return false;
  if (proof.jkt !== token.cnf.jkt) return false;
  return replay.remember(`${proof.jkt}:${proof.jti}`);
}

const token: Token = { value: "access-token", cnf: { jkt: "key-thumbprint" } };
const proof: Proof = {
  htm: "GET",
  htu: "https://api.example.test/accounts",
  iat: 1_700_000_000,
  jti: "proof-1",
  ath: accessTokenHash("access-token"),
  jkt: "key-thumbprint",
};

const replay = new ReplayStore();
console.log(authorize("GET", proof.htu, token, proof, 1_700_000_001, replay));
console.log(authorize("GET", proof.htu, token, proof, 1_700_000_001, replay));
```

Python, runnable with `python3`.

```python
import base64
import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class Proof:
    htm: str
    htu: str
    iat: int
    jti: str
    ath: str
    jkt: str


@dataclass(frozen=True)
class Token:
    value: str
    jkt: str


class ReplayStore:
    def __init__(self) -> None:
        self.seen: set[str] = set()

    def remember(self, key: str) -> bool:
        if key in self.seen:
            return False
        self.seen.add(key)
        return True


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def token_hash(token: str) -> str:
    return b64url(hashlib.sha256(token.encode()).digest())


def authorize(method: str, uri: str, token: Token, proof: Proof,
              now: int, replay: ReplayStore) -> bool:
    if proof.htm != method.upper():
        return False
    if proof.htu != uri:
        return False
    if abs(now - proof.iat) > 300:
        return False
    if proof.ath != token_hash(token.value):
        return False
    if proof.jkt != token.jkt:
        return False
    return replay.remember(f"{proof.jkt}:{proof.jti}")


token = Token("access-token", "key-thumbprint")
proof = Proof(
    "GET",
    "https://api.example.test/accounts",
    1_700_000_000,
    "proof-1",
    token_hash("access-token"),
    "key-thumbprint",
)
store = ReplayStore()
print(authorize("GET", proof.htu, token, proof, 1_700_000_001, store))
print(authorize("GET", proof.htu, token, proof, 1_700_000_001, store))
```

Go, runnable with `go run`.

```go
package main

import (
	"crypto/sha256"
	"encoding/base64"
	"fmt"
	"strings"
)

type Proof struct {
	Htm string
	Htu string
	Iat int64
	Jti string
	Ath string
	Jkt string
}

type Token struct {
	Value string
	Jkt   string
}

type ReplayStore struct {
	seen map[string]bool
}

func (r *ReplayStore) Remember(key string) bool {
	if r.seen[key] {
		return false
	}
	r.seen[key] = true
	return true
}

func tokenHash(token string) string {
	sum := sha256.Sum256([]byte(token))
	return base64.RawURLEncoding.EncodeToString(sum[:])
}

func authorize(method, uri string, token Token, proof Proof, now int64,
	replay *ReplayStore) bool {
	if proof.Htm != strings.ToUpper(method) {
		return false
	}
	if proof.Htu != uri {
		return false
	}
	if now-proof.Iat > 300 || proof.Iat-now > 300 {
		return false
	}
	if proof.Ath != tokenHash(token.Value) {
		return false
	}
	if proof.Jkt != token.Jkt {
		return false
	}
	return replay.Remember(proof.Jkt + ":" + proof.Jti)
}

func main() {
	token := Token{Value: "access-token", Jkt: "key-thumbprint"}
	proof := Proof{
		Htm: "GET",
		Htu: "https://api.example.test/accounts",
		Iat: 1700000000,
		Jti: "proof-1",
		Ath: tokenHash("access-token"),
		Jkt: "key-thumbprint",
	}
	replay := &ReplayStore{seen: map[string]bool{}}
	fmt.Println(authorize("GET", proof.Htu, token, proof, 1700000001, replay))
	fmt.Println(authorize("GET", proof.Htu, token, proof, 1700000001, replay))
}
```

## 18. References

- Daniel Fett, Brian Campbell, John Bradley, Torsten Lodderstedt, Michael
  Jones, David Waite. RFC 9449, *OAuth 2.0 Demonstrating Proof of Possession
  (DPoP)*, September 2023. Sections 1, 2, 4, 7, 8, and 11.
  [https://www.rfc-editor.org/info/rfc9449/](https://www.rfc-editor.org/info/rfc9449/),
  verified 2026-08-02.
- Andrei Popov, Magnus Nystroem, Dirk Balfanz, Jeff Hodges. RFC 8471, *The
  Token Binding Protocol Version 1.0*, October 2018. Sections 1, 2, 5, 7, and
  8.
  [https://www.rfc-editor.org/info/rfc8471/](https://www.rfc-editor.org/info/rfc8471/),
  verified 2026-08-02.
- Andrei Popov, Magnus Nystroem, Dirk Balfanz, Nick Harper, Jeff Hodges. RFC
  8473, *Token Binding over HTTP*, October 2018. Sections 1 and 2.
  [https://www.rfc-editor.org/info/rfc8473/](https://www.rfc-editor.org/info/rfc8473/),
  verified 2026-08-02.
- Brian Campbell, John Bradley, Nat Sakimura, Torsten Lodderstedt. RFC 8705,
  *OAuth 2.0 Mutual-TLS Client Authentication and Certificate-Bound Access
  Tokens*, February 2020. Sections 2, 3, 4, and 7.
  [https://www.rfc-editor.org/rfc/rfc8705.html](https://www.rfc-editor.org/rfc/rfc8705.html),
  verified 2026-08-02.
- Michael Jones, Dick Hardt. RFC 6750, *The OAuth 2.0 Authorization Framework:
  Bearer Token Usage*, October 2012. Sections 1, 2, and 5.
  [https://www.rfc-editor.org/info/rfc6750/](https://www.rfc-editor.org/info/rfc6750/),
  verified 2026-08-02.
- Michael Jones, Nat Sakimura. RFC 7638, *JSON Web Key (JWK) Thumbprint*,
  September 2015. Section 3.
  [https://www.rfc-editor.org/info/rfc7638/](https://www.rfc-editor.org/info/rfc7638/),
  verified 2026-08-02.
- Michael Jones, John Bradley, Hannes Tschofenig. RFC 7800,
  *Proof-of-Possession Key Semantics for JSON Web Tokens (JWTs)*, April 2016.
  Sections 1 and 3.
  [https://www.rfc-editor.org/info/rfc7800/](https://www.rfc-editor.org/info/rfc7800/),
  verified 2026-08-02.
- Yaron Sheffer, Dick Hardt, Michael Jones. RFC 8725, *JSON Web Token Best
  Current Practices*, February 2020. Section 3.
  [https://www.rfc-editor.org/info/rfc8725/](https://www.rfc-editor.org/info/rfc8725/),
  verified 2026-08-02.
- Torsten Lodderstedt, John Bradley, Andrii Labunets, Daniel Fett. RFC 9700,
  *Best Current Practice for OAuth 2.0 Security*, January 2025. Section 2.2.
  [https://www.rfc-editor.org/info/rfc9700/](https://www.rfc-editor.org/info/rfc9700/),
  verified 2026-08-02.
- Okta Developer. *Configure OAuth 2.0 Demonstrating Proof-of-Possession*.
  [https://developer.okta.com/docs/guides/dpop/-/main/](https://developer.okta.com/docs/guides/dpop/-/main/),
  verified 2026-08-02.
- Curity. *DPoP (Demonstrating Proof of Possession)*.
  [https://curity.io/docs/identity-server/profiles/token-profile/clients/client-config/dpop/](https://curity.io/docs/identity-server/profiles/token-profile/clients/client-config/dpop/),
  verified 2026-08-02.
- Duende Software. *Proof-of-Possession Access Tokens*.
  [https://docs.duendesoftware.com/identityserver/tokens/pop/](https://docs.duendesoftware.com/identityserver/tokens/pop/),
  verified 2026-08-02.
- Auth0. *Configure Enterprise Connections with Demonstrating
  Proof-of-Possession (DPoP)*.
  [https://auth0.com/docs/authenticate/enterprise-connections/enable-dpop-enterprise-connections](https://auth0.com/docs/authenticate/enterprise-connections/enable-dpop-enterprise-connections),
  verified 2026-08-02.
- OpenID Foundation. *FAPI 2.0 Security Profile*. Section 5.3.
  [https://openid.net/specs/fapi-security-profile-2_0.html](https://openid.net/specs/fapi-security-profile-2_0.html),
  verified 2026-08-02.
- Mark Nottingham, Poul-Henning Kamp, Lucas Pardue, Martin Thomson, Brian
  Campbell. RFC 9421, *HTTP Message Signatures*, February 2024. Sections 1 and
  2.
  [https://www.rfc-editor.org/info/rfc9421/](https://www.rfc-editor.org/info/rfc9421/),
  verified 2026-08-02.
- Nick Harper. *Intent to Remove: Token Binding*, blink-dev, August 2018.
  [https://groups.google.com/a/chromium.org/g/blink-dev/c/OkdLUyYmY1E](https://groups.google.com/a/chromium.org/g/blink-dev/c/OkdLUyYmY1E),
  verified 2026-08-02.
