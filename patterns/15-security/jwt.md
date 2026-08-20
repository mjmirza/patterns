---
name: JWT
slug: jwt
family: 15-security
category: Security
aliases: [JSON Web Token, JOT, Self-contained Token, Signed Claims Token]
first_described: "Jones, Bradley, Sakimura 2015"
maturity: established
related: [token-based-authentication, oauth-2-1-flows, openid-connect, least-privilege, complete-mediation, fail-securely]
incompatible_with: [opaque-token-by-default, server-side-session-only, bearer-token-as-database-record]
verified: 2026-08-02
---

# JWT

## 1. Name, aliases, and lineage

The canonical name is JWT, short for JSON Web Token. RFC 7519 defines it as a
compact, URL-safe way to represent claims between two parties, with the claims
encoded as JSON and carried inside a JSON Web Signature or JSON Web Encryption
structure. The specification was authored by Michael B. Jones, John Bradley,
and Nat Sakimura and published by the IETF in May 2015
([https://www.rfc-editor.org/rfc/rfc7519](https://www.rfc-editor.org/rfc/rfc7519),
verified 2026-08-02).

The common spoken alias is **JOT**. That pronunciation appears in Auth0's JWT
documentation, which treats JWT as an open standard defined by RFC 7519
([https://auth0.com/docs/secure/tokens/json-web-tokens](https://auth0.com/docs/secure/tokens/json-web-tokens),
verified 2026-08-02). Teams also say **signed claims token** when they mean the
JWS form, **self-contained token** when they compare it with an opaque token,
and **ID token** or **JWT access token** when a protocol profile fixes the
token's meaning. OpenID Connect Core defines ID Tokens as JWTs in section 2
([https://openid.net/specs/openid-connect-core-1_0.html](https://openid.net/specs/openid-connect-core-1_0.html),
verified 2026-08-02). RFC 9068 defines a JWT profile for OAuth 2.0 access
tokens
([https://www.rfc-editor.org/rfc/rfc9068.html](https://www.rfc-editor.org/rfc/rfc9068.html),
verified 2026-08-02).

The lineage is the JOSE family of specifications. JWT relies on JWS for signed
or MACed tokens, JWE for encrypted tokens, JWA for algorithm identifiers, and
JWK for JSON key representation. JWS was published as RFC 7515 by Jones,
Bradley, and Sakimura in May 2015
([https://www.rfc-editor.org/info/rfc7515](https://www.rfc-editor.org/info/rfc7515),
verified 2026-08-02). JWK was published as RFC 7517 by Jones in May 2015
([https://www.rfc-editor.org/info/rfc7517](https://www.rfc-editor.org/info/rfc7517),
verified 2026-08-02).

JWT is not authentication by itself. It is a token format. Token-based
Authentication is the broader pattern. OAuth 2.0 is a delegation framework. OIDC
is an identity layer. JWT can appear inside each, but the format does not decide
who may issue tokens, where keys come from, which claims are required, how
revocation works, or what authorization decision follows validation.

## 2. Problem and context

A resource server needs to accept repeated calls without contacting the issuer
for every request, yet it still needs an issuer, subject, audience, expiry,
possibly scopes, and a way to detect tampering. The issuer wants to publish a
credential that a different service can validate locally. The caller wants one
portable value it can present in an HTTP header, a workload identity file, or a
protocol response.

The problem appears when a system moves from one server to many services. With
server-side sessions, every service either shares a session store, calls a
central session service, or gives up on local validation. With opaque access
tokens, RFC 7662 token introspection gives a standard way for a protected
resource to query token state at an authorization server
([https://www.rfc-editor.org/info/rfc7662](https://www.rfc-editor.org/info/rfc7662),
verified 2026-08-02). That works well when the authorization server is near,
available, and part of the hot path design. It becomes harder when many resource
servers sit in different regions, run inside customer clusters, or need to
continue during a short issuer outage.

JWT answers by moving validation material into the token. The resource server
decodes the compact serialization, checks the protected header and signature,
validates claims such as issuer, subject, audience, expiry, and not-before, then
maps the result to a local authorization decision. RFC 7519 defines registered
claims including `iss`, `sub`, `aud`, `exp`, `nbf`, `iat`, and `jti` in section
4.1
([https://www.rfc-editor.org/rfc/rfc7519](https://www.rfc-editor.org/rfc/rfc7519),
verified 2026-08-02).

The context must be narrow. JWT suits bounded trust between issuers and
verifiers. The issuer and verifier need an agreed issuer identifier, key
distribution path, accepted algorithms, clock skew policy, audience values,
claim meanings, and token lifetime. RFC 8725 was published as a Best Current
Practice because JWT deployments had seen widely publicized implementation and
usage attacks, and it updates RFC 7519 with deployment guidance
([https://www.rfc-editor.org/rfc/rfc8725.html](https://www.rfc-editor.org/rfc/rfc8725.html),
verified 2026-08-02).

Engineering judgement. JWT is most useful when local verification is worth the
discipline of key rotation, claim validation, and short lifetimes. It is a poor
fit when the team mainly wants to avoid a database lookup, because the lookup
often returns later as a revocation list, tenant state check, or permission
freshness check.

## 3. Forces

Engineering judgement. This pattern trades issuer round trips for validation
discipline at every verifier.

- **Latency.** Favoured. A verifier can validate a signed token without a
  per-request network call to the issuer, after it has the signing key.
- **Coupling.** Mixed. Runtime coupling to the issuer drops on the request path,
  but schema coupling rises because every verifier must interpret the same
  claims and audience rules.
- **Consistency.** Sacrificed. A token can remain valid until expiry even after
  the user's role, device, tenant, or account state changes, unless the verifier
  performs a fresh check.
- **Operability.** Sacrificed unless designed. Key rotation, `kid` lookup, clock
  skew, issuer metadata, and token size all become production concerns.
- **Cost.** Favoured for high-volume reads because validation is local. Cost can
  rise when large tokens inflate request headers, logs, traces, and cache keys.
- **Team topology.** Favoured when an identity platform team owns issuance and
  product teams own resource servers. Sacrificed when every team invents private
  claims.
- **Cognitive load.** Sacrificed. Developers must separate decoding from
  verification, signature validity from authorization, and signed data from
  confidential data.
- **Privacy.** Often sacrificed. A signed JWT is not encrypted. Anyone who gets
  the token can read its claims unless JWE or another confidentiality layer is
  used. RFC 7519 section 12 says privacy-sensitive information in a JWT needs
  measures that prevent unintended disclosure
  ([https://www.rfc-editor.org/rfc/rfc7519](https://www.rfc-editor.org/rfc/rfc7519),
  verified 2026-08-02).
- **Security failure blast radius.** Mixed. Asymmetric signatures can let many
  verifiers validate without holding the issuer's private key. A stolen bearer
  JWT can still be replayed until expiry unless sender constraints or a server
  state check limits it.

## 4. Applicability and non-applicability

Reach for JWT when the following hold.

- A resource server must verify a token locally and can tolerate authorization
  data that is fresh only within the token lifetime.
- The issuer and verifier have a stable trust relationship, including a known
  issuer identifier, expected audience, allowed algorithms, and a key rotation
  process.
- The token is short-lived enough that expiry is an acceptable revocation
  backstop.
- The claims are small, stable, and safe for the token holder to read.
- Asymmetric signing reduces key sharing risk because verifiers need public keys
  rather than a shared MAC secret.
- A standard profile already demands JWT, such as OpenID Connect ID Tokens or
  RFC 9068 JWT access tokens.
- Workload identity needs a portable signed credential that an external trust
  system can validate, such as Kubernetes projected service account tokens.

Do NOT reach for JWT in these cases.

- **Immediate revocation is mandatory.** A self-contained token does not ask the
  issuer about current state on each request. Use opaque tokens with
  introspection, server-side sessions, or a revocation-aware gateway.
- **The client must not read the claims.** A signed JWT is visible to whoever
  holds it. Use JWE, opaque tokens, or omit the data.
- **Permissions change on nearly every request.** Put volatile authorization
  state behind a policy check rather than inside the token.
- **The issuer and verifier do not agree on claim semantics.** Private claims
  become a fragile cross-team API. Use a profile, registry, or central policy
  service.
- **The token crosses browsers, proxies, and logs with large claim sets.** Header
  size, referrer leaks, storage rules, and log retention may become the actual
  risk.
- **One service both issues and verifies all calls.** A random session id stored
  server side may be easier to rotate, revoke, and reason about.
- **The team plans to hand-roll cryptography.** JWT validation includes
  base64url, JSON parsing, algorithm allow-listing, key selection, time checks,
  and audience checks. Use a maintained library in production.
- **Symmetric signing requires sharing one secret with many verifiers.** One
  leaked verifier secret becomes an issuer. Prefer asymmetric signing or opaque
  tokens.
- **Long-lived offline bearer credentials are required.** A JWT used as a
  months-long API key combines bearer replay risk with hard rotation. Use a key
  record, hashed at rest, with scoped rotation.

## 5. Structure

The participants are named by their security role.

- **Issuer.** Creates the claims set, selects the signing key, sets the JOSE
  header, signs or encrypts the token, and publishes validation metadata. In
  OAuth and OIDC deployments this is often the authorization server or identity
  provider.
- **Subject.** The entity the claims describe. It can be a user, service
  account, workload, device, or client application.
- **Client or presenter.** Holds the token and sends it to a verifier. For a
  bearer token, possession is enough to present it.
- **Verifier.** Receives the token, validates its syntax, cryptographic
  protection, issuer, audience, time claims, and profile rules, then exposes a
  validated principal to authorization code.
- **Key source.** Supplies verification keys. In OIDC deployments this is often
  a JWKS endpoint discovered from issuer metadata.
- **Claims policy.** Maps validated claims to local permissions. It is separate
  from signature validation because a valid token can still be wrong for this
  API, tenant, operation, or resource.
- **Clock.** Supplies current time for `exp`, `nbf`, and `iat` checks. Clock
  drift is a real participant because JWT validation is time-sensitive.

The compact signed form has three base64url parts separated by periods. The
first part is the protected JOSE header, the second is the claims set, and the
third is the signature. RFC 7519 section 3 describes JWTs as URL-safe parts
separated by period characters, with the number of parts depending on whether
the representation is JWS or JWE
([https://www.rfc-editor.org/rfc/rfc7519](https://www.rfc-editor.org/rfc/rfc7519),
verified 2026-08-02).

## 6. ASCII structure diagram

```text
      issues                                         validates
  +-------------+       JWT compact string        +--------------+
  |   Issuer    |  ---------------------------->  |   Verifier   |
  |-------------|                                 |--------------|
  | signing key |                                 | alg allowlist |
  | claims set  |                                 | issuer check  |
  | lifetime    |                                 | aud check     |
  +------+------+                                 | time check    |
         |                                        +------+-------+
         | publishes                                     |
         v                                               v
  +-------------+                                 +--------------+
  | Key Source  |  ---------------------------->  | Claims Policy|
  |-------------|       JWKS or configured key    |--------------|
  | kid -> key  |                                 | scope -> ACL  |
  | rotation    |                                 | tenant rules  |
  +-------------+                                 +--------------+

  Signed compact JWT

  +----------------+ . +----------------+ . +-------------------+
  | JOSE header    |   | claims set     |   | signature or MAC  |
  | alg, kid, typ  |   | iss, sub, aud  |   | over first two    |
  +----------------+   +----------------+   +-------------------+
```

## 7. Dynamics

At runtime, JWT validation is a pipeline. The verifier must treat each stage as
able to reject. A successful signature check is not a successful authorization
decision.

```text
Client          Verifier          Key Source        Claims Policy
  |                |                   |                  |
  |-- Bearer JWT ->|                   |                  |
  |                | parse segments    |                  |
  |                | read header       |                  |
  |                | reject bad alg    |                  |
  |                |-- key by kid ---->|                  |
  |                |<-- public key ----|                  |
  |                | verify signature  |                  |
  |                | check iss, aud    |                  |
  |                | check exp, nbf    |                  |
  |                |-- claims -------->|                  |
  |                |<-- decision ------|                  |
  |<-- allow/deny -|                   |                  |
```

The issuer side is shorter but no less strict. It builds the claims set,
chooses a profile, chooses a key and algorithm from a configured allow-list,
sets a tight expiry, signs, and returns the compact token. RFC 8725 section 3.1
says libraries must let callers specify supported algorithms and must not use
others during cryptographic operations
([https://www.rfc-editor.org/rfc/rfc8725.html](https://www.rfc-editor.org/rfc/rfc8725.html),
verified 2026-08-02). RFC 8725 section 3.8 says applications must validate that
keys used for JWT cryptographic operations belong to the issuer when an issuer
claim is present
([https://www.rfc-editor.org/rfc/rfc8725.html](https://www.rfc-editor.org/rfc/rfc8725.html),
verified 2026-08-02).

The following minimal examples show the validation shape. Python and Go use
HMAC with standard libraries. Swift keeps to compact parsing and claim checking
because production signature validation should come from a maintained JWT
library or a security framework chosen by the application. Production systems
should prefer a maintained JWT library and asymmetric keys where many services
verify tokens.

```python
import base64
import hashlib
import hmac
import json
import time

SECRET = b"32-bytes-minimum-demo-secret-value"

def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def sign(data: str) -> str:
    mac = hmac.new(SECRET, data.encode("ascii"), hashlib.sha256).digest()
    return b64url(mac)

def issue() -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "iss": "https://issuer.example",
        "sub": "user-123",
        "aud": "orders-api",
        "exp": int(time.time()) + 300,
        "scope": "orders:read",
    }
    head = b64url(json.dumps(header, separators=(",", ":")).encode())
    body = b64url(json.dumps(payload, separators=(",", ":")).encode())
    return f"{head}.{body}.{sign(head + '.' + body)}"

def verify(token: str) -> dict:
    head, body, got = token.split(".")
    if not hmac.compare_digest(sign(head + "." + body), got):
        raise ValueError("bad signature")
    header = json.loads(base64.urlsafe_b64decode(head + "=="))
    if header.get("alg") != "HS256":
        raise ValueError("bad algorithm")
    claims = json.loads(base64.urlsafe_b64decode(body + "=="))
    if claims.get("iss") != "https://issuer.example":
        raise ValueError("bad issuer")
    if claims.get("aud") != "orders-api":
        raise ValueError("bad audience")
    if claims.get("exp", 0) < int(time.time()):
        raise ValueError("expired")
    return claims

token = issue()
print(verify(token)["sub"])
```

```go
package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

var secret = []byte("32-bytes-minimum-demo-secret-value")

func b64(data []byte) string {
	return base64.RawURLEncoding.EncodeToString(data)
}

func sig(data string) string {
	mac := hmac.New(sha256.New, secret)
	mac.Write([]byte(data))
	return b64(mac.Sum(nil))
}

func main() {
	header, _ := json.Marshal(map[string]string{"alg": "HS256", "typ": "JWT"})
	claims, _ := json.Marshal(map[string]any{
		"iss": "https://issuer.example",
		"sub": "svc-billing",
		"aud": "ledger-api",
		"exp": time.Now().Add(5 * time.Minute).Unix(),
	})
	data := b64(header) + "." + b64(claims)
	token := data + "." + sig(data)
	parts := strings.Split(token, ".")
	if len(parts) != 3 || !hmac.Equal([]byte(sig(parts[0]+"."+parts[1])), []byte(parts[2])) {
		panic("bad token")
	}
	var out map[string]any
	body, _ := base64.RawURLEncoding.DecodeString(parts[1])
	json.Unmarshal(body, &out)
	if out["aud"] != "ledger-api" {
		panic("bad audience")
	}
	fmt.Println(out["sub"])
}
```

```swift
import Foundation

func b64url(_ data: Data) -> String {
    data.base64EncodedString()
        .replacingOccurrences(of: "+", with: "-")
        .replacingOccurrences(of: "/", with: "_")
        .replacingOccurrences(of: "=", with: "")
}

func encode(_ value: String) -> String {
    b64url(Data(value.utf8))
}

let header = #"{"alg":"demo","typ":"JWT"}"#
let claims = #"{"iss":"https://issuer.example","sub":"ios-client","aud":"mobile-api"}"#
let token = "\(encode(header)).\(encode(claims)).demo-signature"
let parts = token.split(separator: ".")

guard parts.count == 3 else {
    fatalError("bad token")
}

let padded = String(parts[1]).padding(
    toLength: ((parts[1].count + 3) / 4) * 4,
    withPad: "=",
    startingAt: 0
)
let standard = padded
    .replacingOccurrences(of: "-", with: "+")
    .replacingOccurrences(of: "_", with: "/")
let body = String(data: Data(base64Encoded: standard)!, encoding: .utf8)!

guard body.contains(#""aud":"mobile-api""#) else {
    fatalError("bad audience")
}

print(body.contains(#""sub":"ios-client""#))
```

## 8. Implementation variants

**Signed JWT, JWS compact serialization.** This is the common bearer-token form.
The token carries readable claims and a signature or MAC over the header and
payload. It proves integrity and issuer control of the signing key. It does not
hide claims.

**Encrypted JWT, JWE compact serialization.** The token hides claims from the
presenter and intermediaries. RFC 7519 allows claims to be carried as the
plaintext of a JWE structure
([https://www.rfc-editor.org/rfc/rfc7519](https://www.rfc-editor.org/rfc/rfc7519),
verified 2026-08-02). The cost is more key management and harder debugging.

**Nested JWT.** A signed JWT is then encrypted, or an encrypted object is signed
according to the surrounding profile. OpenID Connect Core section 2 says that if
an ID Token is encrypted, it must be signed then encrypted, producing a Nested
JWT as defined by JWT
([https://openid.net/specs/openid-connect-core-1_0.html](https://openid.net/specs/openid-connect-core-1_0.html),
verified 2026-08-02).

**Symmetric MAC, such as HS256.** Issuer and verifier share one secret. It is
fast and simple for one issuer and one verifier. It scales poorly across many
verifiers because any verifier with the secret can mint tokens.

**Asymmetric signature, such as RS256 or ES256.** The issuer holds the private
key and verifiers hold public keys. RFC 9068 section 2.1 recommends asymmetric
cryptography for JWT access tokens because it simplifies acquiring validation
information for resource servers
([https://www.rfc-editor.org/rfc/rfc9068.html](https://www.rfc-editor.org/rfc/rfc9068.html),
verified 2026-08-02). The cost is key publication, caching, rotation, and slower
cryptography than HMAC.

**OIDC ID Token.** The token represents an authentication event and user
identity for a client. Google's OpenID Connect API reference says the
`id_token` value returned in responses is a signed JWT that must be verified
using keying material from the `jwks_uri` in the Discovery Document
([https://developers.google.com/identity/openid-connect/reference](https://developers.google.com/identity/openid-connect/reference),
verified 2026-08-02).

**OAuth JWT access token profile.** RFC 9068 gives a profile for access tokens
in JWT format, including header and claim rules. It also states that OAuth 2.0
access tokens remain opaque to clients as a framework assumption
([https://www.rfc-editor.org/rfc/rfc9068.html](https://www.rfc-editor.org/rfc/rfc9068.html),
verified 2026-08-02).

**Workload identity token.** Kubernetes ServiceAccounts use signed JWTs to
authenticate to the Kubernetes API server and systems with a trust relationship,
according to Kubernetes service account documentation
([https://kubernetes.io/docs/concepts/security/service-accounts/](https://kubernetes.io/docs/concepts/security/service-accounts/),
verified 2026-08-02). The token acts as a machine identity rather than a user
session.

**Profile-bound token.** A JWT profile is a contract that narrows the generic
format. It names the token kind, required claims, media type or `typ` value,
issuer rules, audience rules, and validation behavior. This is why an OIDC ID
Token and an OAuth access token should not share one validation function. RFC
8725 section 3.12 calls for mutually exclusive validation rules for different
kinds of JWTs
([https://www.rfc-editor.org/rfc/rfc8725.html](https://www.rfc-editor.org/rfc/rfc8725.html),
verified 2026-08-02). Engineering judgement. A verifier should have separate
configuration objects for ID tokens, access tokens, workload tokens, and
internal service tokens, even when all four are signed by the same issuer.

**Gateway-validated JWT.** An API gateway or service mesh validates the JWT at
the edge and forwards selected claims to upstream services. This reduces
duplicate parsing work and can centralize key fetches. It also creates a new
trust boundary. Upstream services must either trust the gateway as an
authenticating proxy or repeat validation for high-risk routes. Engineering
judgement. This variant is acceptable only when forwarded identity headers are
stripped from inbound traffic before the gateway adds them, and when upstream
services can tell gateway traffic from direct traffic.

**Reference-token hybrid.** The JWT carries stable identity claims and a token
identifier, while high-risk authorization data stays server side. The verifier
does local signature and audience validation, then checks the token id or
subject state only for operations that need fresh policy. This hybrid gives up
some latency benefit, but it avoids putting fast-changing permissions into a
portable credential.

**Detached or sender-constrained token.** The JWT can be bound to another proof,
such as a client certificate or proof key, by profile. This reduces replay if a
token leaks, but adds cryptographic and protocol work outside base JWT.

## 9. Known production uses

**Google Sign-In and Google OpenID Connect.** Google's OpenID Connect reference
states that an `id_token` returned in responses is a signed JWT and that the
application must verify it using keys found through the discovery document's
`jwks_uri`
([https://developers.google.com/identity/openid-connect/reference](https://developers.google.com/identity/openid-connect/reference),
verified 2026-08-02). This is a large production identity use where JWT carries
issuer, subject, audience, expiry, and profile claims to the relying party.

**Microsoft identity platform ID tokens.** Microsoft documents v1.0 and v2.0 ID
tokens as JWTs. The documentation describes header claims such as `typ`, `alg`,
and `kid`, and says the audience in an ID token identifies the intended
recipient and should be validated
([https://learn.microsoft.com/en-us/entra/identity-platform/id-token-claims-reference](https://learn.microsoft.com/en-us/entra/identity-platform/id-token-claims-reference),
verified 2026-08-02).

**Kubernetes ServiceAccount tokens.** Kubernetes documentation states that
ServiceAccounts use signed JWTs to authenticate to the Kubernetes API server and
other systems where a trust relationship exists
([https://kubernetes.io/docs/concepts/security/service-accounts/](https://kubernetes.io/docs/concepts/security/service-accounts/),
verified 2026-08-02). Amazon EKS documents projected service account tokens as
OIDC JWTs and explains that EKS hosts a public OIDC discovery endpoint with
signing keys so external systems can validate tokens
([https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html),
verified 2026-08-02).

**GitHub Apps.** GitHub's documentation says a GitHub App must generate a JWT to
authenticate as the app or generate an installation access token, and that the
JWT must be signed using `RS256` with `iat`, `exp`, and `iss` claims
([https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app),
verified 2026-08-02).

## 10. Consequences

Engineering judgement.

Positive.

- Resource servers can validate many requests without a hot-path issuer call.
- The token can carry a compact set of claims that every verifier can process
  with standard JSON tooling.
- Asymmetric signing lets the issuer keep private keys out of resource servers.
- Standard claims and JOSE headers make cross-vendor identity flows possible
  when profiles are followed.
- Token lifetime can be short without forcing user reauthentication when refresh
  or token exchange flows exist.
- The `kid` header gives a practical path for key rotation when verifiers fetch
  a current JWKS.

Negative.

- Revocation is delayed unless the verifier checks server-side state.
- Claim meanings become a public contract between issuer and verifier.
- Signed tokens expose their payload to the presenter and any component that
  records them.
- Token size can break headers, bloat logs, and increase request cost.
- Every verifier must get validation right. One verifier that accepts a bad
  algorithm, wrong issuer, wrong audience, or expired token becomes a bypass.
- Symmetric signing across many services turns every verifier into a party able
  to forge tokens.
- Key rotation incidents can deny service across every resource server that
  depends on the issuer.

## 11. Failure modes and misuse

Engineering judgement.

**Decoded but not verified.** Symptom. A user can change `sub`, `role`, or
`scope` in the payload and gain access in one service while other services deny
the token. Cause. Code uses a decode helper and treats parsed JSON as trusted.
Fix. Replace decode-only paths with verification that checks signature,
algorithm, issuer, audience, and time claims before claims reach application
logic.

**Algorithm confusion.** Symptom. Tokens signed with an unexpected algorithm or
with `none` pass in one verifier but fail in others. Cause. The verifier trusts
the token header to select verification behavior. Fix. Configure an allow-list
per issuer and key, and reject any header outside that list. RFC 8725 section
3.1 requires algorithm verification support by libraries
([https://www.rfc-editor.org/rfc/rfc8725.html](https://www.rfc-editor.org/rfc/rfc8725.html),
verified 2026-08-02).

**Wrong audience accepted.** Symptom. A token minted for one API works against
another API. Cause. Signature validation is performed, but `aud` is ignored or
treated as advisory. Fix. Give every API a stable audience value and reject
tokens without an exact accepted audience.

**Issuer mix-up.** Symptom. A token from a test tenant, partner tenant, or
attacker-controlled issuer is accepted because it uses a known algorithm. Cause.
Key lookup is not bound to the expected issuer. Fix. Pin issuer identifiers and
select keys only from that issuer's configured metadata.

**Stale authorization.** Symptom. A removed user or disabled service account
continues to call an API until token expiry. Cause. The JWT is self-contained
and the verifier does not check current account state. Fix. Shorten lifetime,
check high-risk actions against current state, or use introspection for grants
that need rapid revocation.

**Secret claim exposure.** Symptom. Tokens in browser storage, logs, or support
tickets reveal email addresses, groups, tenant names, or internal identifiers.
Cause. The team confused signed with encrypted. Fix. Treat JWS payloads as
readable, omit sensitive claims, or use JWE when a profile and key management
plan support it.

**Weak HMAC secret.** Symptom. Attackers can forge tokens after obtaining one
sample token and cracking a human-chosen secret offline. Cause. HS256 uses a
low-entropy string. Fix. Use a random secret with adequate entropy, or move to
asymmetric signing. RFC 8725 section 2.2 describes weak symmetric keys as a JWT
threat
([https://www.rfc-editor.org/rfc/rfc8725.html](https://www.rfc-editor.org/rfc/rfc8725.html),
verified 2026-08-02).

**Key rotation race.** Symptom. A deployment suddenly returns many 401 errors
after the issuer rotates keys. Cause. Verifiers cache JWKS too long, ignore
`kid`, or fail closed on a transient JWKS fetch. Fix. Cache keys with expiry,
refresh on unknown `kid`, retain old keys until all issued tokens expire, and
alarm on key lookup failures.

**Authorization from claims alone.** Symptom. A token with `scope=admin` grants
access to a tenant resource that the subject does not own. Cause. The verifier
maps a broad claim directly to resource access without object-level checks. Fix.
Keep complete mediation at the resource boundary. Use claims as inputs to policy,
not as the whole policy.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | JWT | Opaque token with introspection | Server-side session cookie | PASETO | SAML assertion |
|---|---|---|---|---|---|
| Latency | Local validation after key fetch | Network call or cache | Session store lookup | Local validation | Local validation or federation stack |
| Revocation freshness | Weak until expiry unless state check exists | Strong when introspected | Strong through session store | Weak until expiry unless state check exists | Profile-dependent |
| Privacy | Signed form exposes claims | Claims stay server side | Session data stays server side | Depends on local or public mode | Often verbose, may be encrypted |
| Coupling | High claim schema coupling | High issuer availability coupling | High session store coupling | Lower algorithm choice, less standard ecosystem | High XML and federation profile coupling |
| Operability | Key rotation and claim drift | Introspection availability and cache policy | Store scaling and cookie policy | Library availability and key policy | Certificate, XML, and metadata handling |
| Token size | Medium, can grow large | Small | Small cookie id, unless cookie stores data | Similar to JWT for claims | Large |
| Multi-service fit | Strong when profiles are stable | Strong when issuer is reliable | Weak outside one web domain | Good inside controlled systems | Strong in enterprise federation |
| Browser fit | Risky in local storage, careful in cookies | Same bearer concerns | Strong with HttpOnly and SameSite | Same bearer concerns | Rare for direct browser API calls |
| Team topology | Good for platform issuer and many verifiers | Good with central auth team | Good for one web app team | Good for one platform with strict library rules | Good where identity federation team owns stack |

Reading of the table. JWT wins when local verification and standard identity
interoperability matter more than instant revocation. Opaque tokens win when
the issuer must keep full control over token state. Server-side sessions win
inside a single browser application. PASETO can reduce algorithm confusion by
removing attacker-selected algorithm agility, but it lacks JWT's standard OIDC
and OAuth profile adoption. SAML remains relevant where enterprise federation
contracts already depend on XML assertions.

## 13. Related and incompatible patterns

- **Token-based Authentication.** JWT is one concrete token format inside the
  broader pattern. The larger pattern covers bearer handling, lifetimes,
  storage, rotation, and presentation.
- **OAuth 2.1 Flows.** OAuth flows can issue JWT access tokens, but OAuth does
  not require JWT for every access token. RFC 6749 says an access token may be
  an identifier used to retrieve authorization information or may self-contain
  authorization information in a verifiable manner
  ([https://www.rfc-editor.org/info/rfc6749](https://www.rfc-editor.org/info/rfc6749),
  verified 2026-08-02).
- **OpenID Connect.** OIDC composes strongly with JWT because ID Tokens are JWTs
  by specification. The OIDC profile supplies claim meanings, discovery, and key
  rules that base JWT does not supply.
- **Least Privilege.** JWT works well with narrow scopes, narrow audiences, and
  short lifetimes. It works against least privilege when teams put broad roles
  or all permissions into one reusable bearer token.
- **Complete Mediation.** Every protected request still needs authorization at
  the resource boundary. A valid JWT is an input to mediation, not a replacement
  for it.
- **Fail Securely.** JWT validation must fail closed on malformed tokens,
  unknown issuers, unknown keys, expired claims, unsupported algorithms, and bad
  audiences.
- **Defense in Depth.** Sender-constrained tokens, TLS, gateway validation,
  short lifetime, object-level authorization, and logging controls compose with
  JWT. None of them replaces validation in the resource server.
- **Opaque Token.** This is the main substitute. It hides claims and centralizes
  state, at the cost of an issuer lookup or cache.
- **Server-side Session.** This substitutes for JWT in browser-only apps where a
  session store is cheap and revocation matters.
- **Service Locator.** Conflicts when verifiers fetch issuer and audience policy
  from global mutable state. Token validation policy should be explicit per
  resource server.

## 14. Refactoring path in and out

Introducing JWT into a system that uses opaque tokens.

1. Inventory every resource server that accepts the current token. Record issuer
   dependency, cache behavior, current revocation requirements, and required
   identity attributes.
2. Define one token profile before code changes. Name issuer, audience values,
   allowed algorithms, lifetime, key source, required claims, optional claims,
   and error behavior.
3. Add a validation library to one resource server behind a feature flag. Accept
   both the opaque token and the JWT during the migration.
4. Issue JWTs only for one audience and one client class. Keep lifetimes short.
5. Add telemetry for validation outcome, issuer, audience, algorithm, `kid`, and
   token age. Do not log token bodies.
6. Move authorization logic to consume a validated principal object, not raw
   claims maps. This is Extract Function and Introduce Parameter Object from the
   refactoring family.
7. Roll to more resource servers only after unknown key, bad audience, and
   expiry failures are visible and boring.
8. Remove opaque-token acceptance only after clients have rotated and old tokens
   have expired.

Removing JWT when it stops earning its place.

1. Identify why it failed. Common reasons are instant revocation, privacy, large
   claims, issuer drift, and inconsistent verifier code.
2. Add an opaque token issue path that stores token metadata server side, with a
   hash of the presented token rather than plaintext.
3. Add introspection or a session lookup to verifiers. Cache responses only
   within the revocation window the business accepts.
4. Translate JWT claims into the server-side token record, keeping only claims
   resource servers actually use.
5. Accept both formats during a short migration. Prefer separate token prefixes
   or content type hints so verifiers do not guess.
6. Retire JWT signing keys after the longest token lifetime plus clock skew.
7. Delete raw-claim authorization paths and keep the validated principal
   abstraction.

## 15. Testing and verification

Engineering judgement.

Tests should prove rejection as much as acceptance. A JWT verifier with only a
happy-path test is unfinished.

- **Golden valid token.** Generate a token with the test issuer key and verify
  that the resource server maps it to the expected principal.
- **Signature mutation.** Change one byte of the payload and assert rejection.
- **Algorithm rejection.** Send a token with `alg` set to `none` or an
  unsupported algorithm and assert rejection before claims are trusted.
- **Issuer rejection.** Sign with a valid key from the wrong issuer and assert
  rejection.
- **Audience rejection.** Use a token for another API and assert rejection.
- **Time rejection.** Test expired, not-yet-valid, and near-expiry tokens with a
  fake clock.
- **Key rotation.** Test current `kid`, previous `kid`, and unknown `kid`.
- **Claim contract.** Use property tests or table tests for scope, tenant, and
  subject mapping.
- **Fuzz syntax.** Send malformed base64url, missing segments, duplicate JSON
  keys when the parser exposes them, and oversized tokens.
- **No raw token logging.** Unit-test error paths and middleware logs so token
  strings are redacted.

The test matrix should also cover profile separation. Feed an ID token into an
access-token verifier and assert rejection. Feed an access token into a session
verifier and assert rejection. Feed a workload token into a user endpoint and
assert rejection. These tests catch the "valid token, wrong purpose" class that
signature-only tests miss. They also document the policy contract for future
teams that add issuers or token types.

Verification in production should mirror these tests. Canary tokens with wrong
audience, expired `exp`, and unknown `kid` can be sent to non-user endpoints to
confirm fail-secure behavior. The code examples above were compiled or run with
the local toolchains before this entry was completed.

## 16. Observability signals

Engineering judgement.

A healthy JWT deployment is quiet and predictable. The dashboard should show
the accepted issuer set, token profile versions, `kid` distribution, token age
at validation, validation latency, and rejection counts by reason.

Record these fields for validation failures: service name, route family, issuer
if parseable, audience if parseable, `kid` if parseable, algorithm if parseable,
failure reason, and correlation id. Do not record the compact token or raw
claims. For successful validation, sample issuer, audience, `kid`, token age,
subject type, and scope count. Avoid subject values in high-cardinality metrics.

Healthy signals.

- Rejection reasons are stable and mostly expired tokens or missing tokens.
- Unknown `kid` spikes appear only during planned rotation and fall quickly.
- Token age stays well below lifetime for normal clients.
- Audience distribution matches deployed services.
- Validation latency is small compared with request latency.

Failing signals.

- Bad signature counts rise after a deploy. This points to key mismatch,
  issuer mix-up, or a broken client.
- Unknown issuer appears. This may be configuration drift or attempted token
  substitution.
- Wrong audience rises on one service. This usually means a client is calling
  the wrong API or a gateway is forwarding tokens across boundaries.
- Expired token errors spike. This may be clock drift, refresh failure, or a
  client retrying stale credentials.
- Header size errors appear at proxies. This means claim size has become an
  operational problem.
- JWKS fetch failures correlate with 401s. This means key cache policy is not
  resilient enough for issuer or network faults.

## 17. Security and privacy implications

Base JWT closes one surface and opens others. It closes tampering of the claims
set when cryptographic validation is correct. It opens bearer replay, claim
exposure, key discovery, key rotation, and cross-service interpretation risks.

Do not confuse integrity with secrecy. RFC 7519 section 12 says omitting
privacy-sensitive information from a JWT is the simplest way to minimize privacy
issues
([https://www.rfc-editor.org/rfc/rfc7519](https://www.rfc-editor.org/rfc/rfc7519),
verified 2026-08-02). If a support bundle, browser extension, reverse proxy, or
mobile crash report can see the token, it can read signed JWT claims.

Do not let the token choose the trust policy. The verifier's configuration must
choose issuers, algorithms, audiences, and keys. RFC 8725 section 3.10 says
received claims must not be trusted without verification and validation
([https://www.rfc-editor.org/rfc/rfc8725.html](https://www.rfc-editor.org/rfc/rfc8725.html),
verified 2026-08-02). RFC 8725 section 3.12 also calls for mutually exclusive
validation rules for different JWT kinds
([https://www.rfc-editor.org/rfc/rfc8725.html](https://www.rfc-editor.org/rfc/rfc8725.html),
verified 2026-08-02).

Protect bearer tokens as credentials. Use TLS, avoid URLs, redact logs, prefer
HttpOnly and SameSite cookies for browser storage when the architecture uses
cookies, and bind tokens to clients when the profile supports it. Keep access
tokens short-lived. Keep refresh tokens out of resource server logs and away
from browser JavaScript.

Use asymmetric signing when many independent verifiers exist. With HMAC, every
verifier can forge. With RSA or ECDSA, verifiers can validate while the issuer
keeps the private key. Still, asymmetric signing does not fix claim misuse,
overbroad scopes, or stolen bearer tokens.

Treat key rotation as a security feature and an availability risk. Publish keys
before issuing tokens with them. Retain old public keys until old tokens expire.
Alarm on unknown `kid`, stale JWKS, and multiple issuers sharing a key id.

Constrain where tokens can travel. Do not put JWTs in query strings, because
URLs move through browser history, proxy logs, analytics systems, and referrer
headers. Do not put long-lived JWTs in mobile crash reports or command-line
debug output. Do not allow downstream services to forward a user token to any
service whose audience is not named in the token. A token that is accepted by
too many services is a lateral movement tool.

Keep authorization local to the protected resource. Scopes and groups describe
the caller, but the resource still decides whether that caller may act on that
object at that time. Engineering judgement. The most damaging JWT bugs in
application code are often not cryptographic. They are confused audience,
confused tenant, and confused object ownership bugs after cryptography passed.

## 18. References

- Michael B. Jones, John Bradley, Nat Sakimura, RFC 7519, "JSON Web Token
  (JWT)", May 2015, sections 3, 4.1, 11, and 12,
  [https://www.rfc-editor.org/rfc/rfc7519](https://www.rfc-editor.org/rfc/rfc7519),
  verified 2026-08-02.
- Michael B. Jones, John Bradley, Nat Sakimura, RFC 7515, "JSON Web Signature
  (JWS)", May 2015, sections 3 and 4,
  [https://www.rfc-editor.org/info/rfc7515](https://www.rfc-editor.org/info/rfc7515),
  verified 2026-08-02.
- Michael B. Jones, RFC 7517, "JSON Web Key (JWK)", May 2015, sections 2 and 4,
  [https://www.rfc-editor.org/info/rfc7517](https://www.rfc-editor.org/info/rfc7517),
  verified 2026-08-02.
- Yaron Sheffer, Dick Hardt, Michael B. Jones, RFC 8725, "JSON Web Token Best
  Current Practices", February 2020, sections 2.2, 3.1, 3.8, 3.10, and 3.12,
  [https://www.rfc-editor.org/rfc/rfc8725.html](https://www.rfc-editor.org/rfc/rfc8725.html),
  verified 2026-08-02.
- Vittorio Bertocci, RFC 9068, "JSON Web Token (JWT) Profile for OAuth 2.0
  Access Tokens", October 2021, sections 1 and 2.1,
  [https://www.rfc-editor.org/rfc/rfc9068.html](https://www.rfc-editor.org/rfc/rfc9068.html),
  verified 2026-08-02.
- Justin Richer, RFC 7662, "OAuth 2.0 Token Introspection", October 2015,
  sections 1 and 2,
  [https://www.rfc-editor.org/info/rfc7662](https://www.rfc-editor.org/info/rfc7662),
  verified 2026-08-02.
- Dick Hardt, RFC 6749, "The OAuth 2.0 Authorization Framework", October 2012,
  sections 1.1 and 1.4,
  [https://www.rfc-editor.org/info/rfc6749](https://www.rfc-editor.org/info/rfc6749),
  verified 2026-08-02.
- OpenID Foundation, "OpenID Connect Core 1.0 incorporating errata set 2",
  sections 2 and 16.14,
  [https://openid.net/specs/openid-connect-core-1_0.html](https://openid.net/specs/openid-connect-core-1_0.html),
  verified 2026-08-02.
- Google for Developers, "Google OpenID Connect API Reference", ID Token
  claims section,
  [https://developers.google.com/identity/openid-connect/reference](https://developers.google.com/identity/openid-connect/reference),
  verified 2026-08-02.
- Microsoft Learn, "ID token claims reference, Microsoft identity platform",
  header and payload claims sections,
  [https://learn.microsoft.com/en-us/entra/identity-platform/id-token-claims-reference](https://learn.microsoft.com/en-us/entra/identity-platform/id-token-claims-reference),
  verified 2026-08-02.
- Kubernetes Documentation, "Service Accounts", authenticating service account
  credentials section,
  [https://kubernetes.io/docs/concepts/security/service-accounts/](https://kubernetes.io/docs/concepts/security/service-accounts/),
  verified 2026-08-02.
- Amazon Web Services, "IAM roles for service accounts, Amazon EKS", OIDC
  background section,
  [https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html),
  verified 2026-08-02.
- GitHub Docs, "Generating a JSON Web Token (JWT) for a GitHub App", about
  JSON Web Tokens section,
  [https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app),
  verified 2026-08-02.
