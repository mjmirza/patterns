---
name: Access Token
slug: access-token
family: 10-microservices
category: Security
aliases: [Bearer Token, API Token, Security Token]
first_described: "IETF RFC 6749, D. Hardt (ed.), 2012"
maturity: canonical
related: [api-gateway, service-mesh, self-contained-service, audit-logging]
incompatible_with: []
verified: 2026-08-02
---

# Access Token

## 1. Name, aliases, and lineage

The canonical name in the microservices and API security literature is Access
Token. The term was standardized by the IETF in RFC 6749, "The OAuth 2.0
Authorization Framework", edited by D. Hardt and published October 2012.
Section 1.4 states the definition plainly. "Access tokens are credentials used
to access protected resources. An access token is a string representing an
authorization issued to the client" (RFC 6749 section 1.4, verified 2026-08-02,
https://datatracker.ietf.org/doc/html/rfc6749#section-1.4). The same section
notes the string is typically opaque to the client and represents a scope,
lifetime, and other access attributes enforced by the resource server and
authorization server, which is the property that makes an access token a
distinct pattern from a raw password or a long-lived API key.

Bearer Token is the alias used when the token's possession alone is
sufficient to use it, no proof of the holder's identity beyond presenting the
string is required. RFC 6750, "The OAuth 2.0 Authorization Framework. Bearer
Token Usage", defines this usage mode specifically, and it is the dominant
usage mode in production HTTP APIs, carried in the `Authorization: Bearer <token>` header. API Token and Security Token are the vendor-neutral
names used outside the OAuth specification family, for example a Stripe API key or a
GitHub personal access token, where the same string-credential-with-limited-
scope idea appears without an OAuth authorization server issuing it.

The pattern predates the RFC by more than a decade in informal practice.
Kerberos tickets (RFC 1510, 1993) and SAML assertions (OASIS SAML 1.0, 2002)
both carry an access-decision credential separate from the user's long-term
password, and both are properly understood as earlier instances of the same
underlying idea, a short-lived, scoped, verifiable credential that stands in
for re-proving identity on every call. RFC 6749 is cited here as the
"first described" source because it is the specification that fixed the term
"access token" as the name used across the microservices literature this
catalog documents, not because OAuth invented the underlying concept.

A precise boundary matters for this entry. An access token is a runtime
authorization credential presented on a call. It is not the same thing as a
long-lived database password, a TLS client certificate (a transport-layer
identity credential, see mutual TLS in the service mesh entry), or an API key
used purely as an unscoped, non-expiring secret with no issuing authority
behind it. Where a system calls something an "API key" but it is short-lived,
scoped, and independently verifiable, it is, for the purposes of this pattern,
an access token wearing a different name.

## 2. Problem and context

A microservice architecture replaces one perimeter, the monolith's process
boundary, with dozens or hundreds of network boundaries, one between every
pair of services that call each other, and one between every client and the
edge. Each of those boundaries is a place where the caller's authorization
must be checked before the call is allowed to proceed. The naive answer,
re-authenticating the caller with a username and password on every hop, is
both slow (a credential store round trip on every call) and dangerous (every
service in the call graph now has to be trusted with the caller's password).

The concrete situation looks like this in a real system. A mobile client signs
in once, with a password, biometric, or a social identity provider, at the
edge. From that point forward every request the client makes, and every
downstream call one internal service makes to another on the client's behalf,
needs to prove two things without re-running the login flow, who or what is
this request acting for, and what is it allowed to do. A service receiving a
call cannot see the login flow that happened minutes or hours earlier at the
edge. It needs a self-describing or independently verifiable artifact that
carries the answer to both questions, that was issued by something the
receiving service trusts, and that cannot be forged or replayed indefinitely.

The access token pattern is the answer. The client authenticates once,
receives a token, and presents that token on every subsequent call instead of
re-authenticating. Each receiving service validates the token, either by
checking its signature locally against a known key (a self-contained token,
typically a JWT) or by asking a trusted authority whether the token is still
valid (an opaque token validated by introspection, RFC 7662). Either way the
password or long-lived secret never travels past the point where it was first
exchanged for a token, and every downstream party sees only a bounded,
revocable, inspectable credential.

The context that makes this the right pattern, rather than an unnecessary
layer, has three parts. The system has more than one network hop between the
caller and the resource being protected. Different callers legitimately need
different scopes of access, so a single shared secret would either over-grant
or require one secret per caller per scope, an operational dead end at scale.
And the system needs the ability to revoke or expire access without rotating
every downstream service's trusted credential store, which a shared long-lived
secret cannot provide.

## 3. Forces

Statelessness versus revocability is the single dominant tension in this
pattern. A self-contained token (a signed JWT) lets every service validate a
call with zero network round trip to a central authority, which is the entire
point at microservice scale, call volume can be in the tens of thousands of
requests per second per service. But a token nobody has to ask about cannot
be revoked before it expires without a denylist, which reintroduces the
central lookup the self-contained design exists to avoid. Every implementation
variant in dimension 8 is a different answer to this one tension.

Blast radius versus operational simplicity is the second force. A token
scoped narrowly, and short-lived, limits what an attacker who steals it in
transit or from a log can do, and for how long. But narrow scoping and short
lifetimes multiply the number of tokens in flight and the frequency of
refresh calls, which is engineering cost paid continuously, forever, in
exchange for a security property paid off only in the event of a compromise.

Latency versus assurance follows directly from the format chosen. Local
signature verification of a JWT costs microseconds. Introspection of an
opaque token against a central authorization server costs a network round
trip, typically single-digit to low double-digit milliseconds, and that
authority becomes a dependency every protected call now has. RFC 6749 does
not mandate either format, this trade-off is left entirely to the
implementer, and most large systems end up running both, JWTs for
service-to-service calls in the hot path, opaque tokens with introspection
for lower-volume, higher-sensitivity flows.

Trust propagation versus caller identity fidelity is the fourth force. When
service A calls service B on behalf of a user, does B see the original
user's token, a new token minted for A acting as itself, or a token that
carries both A's identity and the original user's identity as a delegated
claim, the on-behalf-of pattern formalized in RFC 8693, OAuth 2.0 Token
Exchange? Each choice trades audit fidelity, blast radius if A is
compromised, and implementation complexity against each other, and getting
it wrong is dimension 11's most common production failure.

Cost of key and secret management versus token format closes the list. A
signed, self-contained token requires every verifying party to have the
signing key, a public key for asymmetric signing, or a shared secret for
symmetric signing, and key rotation without an outage requires every
verifier to support multiple valid keys simultaneously during the rotation
window. An opaque token defers that entire problem to the single issuing
and introspecting authority, at the cost of the network dependency above.

## 4. Applicability and non-applicability

Reach for an access token when:

- A caller crosses one or more network trust boundaries before reaching the
  resource it wants, and the receiving side cannot directly observe the
  original authentication event.
- Different callers need materially different, revocable scopes of access to
  the same resource, so a single static secret cannot express the difference.
- The system must support short-lived credentials, either to bound the impact
  of a leaked credential or to satisfy a compliance requirement for periodic
  re-authorization, for example PCI DSS session timeout rules.
- Multiple independently deployed services need to verify a caller's identity
  and permissions without each one owning a copy of the caller's password.
- The architecture already has, or is willing to build, a trusted issuing
  authority, an authorization server, an identity provider, or a platform
  control plane such as the Kubernetes API server.

Do NOT reach for an access token when:

- The call never crosses a trust boundary, two threads inside one process
  calling each other need no token, the function call itself is the trust
  boundary, and wrapping it in token validation adds cost with no security
  gain.
- The system is a single monolith with one shared session store and no
  independent services to distribute trust to, a signed session cookie or a
  server-side session ID is simpler and equally sufficient, see the session
  state entry.
- The caller and callee are two machines inside a network segment already
  protected by mutual TLS with certificate-based identity, and the workload
  identity that mTLS already establishes is sufficient for the authorization
  decision needed, adding a token on top is redundant defense that most teams
  do add anyway for defense in depth, but it is not required by the problem.
- The team has no operational capacity to run key rotation, token revocation,
  and clock-skew handling correctly. A badly operated token system, keys that
  never rotate, no revocation path, clocks that drift, is a worse security
  posture than a well-operated static secret with a strict network perimeter,
  because it creates a false sense of the properties the pattern is supposed
  to provide.
- Extremely latency-sensitive internal calls, sub-millisecond budgets, where
  even local signature verification's microseconds matter and a coarser,
  cheaper trust mechanism, network segmentation, an already-established mTLS
  session, is sufficient for the specific hop.

## 5. Structure

Resource Owner is the entity, usually a human user, who owns the protected
resource and can grant access to it. In machine-to-machine flows this role
is absent, the client acts on its own behalf (RFC 6749 section 4.4, the
Client Credentials grant).

Client is the application or service that wants access to the protected
resource and holds the access token to present on calls. In a microservices
system a client can itself be another microservice.

Authorization Server is the trusted authority that authenticates the
resource owner or the client, and issues the access token after
successfully validating the request. It holds or has access to the signing
key, and is the single source of truth for what a given token is allowed to
do.

Resource Server is the microservice that hosts the protected resource and
accepts access tokens to authorize incoming requests. It validates the
token, either locally against a signature and claims, or remotely via
introspection, and enforces the scope the token carries.

Access Token is the credential itself, a string, either self-contained,
typically a signed JWT carrying its own claims, or a reference, an opaque
random string that means nothing until looked up.

Refresh Token is an optional participant, a longer-lived, more sensitive
credential the client exchanges for a new access token when the current one
expires, without repeating full user authentication. Defined in RFC 6749
section 1.5.

Introspection Endpoint is present only for opaque tokens. It is an endpoint
on the authorization server, defined by RFC 7662, OAuth 2.0 Token
Introspection, that a resource server calls to determine the current state
and metadata of a token it did not itself issue.

## 6. ASCII structure diagram

```
+------------------+          issues           +----------------------+
|  Client / caller  |  <----------------------  |  Authorization Server |
|  (app, service,   |                            |  (issuer, holds keys) |
|   mobile client)  |  ------------------------> |                        |
+------------------+   authenticates, requests   +----------------------+
        |                     token                          |
        | presents token                                     | signs / mints
        | on every call                                      | access token
        v                                                     v
+-------------------------------------------------------------------+
|                          Access Token (string)                    |
|   self-contained (JWT), header.payload.signature, verified local  |
|   opaque, random string, verified via Introspection Endpoint      |
+-------------------------------------------------------------------+
        |
        | Authorization header, Bearer plus the token
        v
+------------------+   local verify   +------------------------------+
|  Resource Server   | <-------------  |  Introspection Endpoint      |
|  (microservice)    |   (opaque only) |  (authorization server side) |
+------------------+   --------------> +------------------------------+
        |               remote verify
        v
   grants or denies
   the requested call
```

## 7. Dynamics

```
Client                Authorization Server         Resource Server (Service B)
  |                            |                              |
  |-- 1. authenticate -------->|                              |
  |    (password, client       |                              |
  |     credentials, OIDC)     |                              |
  |                            |                              |
  |<-- 2. access_token --------|                              |
  |    (+ refresh_token,       |                              |
  |     expires_in)            |                              |
  |                            |                              |
  |-- 3. GET /resource -------------------------------------->|
  |    Authorization header, Bearer plus access_token          |
  |                            |                              |
  |                            |<-- 4a. introspect(token) -----|
  |                            |    (opaque token only)        |
  |                            |-- active, scope, exp -------->|
  |                            |                              |
  |                            |     4b. verify signature,     |
  |                            |     iss/aud/exp claims        |
  |                            |     (self-contained JWT,      |
  |                            |     no call to step 4a)       |
  |                            |                              |
  |<-------------------------------- 5. 200 OK or 401/403 -----|
  |                            |                              |
  |-- 6. token expires, repeat from step 1                     |
  |    with refresh_token, no full re-auth ------------------->|
```

## 8. Implementation variants

Self-contained token, a JWT under RFC 7519 and the OAuth profile in RFC 9068,
carries its claims (subject, issuer, audience, expiration, scope) plus a
cryptographic signature. Any resource server holding the issuer's public key
can verify the token entirely locally, with zero call to the authorization
server on the hot path. RFC 9068, "JSON Web Token (JWT) Profile for OAuth
2.0 Access Tokens", standardizes the claim set, requires the header field
`"typ":"at+jwt"` specifically so a JWT access token can be distinguished
from an OpenID Connect ID token, and mandates that the signing algorithm
never be `"none"` (RFC 9068, verified 2026-08-02,
https://datatracker.ietf.org/doc/html/rfc9068). The cost is exactly the
revocation problem from dimension 3, a compromised or logged-out token
remains technically valid until it expires, unless the system also
maintains a denylist, which most self-contained-token systems keep
deliberately short lived, five to fifteen minutes, precisely to bound this
exposure.

Opaque reference token with introspection, RFC 7662, uses a random,
unguessable string with no embedded meaning. A resource server that
receives it must call the authorization server's introspection endpoint to
learn whether it is active and what it authorizes. This makes revocation
instantaneous, deleting the token record at the authorization server takes
effect on the very next call, at the cost of a network round trip on every
validated request unless the resource server caches introspection results
for a short window, which reintroduces a bounded version of the same
staleness problem the self-contained variant has.

Hybrid, cached introspection is the middle ground used at scale by API
gateways. Opaque tokens are used at the edge for maximum revocability, but
the gateway performs introspection once and mints a short-lived,
self-contained internal JWT for the call to travel through the internal
service mesh. This confines the introspection network cost to a single hop
at the perimeter while keeping internal hops fast and stateless.

Token exchange and delegation under RFC 8693, OAuth 2.0 Token Exchange,
solves the case where service A must call service B while preserving the
identity of the original caller. A presents its own token plus the caller's
token to a token exchange endpoint, and receives a new token that carries
both identities, the acting party and the delegated subject, as distinct
claims. This is the standardized answer to the trust-propagation force from
dimension 3, and it is what lets an audit log at service B distinguish
"user X's request, routed through service A" from "service A acting on its
own authority."

Cloud platform temporary credentials extend the same pattern outside HTTP
APIs. AWS Security Token Service issues temporary security credentials, an
access key ID, secret access key, and session token bundle, with a
caller-specified or role-defined expiration, commonly fifteen minutes to
twelve hours (AWS STS documentation, verified 2026-08-02,
https://docs.aws.amazon.com/STS/latest/APIReference/welcome.html). This is
architecturally the same access token pattern applied to cloud resource
authorization rather than HTTP API authorization, a short-lived, scoped,
independently issued credential replacing a long-lived static one.

Platform-issued bound service identity tokens apply the pattern to workload
identity rather than user identity. Kubernetes issues ServiceAccount tokens
through the TokenRequest API as short-lived, audience- and object-bound
JWTs, projected into a pod's filesystem and automatically rotated by the
kubelet before expiry, rather than the older, non-expiring, Secret-stored
ServiceAccount tokens (Kubernetes documentation, verified 2026-08-02,
https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/).
The "client" in dimension 5's structure is the pod itself in this variant.

## 9. Known production uses

AWS Security Token Service issues temporary security credentials used across
every AWS service that supports IAM roles, cross-account access, and
identity federation, the standard mechanism by which an EC2 instance, a
Lambda function, or a federated user obtains scoped, expiring access
without a long-lived access key. AWS STS documentation, verified
2026-08-02, https://docs.aws.amazon.com/STS/latest/APIReference/welcome.html.

Kubernetes ServiceAccount bound tokens are used by every pod that talks to
the Kubernetes API server, and by extension the many operators and
controllers built on client-go, which authenticate with a projected,
audience-bound, automatically rotated JWT issued through the TokenRequest
API, replacing the older non-expiring token-in-a-Secret model. Kubernetes
documentation, verified 2026-08-02,
https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/.

GitHub Actions OpenID Connect tokens let GitHub Actions workflows request a
short-lived OIDC token, signed by GitHub's own issuer, that cloud providers
(AWS, Azure, GCP) trust to grant scoped access without a long-lived static
cloud credential ever being stored as a repository secret. This is the
token exchange and delegation variant from dimension 8 applied to CI/CD
workload identity (GitHub documentation, "About security hardening with
OpenID Connect", verified 2026-08-02,
https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect).

Auth0 and Okta are widely deployed commercial implementations of RFC 6749's
Authorization Server role, issuing JWT access tokens conforming to the RFC
9068 profile that downstream resource servers verify locally against a
published JSON Web Key Set, the standard shape microservice APIs use to
accept third-party identity provider tokens without ever seeing a user's
password.

## 10. Consequences

Positive. Passwords and other long-lived secrets never travel past the
initial authentication exchange, every downstream hop sees only a bounded,
purpose-scoped credential. Access can be scoped precisely per caller and per
use case, a mobile client reading a user's profile and a batch job exporting
the same user's data can hold tokens with entirely different, independently
revocable scopes. Self-contained tokens let every service in a large call
graph verify a caller without a central lookup on the hot path, which is
what makes the pattern viable at microservice scale, where a shared session
store would become a bottleneck and a single point of failure. Expiration is
a built-in, cheap defense, a stolen token has a bounded useful life even if
no one notices the theft, which a static, never-expiring API key does not
provide. Delegation and impersonation through token exchange give the
system a standardized, auditable way to say "service A, acting for user X"
rather than services silently forwarding raw user credentials to each
other.

Negative. Self-contained tokens cannot be revoked before their natural
expiry without additional infrastructure, a denylist or a short-lived-
token-plus-refresh design, which means a naive implementation trades one
form of exposure for another rather than eliminating it. The system now
depends on correct clock synchronization across every verifying service,
expiration and not-before checks fail in confusing ways when a server's
clock drifts, and this is a genuinely common production incident class, see
dimension 11. Key management becomes a first-class operational concern,
signing keys must be rotated, distributed to every verifier, and the
rotation itself must not cause an outage, which is nontrivial engineering
that a static shared secret never demanded. Every additional network hop
that must independently validate a token adds latency and a new place for a
validation bug, a wrong audience check, a missing signature verification, an
accepted "none" algorithm, to silently become an authentication bypass.
Token size matters in a way passwords never did, a JWT loaded with claims,
roles, and group memberships can bloat past what fits comfortably in an
HTTP header or a load balancer's header size limit, a real operational
failure mode at organizations with deep role hierarchies.

## 11. Failure modes and misuse

Symptom. A service silently authorizes requests with `alg: none` or accepts
any signature. Cause. The JWT verification library's algorithm list was
left permissive, or the code path that chose the verification algorithm
trusted the algorithm named in the token's own header instead of a
server-side allowlist. Fix. Pin the accepted algorithm list server-side,
never read it from the token, and explicitly reject "none". RFC 9068
mandates never accepting "none" for exactly this reason.

Symptom. A token minted for one service is accepted by an entirely
different, unrelated service. Cause. The receiving service checks the
signature and expiration but never checks the audience claim, so any
validly signed token from the same issuer, regardless of what it was
actually issued for, passes verification. Fix. Every resource server
validates the audience claim against its own identifier as a mandatory,
non-optional check, exactly as RFC 9068 section 4 requires.

Symptom. Authentication intermittently fails for a subset of servers, or
fails only near midnight, and self-resolves. Cause. Clock skew between the
issuing authorization server and a verifying resource server, so the
expiration or not-before claims evaluate as already expired or not yet
valid on the skewed server. Fix. Run NTP or an equivalent time sync on
every host that verifies tokens, and build a small, explicit clock-skew
tolerance, commonly thirty to one hundred twenty seconds, into the
verification logic rather than comparing timestamps with zero tolerance.

Symptom. A revoked user, or a user who has logged out, continues to
successfully call protected APIs for up to the token's full lifetime.
Cause. The system chose the self-contained token variant for its
statelessness benefit and never built a revocation or short-lived-plus-
refresh mechanism, so logout only deletes the client-side copy of a token
that remains cryptographically valid at every server that never checks
back. Fix. Keep access token lifetimes short, minutes rather than hours,
pair with a revocable refresh token, and for genuinely high-sensitivity
operations, add a denylist check or fall back to introspection.

Symptom. A stolen or leaked token found in a log file, a browser history,
or a proxy trace grants an attacker full access for its entire remaining
lifetime, with no way to shut it down individually. Cause. Tokens were
logged in plaintext, a very common mistake, request logging middleware
that dumps raw header values, combined with lifetimes long enough that the
leak matters. Fix. Redact the Authorization header and any token value from
every logging path as policy, not as an afterthought, and keep lifetimes
short enough that a leak's blast radius is bounded even when redaction
fails.

Symptom. Service A calls service B, and B's audit log records the request
as coming from "service A" with no way to tell which end user's action
triggered it. Cause. A confused-deputy setup, A silently forwards its own
service identity token rather than the caller's, or mints its own token
without preserving the delegation chain. Fix. Use token exchange, RFC 8693,
to carry both the acting party and the original subject as distinct
claims, so downstream audit and authorization decisions can see the full
chain, not only the last hop.

## 12. Trade-off matrix

| Force | Access Token (self-contained JWT) | Access Token (opaque + introspection) | Server-side Session | Static long-lived API Key | mTLS client certificate |
|---|---|---|---|---|---|
| Revocation speed | Bounded by token lifetime, no instant revoke without a denylist | Instant, deletion at authority takes effect on next introspection call | Instant, delete the session record | Manual, requires key rotation everywhere it is used | Requires certificate revocation list or short-lived cert reissue |
| Hot-path latency | Local verification, no network call | One network call per validated request unless cached | One lookup against session store | Constant-time string compare, no network call | Handled at TLS handshake, amortized over connection reuse |
| Fine-grained scope per caller | Yes, expressed as claims | Yes, expressed as introspection response | Coarser, tied to the session's user | Coarse, one key usually means one broad grant | Identity only, authorization layered separately |
| Delegation across services | Native via token exchange, RFC 8693 | Native via token exchange, RFC 8693 | Not designed for this, requires custom propagation | Not supported | Not applicable, mTLS proves the calling service's identity, not the end user's |
| Operational cost | Key rotation and distribution to every verifier | Authorization server availability becomes a hard dependency | Central session store becomes a scaling bottleneck | Low, until a key leaks, then rotation is manual and disruptive | Certificate lifecycle management, typically automated via a mesh control plane |
| Best fit | High call volume, many independent verifying services | Lower call volume, high sensitivity, revocation matters more than latency | Single application, no independent downstream services | Legacy or partner integrations with no OAuth infrastructure | Service identity inside a mesh, paired with a token for user-level authorization |

## 13. Related and incompatible patterns

API Gateway is the most common single point at which access tokens are
first validated on the way into a system from an external client, and it
is frequently the component that performs the hybrid pattern from
dimension 8, validating an opaque or externally issued token once and
minting a lighter internal token for the request's remaining path.

Service Mesh typically supplies transport-level identity via mutual TLS
between services. Access tokens and mTLS compose rather than compete, mTLS
answers which service is calling, an access token answers on whose
authority, and to do what. Many production systems run both
simultaneously, mTLS for workload identity, tokens for user and scope
authorization carried on top of that already-authenticated channel.

Self-contained Service and the self-contained JWT variant of the access
token pattern share the same principle. A service that validates tokens
locally, without a network call to a shared session store, is applying the
same "do not depend on a shared runtime state store to do your job"
principle that self-contained service applies to deployment, applied here
to authorization state instead of application state.

Audit Logging depends directly on the claims carried in an access token, in
particular the subject, the acting party from a token exchange, and the
granted scope, which are frequently the exact fields an audit log needs to
answer who did what. Systems that discard the token's claims after
authorization and log only a generic authenticated request have made audit
logging materially harder than it needed to be.

There is no strict incompatibility. The pattern is a cross-cutting
authorization mechanism, not an architectural structure, so it does not
structurally conflict with any other pattern in this catalog. The closest
thing to a conflict is choosing a self-contained JWT for a system with a
hard, sub-second revocation requirement, a payment-authorization system for
example, where the pattern's core trade-off from dimension 3 makes it a
poor fit unless paired with a denylist, at which point much of its
statelessness advantage is given back.

## 14. Refactoring path in and out

Introducing the pattern into a system that currently shares a database
password or a single static API key across services follows five steps.

1. Stand up an authorization server, or select a managed one, an OIDC
   provider such as Auth0, Okta, or a self-hosted implementation, before
   changing any calling code. Nothing downstream should change until the
   issuing side exists and is trustworthy.
2. Introduce token issuance at exactly one entry point first, typically the
   public edge or the API gateway, while every internal call still uses the
   old shared credential. This isolates the blast radius of the change to a
   single component. Choose the token format from dimension 8 deliberately
   at this step, based on the call volume and revocation requirements
   measured from the trade-off matrix, rather than defaulting to whichever
   format the first library examples happen to show.
3. Add token verification to one downstream service at a time, running it
   in parallel with the old credential check, accept either, so a bad
   rollout can be reverted without an outage, and only remove the old check
   once the new one has run in production, verified, for a full deploy
   cycle with no authorization failures traced to the new path.
4. Once every service verifies tokens, retire the shared static credential
   entirely, rotate it to an unusable value, and delete it from every
   configuration store and secret manager, do not merely stop using it.
5. Add token exchange, RFC 8693, only once the basic pattern is stable and
   a genuine service-to-service delegation need appears, introducing it
   preemptively adds complexity dimension 3 already flags as costly, before
   the system has a concrete use for it.

Removing the pattern, when a service genuinely no longer needs it, is rare
in practice, because removing token-based authorization typically means
either collapsing multiple services back into one process, in which case
the pattern is removed as a side effect of the larger refactor and not
directly, or the service moving fully behind a network perimeter it did
not previously have, where mTLS or network segmentation now supplies the
identity guarantee the token supplied. If that shift genuinely holds,
remove verification only after confirming, via the observability signals
in dimension 16, that the perimeter has held for a sustained period with
the token check running in log-only, non-enforcing mode first.

## 15. Testing and verification

Access-token-protected code is easier to unit test than a shared-session
design, because a token is a self-contained input value, tests construct
tokens with specific claims, a specific scope, an expired timestamp, a
mismatched audience, directly, with no need for a stateful session fixture
or a running authorization server for most of the test surface.

Unit test the verification logic in isolation, with hand-constructed
tokens covering, at minimum, a valid token, an expired token, a token with
the wrong audience, a token signed with an unexpected algorithm, and a
token missing a required claim. Every failure mode listed in dimension 11
should map to at least one test case that currently fails closed.

Use a test double for the authorization server, not the real one, for
integration tests of the opaque-token-plus-introspection variant. A local
stub that returns controlled introspection responses lets tests exercise
token revoked mid-flight and authorization server slow to respond
deterministically, conditions the real service is hard to force reliably.

Test clock skew explicitly, by injecting a fake clock into the
verification path rather than relying on the system clock at test-run
time, so the skew-tolerance logic from dimension 11 has coverage that does
not depend on when the test happens to run.

Contract-test the claim shape between the issuer and every consuming
service if the two are maintained by different teams, a claim renamed or
removed on the issuing side is exactly the kind of change that breaks
every downstream verifier silently and simultaneously, and a shared schema
contract test catches it before deploy rather than in production.

Never test with real, valid production tokens or the production signing
key in a test suite, use a dedicated test-only key pair, checked in or
generated at test time, so a leaked test fixture cannot be used against
the real system.

## 16. Observability signals

Token verification failure rate, broken down by reason, expired, bad
signature, wrong audience, wrong issuer, malformed, is the single most
useful metric. A flat baseline of expired-token failures is normal and
expected, a spike in bad-signature or wrong-issuer failures is a strong
signal of either a misconfiguration, a key rotation gone wrong, or an
active attack.

Introspection endpoint latency and error rate matter for the opaque-token
variant, because it is now a hard dependency on the request path of every
service that verifies tokens this way, and its own degradation propagates
directly into every one of those services' error rates.

Token issuance rate versus refresh rate is worth tracking, since an
unexpected drop in refresh volume relative to issuance can indicate clients
failing to refresh silently, a signal that surfaces as a slow-building wave
of expired-token errors minutes later if it is not caught first at the
refresh metric.

The distinct count of subjects and scopes seen per token, watched over time, is a
useful early-warning signal, because a rapid unexplained growth in the
number of distinct scopes or subjects seen is a common early signal of
either a misconfigured client minting overly specific tokens per request
instead of reusing one, or of token-forging activity.

Key age and rotation lag, tracked per verifying service, matters because
the slowest service to pick up a newly rotated signing key is the one
whose outage window, if the old key is retired too early, will be longest
and hardest to diagnose from the outside.

Audit log completeness for delegated calls, specifically whether the
acting-party and subject claims from a token-exchange flow are both
present in the downstream audit trail, is the observable proxy for the
confused-deputy failure mode described in dimension 11, absence of one is
the symptom.

## 17. Security and privacy implications

The access token is itself a bearer secret for the duration of its
validity, by RFC 6750's own definition possession alone is sufficient to
use it, so every place a token transits or rests, request logs, browser
storage, proxy traces, error reporting tools that capture request headers,
is a place it can leak with the same consequence as a leaked password for
that token's scope and lifetime. This is why redaction of the
Authorization header from logs is not an optional hardening step, it is
the single most effective control available, because it closes the most
common real-world leak vector directly.

Self-contained JWTs carry their claims in a base64url-encoded, not
encrypted, payload by default, anyone who intercepts the token, or anyone
the token is merely shown to in a debugging tool, can read every claim in
it without holding the signing key. Do not place personally identifiable
information beyond what is operationally necessary, and never place a
secret value, into an unencrypted JWT's claims, use JWE, JSON Web
Encryption, if the claim set itself must be confidential from parties who
legitimately hold the token but should not see its full contents.

Token lifetime is a direct security-versus-usability trade with no free
option, and RFC 9068's typing requirement, the header field set to
`at+jwt`, exists specifically to close a real, previously exploited
confusion between OAuth access tokens and OpenID Connect ID tokens, where
a token minted to prove identity to a client application was being
accepted by resource servers as if it granted API access, because nothing
in the unmarked token distinguished the two roles.

The introspection endpoint used by the opaque-token variant is itself a
sensitive API, it answers whether a given credential is currently valid,
and for what, which is exactly the information an attacker probing for
valid tokens wants, so it must be authenticated and rate-limited as
carefully as any other security-critical endpoint, not treated as an
internal implementation detail exempt from the system's usual API
security controls.

## 18. References

1. D. Hardt, ed., "The OAuth 2.0 Authorization Framework", RFC 6749, IETF,
   October 2012, section 1.4, verified 2026-08-02,
   https://datatracker.ietf.org/doc/html/rfc6749#section-1.4.
2. M. Jones, D. Hardt, "The OAuth 2.0 Authorization Framework. Bearer
   Token Usage", RFC 6750, IETF, October 2012.
3. D. Hardt et al., "OAuth 2.0 Token Introspection", RFC 7662, IETF,
   October 2015.
4. M. Jones, J. Bradley, N. Sakimura, "JSON Web Token (JWT)", RFC 7519,
   IETF, May 2015.
5. V. Bertocci, "JSON Web Token (JWT) Profile for OAuth 2.0 Access
   Tokens", RFC 9068, IETF, October 2021, verified 2026-08-02,
   https://datatracker.ietf.org/doc/html/rfc9068.
6. T. Jones, D. Nadalin, D. Campbell, B. Bihari, M. Jones, "OAuth 2.0
   Token Exchange", RFC 8693, IETF, January 2020.
7. Amazon Web Services, "AWS Security Token Service, API Reference",
   verified 2026-08-02,
   https://docs.aws.amazon.com/STS/latest/APIReference/welcome.html.
8. The Kubernetes Authors, "Managing Service Accounts", Kubernetes
   documentation, verified 2026-08-02,
   https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/.
9. GitHub, Inc., "About security hardening with OpenID Connect", GitHub
   Actions documentation, verified 2026-08-02,
   https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect.
10. Wikipedia contributors, summary of the OAuth 2.0 access token
    definition, cross-checked against the primary RFC 6749 text, verified
    2026-08-02, https://en.wikipedia.org/wiki/OAuth.

## Code examples

Working, minimal examples of minting and verifying a self-contained JWT
access token, chosen because it is the variant most microservice teams
reach for first. TypeScript, Python, and Go each show HMAC-signed issuance
and verification with an explicit audience and expiration check. Rust shows
the verification side only, receiving and checking a token, since a
resource server verifying a token it did not itself mint is the more
common role for a downstream microservice. Java and Kotlin are omitted, no
working JDK was available in the environment these samples were run in,
and shipping an uncompiled Java sample would misrepresent it as verified
when it was not. The pattern maps directly onto the standard Base64 and
Mac classes for teams working in Java, using the same three-part signing
scheme shown below.

### TypeScript

```typescript
import { createHmac, timingSafeEqual } from "node:crypto";

const SECRET = "test-signing-key-do-not-use-in-production";

function base64url(input: Buffer): string {
  return input.toString("base64url");
}

function signAccessToken(
  subject: string,
  audience: string,
  scopes: string[],
  ttlSeconds: number,
): string {
  const header = { alg: "HS256", typ: "at+jwt" };
  const now = Math.trunc(Date.now() / 1000);
  const payload = {
    iss: "https://auth.example.com",
    sub: subject,
    aud: audience,
    scope: scopes.join(" "),
    iat: now,
    exp: now + ttlSeconds,
  };
  const headerPart = base64url(Buffer.from(JSON.stringify(header)));
  const payloadPart = base64url(Buffer.from(JSON.stringify(payload)));
  const signingInput = `${headerPart}.${payloadPart}`;
  const signature = createHmac("sha256", SECRET).update(signingInput).digest();
  return `${signingInput}.${base64url(signature)}`;
}

interface VerifyResult {
  ok: boolean;
  reason?: string;
  scopes?: string[];
}

function verifyAccessToken(token: string, expectedAudience: string): VerifyResult {
  const parts = token.split(".");
  if (parts.length !== 3) return { ok: false, reason: "malformed" };
  const [headerPart, payloadPart, signaturePart] = parts;

  const expected = createHmac("sha256", SECRET)
    .update(`${headerPart}.${payloadPart}`)
    .digest();
  const given = Buffer.from(signaturePart, "base64url");
  if (expected.length !== given.length || !timingSafeEqual(expected, given)) {
    return { ok: false, reason: "bad_signature" };
  }

  const payload = JSON.parse(Buffer.from(payloadPart, "base64url").toString());
  const now = Math.trunc(Date.now() / 1000);
  if (payload.aud !== expectedAudience) return { ok: false, reason: "wrong_audience" };
  if (payload.exp < now) return { ok: false, reason: "expired" };

  return { ok: true, scopes: payload.scope.split(" ") };
}

const token = signAccessToken("user-42", "orders-service", ["orders:read"], 300);
console.log("issued", token);
console.log("verify correct audience", verifyAccessToken(token, "orders-service"));
console.log("verify wrong audience", verifyAccessToken(token, "billing-service"));
```

Run with `npx tsc --strict --target es2022 --module nodenext access-token.ts && node access-token.js`.

### Python

```python
import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass

SECRET = b"test-signing-key-do-not-use-in-production"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def sign_access_token(subject: str, audience: str, scopes: list[str], ttl_seconds: int) -> str:
    header = {"alg": "HS256", "typ": "at+jwt"}
    now = int(time.time())
    payload = {
        "iss": "https://auth.example.com",
        "sub": subject,
        "aud": audience,
        "scope": " ".join(scopes),
        "iat": now,
        "exp": now + ttl_seconds,
    }
    header_part = _b64url(json.dumps(header).encode())
    payload_part = _b64url(json.dumps(payload).encode())
    signing_input = f"{header_part}.{payload_part}".encode()
    signature = hmac.new(SECRET, signing_input, hashlib.sha256).digest()
    return f"{header_part}.{payload_part}.{_b64url(signature)}"


@dataclass
class VerifyResult:
    ok: bool
    reason: str | None = None
    scopes: list[str] | None = None


def verify_access_token(token: str, expected_audience: str) -> VerifyResult:
    parts = token.split(".")
    if len(parts) != 3:
        return VerifyResult(ok=False, reason="malformed")
    header_part, payload_part, signature_part = parts

    signing_input = f"{header_part}.{payload_part}".encode()
    expected = hmac.new(SECRET, signing_input, hashlib.sha256).digest()
    given = _b64url_decode(signature_part)
    if not hmac.compare_digest(expected, given):
        return VerifyResult(ok=False, reason="bad_signature")

    payload = json.loads(_b64url_decode(payload_part))
    now = int(time.time())
    if payload["aud"] != expected_audience:
        return VerifyResult(ok=False, reason="wrong_audience")
    if payload["exp"] < now:
        return VerifyResult(ok=False, reason="expired")

    return VerifyResult(ok=True, scopes=payload["scope"].split(" "))


if __name__ == "__main__":
    token = sign_access_token("user-42", "orders-service", ["orders:read"], 300)
    print("issued", token)
    print("verify correct audience", verify_access_token(token, "orders-service"))
    print("verify wrong audience", verify_access_token(token, "billing-service"))
```

Run with `python3 access_token.py`.

### Go

```go
package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

var secret = []byte("test-signing-key-do-not-use-in-production")

type header struct {
	Alg string `json:"alg"`
	Typ string `json:"typ"`
}

type claims struct {
	Iss   string `json:"iss"`
	Sub   string `json:"sub"`
	Aud   string `json:"aud"`
	Scope string `json:"scope"`
	Iat   int64  `json:"iat"`
	Exp   int64  `json:"exp"`
}

func b64url(b []byte) string {
	return base64.RawURLEncoding.EncodeToString(b)
}

func signAccessToken(subject, audience string, scopes []string, ttl time.Duration) (string, error) {
	h := header{Alg: "HS256", Typ: "at+jwt"}
	now := time.Now().Unix()
	c := claims{
		Iss:   "https://auth.example.com",
		Sub:   subject,
		Aud:   audience,
		Scope: strings.Join(scopes, " "),
		Iat:   now,
		Exp:   now + int64(ttl.Seconds()),
	}
	hb, err := json.Marshal(h)
	if err != nil {
		return "", err
	}
	cb, err := json.Marshal(c)
	if err != nil {
		return "", err
	}
	signingInput := b64url(hb) + "." + b64url(cb)
	mac := hmac.New(sha256.New, secret)
	mac.Write([]byte(signingInput))
	return signingInput + "." + b64url(mac.Sum(nil)), nil
}

type verifyResult struct {
	OK     bool
	Reason string
	Scopes []string
}

func verifyAccessToken(token, expectedAudience string) verifyResult {
	parts := strings.Split(token, ".")
	if len(parts) != 3 {
		return verifyResult{Reason: "malformed"}
	}
	signingInput := parts[0] + "." + parts[1]
	mac := hmac.New(sha256.New, secret)
	mac.Write([]byte(signingInput))
	expected := mac.Sum(nil)
	given, err := base64.RawURLEncoding.DecodeString(parts[2])
	if err != nil || subtle.ConstantTimeCompare(expected, given) != 1 {
		return verifyResult{Reason: "bad_signature"}
	}

	payloadBytes, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return verifyResult{Reason: "malformed"}
	}
	var c claims
	if err := json.Unmarshal(payloadBytes, &c); err != nil {
		return verifyResult{Reason: "malformed"}
	}
	if c.Aud != expectedAudience {
		return verifyResult{Reason: "wrong_audience"}
	}
	if c.Exp < time.Now().Unix() {
		return verifyResult{Reason: "expired"}
	}
	return verifyResult{OK: true, Scopes: strings.Split(c.Scope, " ")}
}

func main() {
	token, err := signAccessToken("user-42", "orders-service", []string{"orders:read"}, 5*time.Minute)
	if err != nil {
		panic(err)
	}
	fmt.Println("issued", token)
	fmt.Printf("verify correct audience %+v\n", verifyAccessToken(token, "orders-service"))
	fmt.Printf("verify wrong audience %+v\n", verifyAccessToken(token, "billing-service"))
}
```

Run with `go run access_token.go`.

### Rust

```rust
use std::time::{SystemTime, UNIX_EPOCH};

const K: [u32; 64] = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
];

fn sha256(message: &[u8]) -> [u8; 32] {
    let mut h: [u32; 8] = [
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
    ];

    let bit_len = (message.len() as u64) * 8;
    let mut padded = message.to_vec();
    padded.push(0x80);
    while padded.len() % 64 != 56 {
        padded.push(0);
    }
    padded.extend_from_slice(&bit_len.to_be_bytes());

    for chunk in padded.chunks(64) {
        let mut w = [0u32; 64];
        for i in 0..16 {
            w[i] = u32::from_be_bytes([chunk[4 * i], chunk[4 * i + 1], chunk[4 * i + 2], chunk[4 * i + 3]]);
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16].wrapping_add(s0).wrapping_add(w[i - 7]).wrapping_add(s1);
        }

        let (mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut hh) =
            (h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7]);

        for i in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ ((!e) & g);
            let temp1 = hh.wrapping_add(s1).wrapping_add(ch).wrapping_add(K[i]).wrapping_add(w[i]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let temp2 = s0.wrapping_add(maj);

            hh = g;
            g = f;
            f = e;
            e = d.wrapping_add(temp1);
            d = c;
            c = b;
            b = a;
            a = temp1.wrapping_add(temp2);
        }

        h[0] = h[0].wrapping_add(a);
        h[1] = h[1].wrapping_add(b);
        h[2] = h[2].wrapping_add(c);
        h[3] = h[3].wrapping_add(d);
        h[4] = h[4].wrapping_add(e);
        h[5] = h[5].wrapping_add(f);
        h[6] = h[6].wrapping_add(g);
        h[7] = h[7].wrapping_add(hh);
    }

    let mut out = [0u8; 32];
    for (i, word) in h.iter().enumerate() {
        out[4 * i..4 * i + 4].copy_from_slice(&word.to_be_bytes());
    }
    out
}

fn hmac_sha256(key: &[u8], message: &[u8]) -> [u8; 32] {
    const BLOCK_SIZE: usize = 64;
    let mut key_block = [0u8; BLOCK_SIZE];
    if key.len() > BLOCK_SIZE {
        let hashed = sha256(key);
        key_block[..32].copy_from_slice(&hashed);
    } else {
        key_block[..key.len()].copy_from_slice(key);
    }

    let mut inner_pad = [0x36u8; BLOCK_SIZE];
    let mut outer_pad = [0x5cu8; BLOCK_SIZE];
    for i in 0..BLOCK_SIZE {
        inner_pad[i] ^= key_block[i];
        outer_pad[i] ^= key_block[i];
    }

    let mut inner_input = inner_pad.to_vec();
    inner_input.extend_from_slice(message);
    let inner_hash = sha256(&inner_input);

    let mut outer_input = outer_pad.to_vec();
    outer_input.extend_from_slice(&inner_hash);
    sha256(&outer_input)
}

fn constant_time_eq(a: &[u8], b: &[u8]) -> bool {
    if a.len() != b.len() {
        return false;
    }
    let mut diff = 0u8;
    for i in 0..a.len() {
        diff |= a[i] ^ b[i];
    }
    diff == 0
}

const ALPHABET: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";

fn b64url_encode(data: &[u8]) -> String {
    let mut out = String::new();
    for chunk in data.chunks(3) {
        let b0 = chunk[0];
        let b1 = *chunk.get(1).unwrap_or(&0);
        let b2 = *chunk.get(2).unwrap_or(&0);
        let n = ((b0 as u32) << 16) | ((b1 as u32) << 8) | (b2 as u32);
        out.push(ALPHABET[((n >> 18) & 63) as usize] as char);
        out.push(ALPHABET[((n >> 12) & 63) as usize] as char);
        if chunk.len() > 1 {
            out.push(ALPHABET[((n >> 6) & 63) as usize] as char);
        }
        if chunk.len() > 2 {
            out.push(ALPHABET[(n & 63) as usize] as char);
        }
    }
    out
}

fn b64url_decode(s: &str) -> Vec<u8> {
    let mut table = [255u8; 256];
    for (i, &c) in ALPHABET.iter().enumerate() {
        table[c as usize] = i as u8;
    }
    let bytes: Vec<u8> = s.bytes().map(|c| table[c as usize]).collect();
    let mut out = Vec::new();
    for chunk in bytes.chunks(4) {
        let mut n: u32 = 0;
        for (i, &v) in chunk.iter().enumerate() {
            n |= (v as u32) << (18 - 6 * i);
        }
        out.push(((n >> 16) & 0xFF) as u8);
        if chunk.len() > 2 {
            out.push(((n >> 8) & 0xFF) as u8);
        }
        if chunk.len() > 3 {
            out.push((n & 0xFF) as u8);
        }
    }
    out
}

#[derive(Debug)]
struct VerifyResult {
    ok: bool,
    reason: Option<&'static str>,
}

const SECRET: &[u8] = b"test-signing-key-do-not-use-in-production";

fn extract_json_string(json: &str, key: &str) -> Option<String> {
    let needle = format!("\"{}\":\"", key);
    let start = json.find(&needle)? + needle.len();
    let rest = &json[start..];
    let end = rest.find('"')?;
    Some(rest[..end].to_string())
}

fn extract_json_number(json: &str, key: &str) -> Option<i64> {
    let needle = format!("\"{}\":", key);
    let start = json.find(&needle)? + needle.len();
    let rest = &json[start..];
    let end = rest.find(|c: char| c == ',' || c == '}').unwrap_or(rest.len());
    rest[..end].trim().parse().ok()
}

fn mint_test_token(audience: &str, exp: i64) -> String {
    let header = "{\"alg\":\"HS256\",\"typ\":\"at+jwt\"}".to_string();
    let payload = format!(
        "{{\"iss\":\"https://auth.example.com\",\"sub\":\"user-42\",\"aud\":\"{}\",\"scope\":\"orders:read\",\"exp\":{}}}",
        audience, exp
    );
    let signing_input = format!(
        "{}.{}",
        b64url_encode(header.as_bytes()),
        b64url_encode(payload.as_bytes())
    );
    let sig = hmac_sha256(SECRET, signing_input.as_bytes());
    format!("{}.{}", signing_input, b64url_encode(&sig))
}

fn verify_access_token(token: &str, expected_audience: &str) -> VerifyResult {
    let parts: Vec<&str> = token.split('.').collect();
    if parts.len() != 3 {
        return VerifyResult { ok: false, reason: Some("malformed") };
    }
    let signing_input = format!("{}.{}", parts[0], parts[1]);
    let expected_sig = hmac_sha256(SECRET, signing_input.as_bytes());
    let given_sig = b64url_decode(parts[2]);
    if !constant_time_eq(&expected_sig, &given_sig) {
        return VerifyResult { ok: false, reason: Some("bad_signature") };
    }

    let payload_bytes = b64url_decode(parts[1]);
    let payload = String::from_utf8(payload_bytes).unwrap_or_default();

    let aud = extract_json_string(&payload, "aud").unwrap_or_default();
    if aud != expected_audience {
        return VerifyResult { ok: false, reason: Some("wrong_audience") };
    }

    let exp = extract_json_number(&payload, "exp").unwrap_or(0);
    let now = current_unix_time();
    if exp < now {
        return VerifyResult { ok: false, reason: Some("expired") };
    }

    VerifyResult { ok: true, reason: None }
}

fn current_unix_time() -> i64 {
    match SystemTime::now().duration_since(UNIX_EPOCH) {
        Ok(d) => d.as_secs() as i64,
        Err(_) => 0,
    }
}

fn to_hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{:02x}", b)).collect()
}

fn main() {
    let rfc_key = [0x0bu8; 20];
    let rfc_mac = hmac_sha256(&rfc_key, b"Hi There");
    assert_eq!(
        to_hex(&rfc_mac),
        "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7"
    );

    let now = current_unix_time();
    let token = mint_test_token("orders-service", now + 300);
    println!("issued {}", token);
    println!("verify correct audience {:?}", verify_access_token(&token, "orders-service"));
    println!("verify wrong audience {:?}", verify_access_token(&token, "billing-service"));
}
```

Compile with `rustc --edition 2021 -O access_token.rs`, then run the
binary. SHA-256 and HMAC are implemented directly against FIPS 180-4 and RFC
2104 rather than pulled from a crate, so the sample has zero external
dependencies, and `main` asserts the implementation against the RFC 4231
test vector (key `0x0b` repeated twenty times, message `Hi There`) before
using it to mint and check a token, so a broken hash implementation would
fail the assertion rather than silently mis-signing tokens.
