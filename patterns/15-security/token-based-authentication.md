---
name: Token-based Authentication
slug: token-based-authentication
family: 15-security
category: Security
aliases: [Bearer Token Authentication, Access Token Authentication, Token Auth]
first_described: "IETF OAuth 2.0 and Bearer Token specifications, 2012"
maturity: established
related: [least-privilege, zero-trust, secure-by-default, complete-mediation]
incompatible_with: [password-per-request, implicit-session-authority]
verified: 2026-08-02
---

# Token-based Authentication

## 1. Name, aliases, and lineage

The canonical name is Token-based Authentication. In deployed HTTP systems it
is often called Bearer Token Authentication, Access Token Authentication, API
Token Authentication, or Token Auth. The precise term depends on the token's
job. OAuth calls the credential used at a resource server an access token, and
defines roles for resource owner, client, authorization server, and resource
server in RFC 6749, sections 1.1 and 1.4
([https://www.rfc-editor.org/rfc/rfc6749](https://www.rfc-editor.org/rfc/rfc6749),
verified 2026-08-02). RFC 6750 defines bearer token usage for OAuth 2.0
protected resources, including the HTTP Authorization header form
`Authorization: Bearer <token>` in section 2.1
([https://www.rfc-editor.org/rfc/rfc6750](https://www.rfc-editor.org/rfc/rfc6750),
verified 2026-08-02).

The lineage is older than OAuth. Distributed systems have long passed
capability-like values, tickets, or session identifiers instead of sending a
password on every request. This entry treats the pattern as established because
modern web APIs, cloud infrastructure, and cluster control planes now expose it
as a first-class authentication shape. JWT is a common token format, but it is
not the pattern. RFC 7519 defines JSON Web Token as a compact representation for
claims between parties
([https://www.rfc-editor.org/rfc/rfc7519](https://www.rfc-editor.org/rfc/rfc7519),
verified 2026-08-02). A system can use opaque database-backed tokens, random
API keys, signed JWTs, proof-bound tokens, or short-lived cloud credentials and
still be using this pattern.

The pattern is named differently across communities.

- API teams often say **API token** when the credential belongs to a service,
  script, or developer account.
- OAuth teams say **access token** when the credential represents an approved
  access grant and is presented to a resource server.
- Infrastructure teams may say **temporary credentials** when a token or token
  set grants time-limited cloud access. AWS documents AWS STS as the service
  that creates temporary security credentials
  ([https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html),
  verified 2026-08-02).
- Kubernetes teams say **ServiceAccount token** for the credential mounted into
  workloads or requested through the TokenRequest API
  ([https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/](https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/),
  verified 2026-08-02).

The disputed boundary is whether a server-side session cookie counts. This
entry uses a narrow definition. A token is a credential value presented by the
client as proof that an earlier authentication or authorization step occurred.
It may be carried in an HTTP header, cookie, mTLS-bound envelope, command-line
configuration, or workload identity file. A plain session cookie can be
implemented as a token, but cookie-session management brings browser-specific
CSRF, SameSite, domain, and path rules that deserve their own pattern.

## 2. Problem and context

The problem appears when a system must authenticate repeated requests without
asking the caller to resend a long-lived secret, such as a password, private
key, or root cloud credential. The resource server needs enough evidence to
decide who is calling, what access has been granted, whether the grant is still
valid, and which tenant, audience, or workload the request is meant for. At the
same time, the caller needs a credential that can be attached to each request
without blocking on an interactive sign-in flow.

The context is usually one of four cases.

- A user signs in through an authorization server, and an application calls an
  API on that user's behalf. OAuth 2.0 describes this split between client,
  authorization server, and resource server in RFC 6749, section 1.1
  ([https://www.rfc-editor.org/rfc/rfc6749](https://www.rfc-editor.org/rfc/rfc6749),
  verified 2026-08-02).
- A service calls another service without a human in the loop, and the callee
  needs a scoped credential instead of a shared password.
- A workload running on a platform needs access to a control plane or cloud
  API. Kubernetes obtains time-bound ServiceAccount tokens through its
  TokenRequest mechanism for pods, according to its service account
  administration documentation
  ([https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/](https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/),
  verified 2026-08-02).
- A developer or automation tool needs API access and receives a personal or
  fine-grained token. GitHub documents fine-grained personal access tokens with
  resource owner, repository access, and permission choices
  ([https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens),
  verified 2026-08-02).

The pressure comes from repetition. Password authentication answers the first
request, but it is a poor answer for every request. The password is too broad,
too long-lived, too hard to rotate without user disruption, and too attractive
to logs, crash dumps, proxies, SDK debug output, and third-party clients. OAuth
2.0 describes the password-sharing problem by separating the resource owner's
credentials from the credential issued to a client for a limited grant in RFC
6749, section 1
([https://www.rfc-editor.org/rfc/rfc6749](https://www.rfc-editor.org/rfc/rfc6749),
verified 2026-08-02).

Token-based Authentication moves the repeated request credential into a smaller
object. The token can carry or reference a subject, issuer, audience, expiry,
scope, key identifier, token identifier, and client identity. The resource
server validates that object or asks an authority to validate it, then maps the
validated result to local authorization.

Engineering judgement. The pattern is strongest when authentication and
authorization must be separated in time. The expensive, user-facing,
risk-scored, or multi-factor step happens once. Later calls use a narrow
credential with a limited lifetime. The pattern is weakest when developers
treat the token as a portable password and forget the lifetime, audience,
storage, and revocation model.

## 3. Forces

Engineering judgement. Token-based Authentication is a trade among latency,
coupling, consistency, operability, cost, team topology, and cognitive load. It
does not remove the need for trust. It relocates trust to issuance, validation,
storage, and key management.

- **Latency.** Favoured when validation is local, as with a signed JWT whose
  issuer key is cached. Sacrificed when every request calls an introspection
  endpoint or database. RFC 7662 defines OAuth 2.0 Token Introspection as a way
  for a protected resource to query an authorization server about token state
  ([https://datatracker.ietf.org/doc/html/rfc7662](https://datatracker.ietf.org/doc/html/rfc7662),
  verified 2026-08-02).
- **Coupling.** Favoured between clients and resource servers because clients
  do not send passwords to every API. Sacrificed between resource servers and
  the issuer because validation rules, issuer identifiers, key rotation, scopes,
  and audiences become a shared contract.
- **Consistency.** Favoured when every request is checked against the token's
  current claims or introspection result. Sacrificed when long token lifetimes
  let old grants survive after account, tenant, or role changes.
- **Operability.** Favoured because token issuance, validation failures, expiry,
  and scope decisions can be logged as separate events. Sacrificed because bad
  logs can leak bearer tokens. RFC 6750 warns that bearer tokens need protection
  in storage and transport because possession is enough for use
  ([https://www.rfc-editor.org/rfc/rfc6750](https://www.rfc-editor.org/rfc/rfc6750),
  verified 2026-08-02).
- **Cost.** Favoured when a resource server can verify tokens without a central
  round trip. Sacrificed by key rotation, issuer uptime, token revocation
  stores, monitoring, incident response, and developer education.
- **Team topology.** Favoured when an identity or platform team owns issuance
  and domain teams own resource authorization. Sacrificed when no team owns the
  contract, leaving each API to invent claims, scopes, errors, and expiry rules.
- **Cognitive load.** Sacrificed. A request is no longer authenticated by one
  credential check. Readers must understand token class, issuer, audience,
  lifetime, storage channel, renewal path, revocation path, and authorization
  mapping.

The pattern favours stateless request handling, delegation, scope reduction,
and revocability at the grant level. It sacrifices simple reasoning. A team
must treat tokens as live credentials with a full life cycle.

## 4. Applicability and non-applicability

Reach for Token-based Authentication when the following conditions hold.

- Repeated API calls need a request credential after a stronger sign-in,
  federation, device, workload, or service identity step.
- A third-party or internal client needs limited access without receiving the
  user's password. OAuth 2.0 was designed around this separation in RFC 6749,
  section 1
  ([https://www.rfc-editor.org/rfc/rfc6749](https://www.rfc-editor.org/rfc/rfc6749),
  verified 2026-08-02).
- Access should be limited by scope, audience, resource, tenant, time, or
  subject.
- The resource server can validate the token on every request or on every
  security decision that matters.
- Revocation or expiry can be made operationally visible, including dashboards
  for denied tokens, expired tokens, issuer failures, and key rotation errors.
- Different teams or products need a stable authentication contract over HTTP,
  queues, RPC, command-line tools, or workload identity.
- A caller must renew access without repeating user interaction, using a
  refresh token or platform credential exchange. Google documents refresh-token
  use for continued access after an access token expires
  ([https://developers.google.com/identity/protocols/oauth2](https://developers.google.com/identity/protocols/oauth2),
  verified 2026-08-02).

Explicit non-applicability list.

- **Do not use it to avoid password hygiene.** A token stored forever in the
  same places as a password becomes a second password. Use password managers,
  hardware-backed keys, workload identity, or short-lived exchange instead.
- **Do not use self-contained bearer tokens when instant revocation is a hard
  requirement.** A signed token can be accepted until expiry unless the resource
  server also checks revocation state. Use opaque reference tokens with
  introspection, short lifetimes with denial lists, or sender-constrained
  tokens.
- **Do not use bearer tokens over plaintext transport.** Bearer possession is
  enough for use under RFC 6750, section 1.2, so transport disclosure is account
  disclosure
  ([https://www.rfc-editor.org/rfc/rfc6750](https://www.rfc-editor.org/rfc/rfc6750),
  verified 2026-08-02).
- **Do not put access tokens in URLs when a header can carry them.** RFC 6750,
  section 2.3 says the URI query method is not recommended because URLs are
  likely to be logged
  ([https://www.rfc-editor.org/rfc/rfc6750](https://www.rfc-editor.org/rfc/rfc6750),
  verified 2026-08-02).
- **Do not use JWTs because the team wants to avoid server storage.** Storage
  removal moves state into keys, expiry, audience, revocation gaps, and claim
  migration. Pick JWTs for validation distribution, not fashion.
- **Do not accept a token for every API owned by the company.** Audience and
  resource binding exist so one stolen token does not work everywhere. RFC 9068
  requires `aud` for JWT access tokens and describes resource indicators in
  sections 2.2 and 3
  ([https://www.rfc-editor.org/rfc/rfc9068](https://www.rfc-editor.org/rfc/rfc9068),
  verified 2026-08-02).
- **Do not use a long-lived personal token for high-volume automation when an
  app or workload identity model exists.** GitHub advises considering GitHub
  Apps for better scalability and management when more fine-grained tokens are
  needed
  ([https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens),
  verified 2026-08-02).
- **Do not mix authentication and authorization in a single unreviewed claim.**
  `sub=alice` proves a subject only after issuer, signature, expiry, audience,
  and token class have all been validated. It does not by itself grant write
  access to invoices.
- **Do not use it when a short local session is enough and there is no API
  boundary.** A server-rendered application with one origin, one server, and no
  third-party API access may be simpler with a server-side session cookie.
- **Do not use it for non-repudiation.** Bearer token logs can identify which
  credential was presented, not who physically operated the device.

## 5. Structure

Name participants by security role, not by implementation class.

- **Subject.** The human, service, workload, or device that the token says
  something about. In OAuth this may be the resource owner, the client, or both
  depending on grant type.
- **Client.** The program that obtains the token and presents it on requests.
  It may be public, confidential, first-party, third-party, interactive, or
  headless.
- **Issuer.** The authorization server, identity provider, control plane, or
  credential service that creates tokens. It authenticates the subject or
  client, chooses claims, signs or stores the token, and defines expiry.
- **Token.** The credential presented by the client. It may be opaque, signed,
  encrypted, reference-based, sender-constrained, or a structured credential
  set.
- **Resource server.** The API or service that receives the token. It validates
  token form and trust, extracts validated attributes, and runs local
  authorization.
- **Validation material.** The key set, introspection endpoint, token database,
  issuer metadata, revocation list, or policy bundle that lets the resource
  server decide whether the token is acceptable.
- **Authorization policy.** The local rule set that maps validated attributes
  to actions, resources, tenants, and data fields.
- **Renewal path.** The refresh token, token exchange, workload identity file,
  device code flow, or platform refresh mechanism that obtains a replacement
  token before or after expiry.
- **Revocation path.** The delete, rotate, deny, invalidate, account-disable,
  key-roll, or policy-change path that stops further use.

The structural rule is simple. The token must be smaller than the original
authority it represents. Smaller can mean shorter lifetime, fewer resources,
smaller scope, one audience, one workload, one tenant, one device, or binding
to a cryptographic holder. If the token is as broad and permanent as the
credential that minted it, the pattern has collapsed into password replication.

Two implementation boundaries matter. First, issuance and validation are
separate jobs. The issuer decides what the token means. The resource server
decides whether to trust that meaning for a requested action. Second,
authentication and authorization are separate jobs. A valid token identifies a
grant or subject. It does not automatically authorize a domain action.

## 6. ASCII structure diagram

```text
  +-----------+       sign in, exchange, or grant       +-------------+
  | Subject   | --------------------------------------> | Issuer      |
  +-----------+                                         |-------------|
        ^                                               | keys        |
        |                                               | grants      |
        |                                               | policies    |
        |                                               +------+------+
        |                                                      |
        |                       token                          |
        |                      issued                          v
  +-----+-----+   Authorization: Bearer token       +----------+------+
  | Client    | ----------------------------------> | Resource Server |
  |-----------|                                     |-----------------|
  | stores    |                                     | validates token |
  | renews    |                                     | maps policy     |
  +-----+-----+                                     +----------+------+
        |                                                      |
        | refresh, exchange, rotate                           |
        v                                                      v
  +-----------+                                      +----------------+
  | Renewal   |                                      | Validation     |
  | Path      |                                      | Material       |
  +-----------+                                      +----------------+

  The client presents the token. The resource server validates the token.
  The authorization policy still decides the requested operation.
```

## 7. Dynamics

The runtime flow has two phases. Issuance creates or retrieves a credential
after a stronger authentication or grant event. Use presents that credential to
the resource server. Validation may be local or remote.

```text
Subject/Client          Issuer              Resource Server       Policy
      |                   |                       |                  |
      |-- authenticate -->|                       |                  |
      |-- request grant ->|                       |                  |
      |                   |-- create token ------>|                  |
      |<-- token ---------|                       |                  |
      |                   |                       |                  |
      |-- request + token ----------------------->|                  |
      |                   |                       |-- validate ----->|
      |                   |                       |<- attributes ----|
      |                   |                       |-- authorize ---->|
      |                   |                       |<- allow/deny ----|
      |<-- response ------|-----------------------|                  |
      |                   |                       |                  |
      |-- refresh or re-authenticate ------------>|                  |
      |                   |                       |                  |
```

For a signed JWT, the validation step often reads issuer metadata and cached
keys rather than calling the issuer on every request. RFC 9068 section 4
recommends authorization server metadata or OpenID Connect discovery for
publishing signing keys and issuer values to resource servers
([https://www.rfc-editor.org/rfc/rfc9068](https://www.rfc-editor.org/rfc/rfc9068),
verified 2026-08-02). For an opaque token, the resource server commonly asks a
database or introspection endpoint. RFC 7662 standardizes a token introspection
response model
([https://datatracker.ietf.org/doc/html/rfc7662](https://datatracker.ietf.org/doc/html/rfc7662),
verified 2026-08-02).

Timing is the hard part. A token has an issue time, acceptance window, expiry,
and sometimes a not-before time. A resource server must handle clock skew
without accepting old tokens for too long. A client must renew before expiry
without stampeding the issuer. A revocation event must either reach every
resource server or be bounded by short expiry. A key rotation must overlap old
and new keys long enough for in-flight tokens, then retire old keys once their
tokens can no longer be accepted.

Engineering judgement. The runtime invariant to defend is this. Every protected
operation must derive its authority from a freshly validated token result and a
local authorization decision, not from a cached boolean named `authenticated`.

## 8. Implementation variants

**Opaque reference token.** The token is a high-entropy random string. The
issuer stores the associated subject, scope, audience, expiry, and status. The
resource server looks up the token locally or through introspection. This gives
strong revocation and small wire size. It costs a storage or network dependency
on the validation path. It fits payment systems, admin APIs, and environments
where revocation matters more than per-request latency.

**Signed self-contained token.** The token carries claims and a signature, often
as a JWT. The resource server validates issuer, signature, expiry, audience,
token type, and claims. RFC 7519 defines JWT claims, and RFC 9068 defines a JWT
profile for OAuth 2.0 access tokens
([https://www.rfc-editor.org/rfc/rfc7519](https://www.rfc-editor.org/rfc/rfc7519),
verified 2026-08-02;
[https://www.rfc-editor.org/rfc/rfc9068](https://www.rfc-editor.org/rfc/rfc9068),
verified 2026-08-02). This reduces validation round trips. It costs careful key
rotation, token-class separation, and revocation design.

**Bearer token.** The client proves authority by possession. RFC 6750 defines
this property and states that proof of possession of key material is not
required
([https://www.rfc-editor.org/rfc/rfc6750](https://www.rfc-editor.org/rfc/rfc6750),
verified 2026-08-02). This is operationally simple and widely supported. It
raises the value of every storage channel and log line that might contain the
token.

**Sender-constrained token.** The token is accepted only when accompanied by
proof from a key, certificate, or secure holder. OAuth Security BCP discusses
sender-constrained access tokens as a replay defense in RFC 9700, section 4.10
([https://datatracker.ietf.org/doc/html/rfc9700](https://datatracker.ietf.org/doc/html/rfc9700),
verified 2026-08-02). This reduces replay value after theft. It costs client
key management and protocol support.

**Refresh token plus access token.** The access token is short-lived and sent
to APIs. The refresh token is longer-lived, stored more carefully, and used to
obtain new access tokens. OAuth 2.0 defines refresh tokens in RFC 6749, section
1.5
([https://www.rfc-editor.org/rfc/rfc6749](https://www.rfc-editor.org/rfc/rfc6749),
verified 2026-08-02). This fits user-facing apps that need continued access.
It adds a second secret and a second theft mode.

**Personal access token.** The token belongs to a user and is created for a
tool, script, or API client. GitHub documents both fine-grained and classic
personal access tokens, and lists resource and permission controls for the
fine-grained form
([https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens),
verified 2026-08-02). This is useful for developer tooling. It is risky when
used as a shared team credential.

**Workload identity token.** The platform mints a short-lived token for a pod,
VM, function, job, or build runner. Kubernetes documents bound ServiceAccount
tokens that are time-bound, audience-bound, and tied to a pod
([https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/](https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/),
verified 2026-08-02). AWS STS creates temporary security credentials for
trusted users and roles
([https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html),
verified 2026-08-02). This variant is the right default for cloud automation
when the platform can identify the workload.

**Cookie-carried token.** The token is carried in a cookie rather than an
Authorization header. This can fit browser applications because cookies have
built-in send rules. It also imports browser risks such as CSRF and cookie
scope mistakes. The pattern still applies only if every server-side protected
operation validates the token result.

**Token exchange.** One token is traded for another with a narrower audience,
scope, or delegation path. This limits downstream exposure. It costs exchange
policy and audit clarity. Use it when a frontend or edge service must call
multiple downstream services with different audiences.

## 9. Known production uses

**Google APIs.** Google documents OAuth 2.0 access tokens for calls to Google
APIs. Its overview says an application obtains an access token or an
authorization code that can be exchanged for one, sends the token to a Google
API in an Authorization header, and uses refresh tokens for continued access
after access-token expiry
([https://developers.google.com/identity/protocols/oauth2](https://developers.google.com/identity/protocols/oauth2),
verified 2026-08-02). This is a production use of user-granted access tokens
across many Google API clients.

**Kubernetes ServiceAccounts.** Kubernetes mounts API credentials into pods
using projected ServiceAccount tokens. Its documentation says the kubelet
fetches time-bound tokens with the TokenRequest API, that a token expires when
the pod is deleted or after a configured lifetime, and that newer versions use
the TokenRequest API and projected volume mechanism
([https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/](https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/),
verified 2026-08-02). This is a production use of workload-bound token
authentication for cluster API access.

**AWS STS temporary credentials.** AWS documents AWS Security Token Service as
creating temporary security credentials for access to AWS resources. The IAM
documentation states that temporary credentials are short-term, are generated
dynamically, are not stored with the user, and stop working after expiry
([https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html),
verified 2026-08-02). This is a production use of token-like, time-limited
credentials for cloud authorization.

**GitHub personal access tokens.** GitHub documents personal access tokens for
API and command-line access. Its fine-grained tokens are limited by resource
owner, repository access, and permissions, while classic tokens have broader
limits and risk
([https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens),
verified 2026-08-02). This is a production use of developer-created tokens for
automation and API clients.

## 10. Consequences

Engineering judgement. The consequences below are practice effects of adopting
the pattern. The cited standards define mechanisms; the weighting is design
reasoning.

Positive consequences.

- Repeated requests no longer need the user's password or a long-lived root
  credential.
- The issuer can grant narrower authority than the original sign-in, using
  scope, audience, expiry, tenant, client, device, workload, or resource claims.
- Resource servers can be scaled independently when validation is local and key
  material is cached.
- APIs get a protocol-level authentication boundary that works for browsers,
  mobile clients, CLI tools, services, and jobs.
- Token issue, refresh, denial, and expiry events can be measured separately.
- Incident response can rotate keys, revoke token records, shorten lifetimes,
  disable clients, or remove grants without resetting every user password.
- Third-party clients can be removed without changing the resource owner's
  primary credential, which is one of the problems OAuth 2.0 was designed to
  address in RFC 6749, section 1
  ([https://www.rfc-editor.org/rfc/rfc6749](https://www.rfc-editor.org/rfc/rfc6749),
  verified 2026-08-02).

Negative consequences.

- A stolen bearer token can be replayed until expiry or revocation takes
  effect. RFC 6750 defines bearer semantics as possession-based use without
  proof of key possession
  ([https://www.rfc-editor.org/rfc/rfc6750](https://www.rfc-editor.org/rfc/rfc6750),
  verified 2026-08-02).
- Every service now depends on issuer availability, key distribution, metadata,
  or introspection.
- Debug logs, proxy logs, browser histories, crash reports, and support bundles
  become sensitive if they can contain tokens.
- Long token lifetimes weaken role-change and account-disable response.
- Short token lifetimes create refresh traffic and expiry edge cases.
- JWT claims can become a distributed schema. Bad claim names and type changes
  become cross-service migrations.
- Revocation is simple for opaque tokens and harder for self-contained tokens.
- Local authorization can be skipped by teams that mistake a valid token for an
  allow decision.
- Key rotation mistakes can cause broad outages. A missing `kid`, stale JWKS
  cache, or premature key removal can reject active clients.
- Test setup grows because every protected path needs valid, expired, malformed,
  wrong-audience, wrong-issuer, and under-scoped cases.

## 11. Failure modes and misuse

Engineering judgement. These are the failure patterns to test and monitor. Each
triple includes an observable symptom, a likely cause, and a fix.

**Symptom.** A token from one API works against another API.  
**Cause.** The resource server validates signature and expiry but does not check
audience or resource binding.  
**Fix.** Require and validate audience. For JWT access tokens, RFC 9068 requires
`aud` and says the resource server must reject tokens whose audience does not
identify the resource server
([https://www.rfc-editor.org/rfc/rfc9068](https://www.rfc-editor.org/rfc/rfc9068),
verified 2026-08-02).

**Symptom.** Users keep access for minutes or hours after being disabled.  
**Cause.** Long-lived self-contained access tokens are accepted without
revocation checks.  
**Fix.** Shorten access-token lifetime, add introspection or deny-list checks
for high-risk operations, and invalidate refresh tokens or grants on disable.

**Symptom.** Support tickets include full Authorization headers.  
**Cause.** Request logging captures credentials before redaction.  
**Fix.** Redact Authorization, Cookie, query parameters named `access_token`,
and token-shaped values at the logging boundary.

**Symptom.** Random 401 spikes begin after key rotation.  
**Cause.** Resource servers cached old metadata too long, or the issuer removed
old signing keys before all matching tokens expired.  
**Fix.** Rotate with overlap. Publish new keys before use, accept old keys until
all old tokens expire, then retire.

**Symptom.** A copied URL grants API access.  
**Cause.** Access tokens are accepted in query strings and were logged, shared,
or stored in browser history.  
**Fix.** Reject token query parameters except for a documented legacy endpoint.
RFC 6750 section 2.3 says URI query usage is not recommended because URLs are
likely to be logged
([https://www.rfc-editor.org/rfc/rfc6750](https://www.rfc-editor.org/rfc/rfc6750),
verified 2026-08-02).

**Symptom.** A token with `alg=none` or a wrong algorithm is accepted in tests
or production.  
**Cause.** The verifier trusts the token header to choose verification
semantics.  
**Fix.** Pin allowed algorithms per issuer and token class. RFC 9068 section 4
says JWT access tokens using `alg` value `none` must be rejected
([https://www.rfc-editor.org/rfc/rfc9068](https://www.rfc-editor.org/rfc/rfc9068),
verified 2026-08-02).

**Symptom.** Expired tokens pass on one node and fail on another.  
**Cause.** Clock skew across resource servers or inconsistent skew allowance.
**Fix.** Monitor time sync, define a small skew window, and test boundary times.

**Symptom.** A service account token keeps working after a pod is gone.  
**Cause.** Legacy long-lived service account secrets are being used instead of
bound tokens.  
**Fix.** Prefer TokenRequest and projected tokens. Kubernetes documents
time-bound TokenRequest tokens and notes that manual long-lived tokens still
exist for cases that need them
([https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/](https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/),
verified 2026-08-02).

**Symptom.** One broad personal token appears in many CI jobs.  
**Cause.** A user token became a shared automation credential.  
**Fix.** Replace it with workload identity, a GitHub App, or per-job scoped
tokens. GitHub points users toward GitHub Apps for scalability and management
when many fine-grained tokens would be needed
([https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens),
verified 2026-08-02).

**Symptom.** API returns 500 for malformed tokens.  
**Cause.** The parser throws before the authentication layer converts failures
to a controlled denial.  
**Fix.** Treat parse, decode, signature, expiry, issuer, audience, and scope
failures as authentication or authorization denials with bounded error detail.

## 12. Trade-off matrix

Engineering judgement. The table compares named alternatives across the forces
from dimension 3.

| Approach | Latency | Coupling | Consistency | Operability | Cost | Team topology | Cognitive load |
|---|---|---|---|---|---|---|---|
| Token-based Authentication with local JWT validation | Low per request after key cache warmup | Resource servers coupled to issuer metadata and claim schema | Medium, expiry creates a stale window | Good if issue, validation, and denial events are traced | Key rotation and schema governance | Good split between identity and API teams | High |
| Token-based Authentication with opaque introspection | Higher, validation path may call issuer or token store | Resource servers coupled to introspection contract | High, revocation can be near immediate | Good, central validation gives one audit point | Issuer availability and cache design | Central identity team has more runtime load | Medium |
| Server-side session cookie | Low inside one origin | Tight to web origin and session store | High if every request reads session state | Mature for browser apps | Session store and CSRF controls | Good for one application team | Lower |
| HTTP Basic Authentication over TLS | Low | Client and server share password handling | Low for rotation and delegated grants | Poor unless password events are isolated | Low at first, high after growth | Poor for third-party clients | Low at first |
| Mutual TLS client authentication | Medium due to certificate operations and provisioning | Coupled to PKI and client certificate lifecycle | High for device or service identity | Good where certificate inventory is mature | PKI operations | Strong for platform teams | High |
| Signed request authentication | Medium, every request signs canonical data | Coupled to canonicalization and key handling | High replay resistance when nonce or timestamp is used | Harder to debug than bearer tokens | Key distribution and client libraries | Good for partner APIs | High |
| API gateway session exchange | Low for downstream services after edge validation | Coupled to gateway and internal identity headers | Medium, depends on gateway policy freshness | Good at edge, weaker inside if headers are trusted blindly | Gateway operation | Central platform owns edge | Medium |

The practical choice often combines rows. A browser app may use a server-side
session cookie to protect the web tier, then exchange that session for a
short-lived access token when calling an API. A service mesh may use mTLS for
service identity and token claims for user or workload delegation. The pattern
does not require one credential type for every boundary.

## 13. Related and incompatible patterns

**Least Privilege.** Token claims and server-side grants are the mechanism by
which a caller receives less than full authority. The relationship is direct.
If scope, audience, lifetime, and resource restrictions are absent, the token
does not support least privilege.

**Zero Trust.** Token validation on each request supports the zero-trust habit
of checking identity and context at service boundaries. It does not by itself
provide device health, network segmentation, or continuous risk evaluation.

**Complete Mediation.** Every protected operation must check the token result
and local policy. Caching an `isAuthenticated` flag across operations conflicts
with complete mediation.

**Defense in Depth.** Sender constraints, TLS, token redaction, short lifetimes,
audience checks, revocation, and key rotation are layers around the core token.
Each layer assumes another layer can fail.

**Secure by Default.** A secure default token system issues short-lived,
audience-bound, scoped tokens and rejects query-string tokens. RFC 9700 updates
OAuth 2.0 security guidance and includes best current practices for redirect
flows, replay prevention, and privilege restriction
([https://datatracker.ietf.org/doc/html/rfc9700](https://datatracker.ietf.org/doc/html/rfc9700),
verified 2026-08-02).

**Session.** A server-side session can replace token-based authentication for
single-origin browser applications. It composes when a web session is exchanged
for downstream access tokens.

**Capability.** A bearer token resembles a capability when possession grants
some authority. The difference in many business systems is that resource
servers still consult policy and account state rather than treating the token
as the whole authorization object.

**Gateway and reverse proxy authentication.** Gateways compose well when they
validate external tokens and pass signed internal identity headers or new
tokens downstream. They conflict when downstream services blindly trust
unsiged, client-supplied identity headers.

**Password-per-request.** This is incompatible for delegated API access because
it requires clients to keep and replay the user's primary secret. OAuth 2.0 was
created to avoid that class of problem in third-party access scenarios
([https://www.rfc-editor.org/rfc/rfc6749](https://www.rfc-editor.org/rfc/rfc6749),
verified 2026-08-02).

**Implicit session authority.** Code that checks "a request reached this
service, therefore it is authenticated" conflicts with the pattern. The token
must be validated at the boundary where authority is needed.

## 14. Refactoring path in and out

Engineering judgement. Introduce the pattern as a boundary migration, not as a
global rewrite.

Refactoring in.

1. Inventory every protected route, RPC method, queue consumer, and background
   task that currently trusts a password, API key, session flag, network
   location, or shared secret.
2. Pick one boundary and one caller class. Good first cuts are service-to-
   service read APIs, developer automation tokens, or one user-facing API.
3. Define token classes before token fields. Examples are user access token,
   service token, refresh token, personal token, and workload token. Each class
   gets its own issuer, audience, lifetime, storage rules, and accepted
   algorithms.
4. Create an authentication middleware that returns a typed validation result,
   not a raw claims map. Apply the refactoring family technique "Extract
   Function" to isolate parse, verify, and map steps when starting from inline
   checks.
5. Add audience, issuer, expiry, and scope checks before accepting any
   production traffic. For JWT access tokens, follow RFC 9068 validation
   requirements for `typ`, issuer, audience, signature, and `alg=none` rejection
   ([https://www.rfc-editor.org/rfc/rfc9068](https://www.rfc-editor.org/rfc/rfc9068),
   verified 2026-08-02).
6. Add redaction at ingress logs before rollout. Once tokens exist, old debug
   habits become incident sources.
7. Issue tokens in parallel with the old credential for one caller. Compare
   allow and deny decisions without enforcing them, then switch enforcement.
8. Shorten old credential permissions after token use is stable.
9. Document renewal and revocation. A token launch without operational
   revocation is unfinished.

Refactoring out.

1. Identify the cost that exceeds the value. Common reasons are one-origin
   browser simplicity, issuer outages, claim sprawl, or no real delegation.
2. Count token classes and consumers. Removing the pattern is tractable only
   when consumers can be migrated in groups.
3. Replace self-contained tokens first where revocation pain is the driver.
   Move to opaque reference tokens or sessions before removing token auth
   entirely.
4. For single-application web flows, move request authority back to a server-
   side session and keep API tokens only for external APIs.
5. Expire old tokens by reducing lifetime, refusing new refreshes, then
   rejecting the old token class after the maximum lifetime passes.
6. Remove dead keys, metadata documents, token stores, and denial lists after
   traffic proves the old class is gone.

Cross references. "Replace Magic Literal with Symbolic Constant" applies to
scope strings and audience names. "Extract Class" applies when token validation
has grown inside route handlers. "Move Function" applies when authorization
logic sits inside the token parser rather than the domain policy module.

## 15. Testing and verification

Engineering judgement. Test the token life cycle as a protocol, then test
domain authorization as policy. Do not test only the happy path with one sample
token.

Unit tests for validation should cover:

- missing credential,
- malformed token,
- wrong token class,
- wrong issuer,
- wrong audience,
- expired token,
- token before not-before time,
- unsupported algorithm,
- missing key identifier,
- unknown key identifier,
- invalid signature or MAC,
- missing required subject,
- missing required scope,
- under-scoped token,
- revoked token,
- clock-skew boundary,
- duplicated or conflicting claims,
- query-string token rejection where the API policy bans it.

Integration tests should cover issuer metadata caching, key rotation overlap,
introspection timeout, introspection negative response, refresh before expiry,
refresh after expiry, account disable, client disable, tenant removal, and
logging redaction.

Test doubles must be chosen with care.

- Use a fake issuer when testing clients. It should issue real signed tokens
  from a test key rather than mocking the token string.
- Use a fake clock for expiry and skew. Sleeping in tests creates slow and
  flaky suites.
- Use a local JWKS or key provider fake for resource servers. Exercise cache
  refresh and unknown-key paths.
- Use an introspection fake for opaque tokens. It should return active,
  inactive, under-scoped, wrong-audience, and timeout responses.
- Use property tests for token parsers when the language ecosystem supports
  them. Inputs should include truncation, extra dots, non-UTF-8 bytes, large
  payloads, duplicate JSON names if the parser permits them, and base64url edge
  cases.

Security verification should include negative tests taken from the failure
modes. A verifier that accepts the wrong audience is not "mostly working"; it
is working for the attacker. A route that logs a token on malformed input is
not a minor debug issue; it turns authentication failures into credential
leakage.

Verification in production should use canary tokens and synthetic requests.
Create a valid token for a test subject, an expired token, a wrong-audience
token, and an under-scoped token. Synthetic checks should prove that only the
valid one reaches the protected operation. The invalid cases must fail with
stable 401 or 403 responses and no token material in logs.

## 16. Observability signals

Engineering judgement. Observe token auth without recording token values. The
dashboard should answer which issuer, token class, client, scope, and audience
are failing, not which secret was presented.

Log these events with redacted credentials:

- token issued, with token class, issuer, subject category, client id, audience,
  scope count, lifetime, and key id,
- token refreshed, with old token class, new token class, client id, and
  rotation result,
- validation allowed, sampled at low rate for high-volume paths,
- validation denied, with reason code such as missing, malformed, expired,
  wrong issuer, wrong audience, bad signature, unknown key, inactive,
  under-scoped, revoked, or introspection unavailable,
- authorization denied after valid authentication, with policy reason and
  requested action,
- key set fetched, key set failed, key id unknown, key retired,
- revocation, account disable, client disable, grant removal, and token class
  shutdown.

Trace attributes should include issuer, audience, token class, client id, grant
type where known, validation mode, and denial reason. Do not put token strings,
refresh tokens, session cookies, or raw Authorization headers into traces.

Useful metrics:

- request count by validation result,
- 401 and 403 rate by route and client,
- expired-token rate,
- wrong-audience rate,
- unknown-key rate,
- introspection latency and error rate,
- issuer metadata fetch latency and error rate,
- token issue rate,
- refresh success and failure rate,
- refresh-token reuse detection rate,
- key age and time until oldest accepted token expires,
- percentage of tokens with target lifetime,
- percentage of requests using deprecated token classes,
- redaction rule hit count in logs.

A healthy dashboard has low malformed-token rate, stable expired-token rate,
near-zero wrong-audience rate, near-zero unknown-key rate except during planned
rotation, bounded issuer latency, and no raw-token samples in log storage. A
failing dashboard shows a sudden 401 spike after deployment, key id misses,
introspection timeouts, refresh storms, or a validation-allowed rate for a
deprecated token class that should be gone.

Alert on conditions tied to user harm or incident response. Alert when unknown
key id failures spike, when introspection is unavailable for protected APIs,
when wrong-audience tokens are accepted by any synthetic test, when revoked
tokens are allowed, and when redaction detects token-shaped values in logs.

## 17. Security and privacy implications

Token-based Authentication closes one attack surface and opens another. It
reduces password replay to APIs, supports scoped grants, and gives revocation
at the client, grant, token, account, or key level. It opens credential theft
paths through token storage, transport, logs, browser history, mobile backups,
CI variables, support bundles, package scripts, and client-side code.

Bearer tokens are high-risk secrets. RFC 6750 states that any party in
possession of a bearer token can use it without proving possession of
cryptographic key material, and that bearer tokens need protection in storage
and transport
([https://www.rfc-editor.org/rfc/rfc6750](https://www.rfc-editor.org/rfc/rfc6750),
verified 2026-08-02). The design response is to reduce what theft buys:
shorter lifetime, narrower audience, narrower scope, sender constraint, device
binding, workload binding, revocation, and redaction.

JWTs create privacy pressure because claims are often readable by the holder
and by any service that receives the token. RFC 7519 defines JWTs as JSON claim
sets carried in JWS or JWE form
([https://www.rfc-editor.org/rfc/rfc7519](https://www.rfc-editor.org/rfc/rfc7519),
verified 2026-08-02). Engineering judgement. Put only the claims needed by
resource servers into access tokens. Do not place email address, group
membership, tenant list, entitlement list, or profile data in every token
unless every receiving service needs it and retention rules permit it.

Audience matters for privacy and security. A token made for one API should not
be a portable identity document for another API. RFC 9068 requires JWT access
tokens to include audience and requires resource servers to reject tokens whose
audience does not identify them
([https://www.rfc-editor.org/rfc/rfc9068](https://www.rfc-editor.org/rfc/rfc9068),
verified 2026-08-02). Engineering judgement. Treat audience as a data-minimizing
control as well as a replay control.

Refresh tokens are more sensitive than access tokens because they can mint new
access. Store them with stronger controls than access tokens. Rotate them where
the issuer supports rotation. Detect reuse where possible. RFC 9700 includes
refresh token protection in its OAuth security best current practice
([https://datatracker.ietf.org/doc/html/rfc9700](https://datatracker.ietf.org/doc/html/rfc9700),
verified 2026-08-02).

Token-based Authentication is silent on user consent quality, account recovery,
legal basis, retention, and authorization policy correctness. It can carry the
result of those decisions, but it does not make them correct. It also does not
replace secure transport, input validation, rate limiting, audit logging, abuse
detection, or secrets management.

## Code examples

The examples use HMAC-signed, compact tokens to show the core pattern without
framework setup. Production JWT libraries should be preferred for standards
compliance; these examples are runnable teaching code for validation flow,
expiry, audience, and scope checks.

TypeScript, run with Node after compiling through `npx tsc`.

```typescript
const { createHmac, timingSafeEqual } = require("crypto");

type Claims = { sub: string; aud: string; exp: number; scopes: string[] };

const secret = "demo-secret-for-token-auth";

function b64url(input: string): string {
  return Buffer.from(input).toString("base64url");
}

function sign(data: string): string {
  return createHmac("sha256", secret).update(data).digest("base64url");
}

function issue(claims: Claims): string {
  const body = b64url(JSON.stringify(claims));
  return `${body}.${sign(body)}`;
}

function authenticate(
  header: string,
  audience: string,
  scope: string,
  now: number,
): Claims {
  if (!header.startsWith("Bearer ")) throw new Error("missing bearer token");
  const [body, mac] = header.slice(7).split(".");
  if (!body || !mac) throw new Error("malformed token");
  const actual = Buffer.from(sign(body));
  const given = Buffer.from(mac);
  if (actual.length !== given.length || !timingSafeEqual(actual, given)) {
    throw new Error("bad signature");
  }
  const claims = JSON.parse(
    Buffer.from(body, "base64url").toString(),
  ) as Claims;
  if (claims.exp <= now) throw new Error("expired token");
  if (claims.aud !== audience) throw new Error("wrong audience");
  if (!claims.scopes.includes(scope)) throw new Error("missing scope");
  return claims;
}

const token = issue({
  sub: "user-123",
  aud: "billing-api",
  exp: 2_000_000_000,
  scopes: ["invoice:read"],
});

const claims = authenticate(
  `Bearer ${token}`,
  "billing-api",
  "invoice:read",
  1_700_000_000,
);
console.log(claims.sub);
```

Python, run with `python3`.

```python
import base64
import hashlib
import hmac
import json

SECRET = b"demo-secret-for-token-auth"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def unb64url(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def sign(body: str) -> str:
    mac = hmac.new(SECRET, body.encode("ascii"), hashlib.sha256).digest()
    return b64url(mac)


def issue(claims: dict) -> str:
    body = b64url(json.dumps(claims, separators=(",", ":")).encode("utf-8"))
    return f"{body}.{sign(body)}"


def authenticate(header: str, audience: str, scope: str, now: int) -> dict:
    if not header.startswith("Bearer "):
        raise ValueError("missing bearer token")
    try:
        body, given = header[7:].split(".", 1)
    except ValueError as exc:
        raise ValueError("malformed token") from exc
    if not hmac.compare_digest(sign(body), given):
        raise ValueError("bad signature")
    claims = json.loads(unb64url(body))
    if claims["exp"] <= now:
        raise ValueError("expired token")
    if claims["aud"] != audience:
        raise ValueError("wrong audience")
    if scope not in claims["scopes"]:
        raise ValueError("missing scope")
    return claims


token = issue({
    "sub": "user-123",
    "aud": "billing-api",
    "exp": 2_000_000_000,
    "scopes": ["invoice:read"],
})
print(authenticate(f"Bearer {token}", "billing-api", "invoice:read", 1_700_000_000)["sub"])
```

Go, run with `go run`.

```go
package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
)

type Claims struct {
	Sub    string   `json:"sub"`
	Aud    string   `json:"aud"`
	Exp    int64    `json:"exp"`
	Scopes []string `json:"scopes"`
}

var secret = []byte("demo-secret-for-token-auth")

func sign(body string) string {
	mac := hmac.New(sha256.New, secret)
	mac.Write([]byte(body))
	return base64.RawURLEncoding.EncodeToString(mac.Sum(nil))
}

func issue(claims Claims) (string, error) {
	raw, err := json.Marshal(claims)
	if err != nil {
		return "", err
	}
	body := base64.RawURLEncoding.EncodeToString(raw)
	return body + "." + sign(body), nil
}

func hasScope(scopes []string, wanted string) bool {
	for _, scope := range scopes {
		if scope == wanted {
			return true
		}
	}
	return false
}

func authenticate(header, audience, scope string, now int64) (Claims, error) {
	var claims Claims
	if !strings.HasPrefix(header, "Bearer ") {
		return claims, errors.New("missing bearer token")
	}
	parts := strings.SplitN(strings.TrimPrefix(header, "Bearer "), ".", 2)
	if len(parts) != 2 {
		return claims, errors.New("malformed token")
	}
	if !hmac.Equal([]byte(sign(parts[0])), []byte(parts[1])) {
		return claims, errors.New("bad signature")
	}
	raw, err := base64.RawURLEncoding.DecodeString(parts[0])
	if err != nil {
		return claims, err
	}
	if err := json.Unmarshal(raw, &claims); err != nil {
		return claims, err
	}
	if claims.Exp <= now {
		return claims, errors.New("expired token")
	}
	if claims.Aud != audience {
		return claims, errors.New("wrong audience")
	}
	if !hasScope(claims.Scopes, scope) {
		return claims, errors.New("missing scope")
	}
	return claims, nil
}

func main() {
	token, err := issue(Claims{
		Sub:    "user-123",
		Aud:    "billing-api",
		Exp:    2_000_000_000,
		Scopes: []string{"invoice:read"},
	})
	if err != nil {
		panic(err)
	}
	claims, err := authenticate("Bearer "+token, "billing-api", "invoice:read", 1_700_000_000)
	if err != nil {
		panic(err)
	}
	fmt.Println(claims.Sub)
}
```

## 18. References

- D. Hardt, editor, RFC 6749, *The OAuth 2.0 Authorization Framework*,
  sections 1, 1.1, 1.4, 1.5, October 2012,
  [https://www.rfc-editor.org/rfc/rfc6749](https://www.rfc-editor.org/rfc/rfc6749),
  verified 2026-08-02.
- M. Jones and D. Hardt, RFC 6750, *The OAuth 2.0 Authorization Framework:
  Bearer Token Usage*, sections 1.2, 2.1, 2.3, 5, October 2012,
  [https://www.rfc-editor.org/rfc/rfc6750](https://www.rfc-editor.org/rfc/rfc6750),
  verified 2026-08-02.
- M. Jones, J. Bradley, and N. Sakimura, RFC 7519, *JSON Web Token (JWT)*,
  sections 1 and 2, May 2015,
  [https://www.rfc-editor.org/rfc/rfc7519](https://www.rfc-editor.org/rfc/rfc7519),
  verified 2026-08-02.
- V. Bertocci, RFC 9068, *JSON Web Token (JWT) Profile for OAuth 2.0 Access
  Tokens*, sections 2.2, 3, and 4, October 2021,
  [https://www.rfc-editor.org/rfc/rfc9068](https://www.rfc-editor.org/rfc/rfc9068),
  verified 2026-08-02.
- T. Lodderstedt, J. Bradley, A. Labunets, and D. Fett, RFC 9700, *Best Current
  Practice for OAuth 2.0 Security*, sections 2, 4.10, and 4.14, January 2025,
  [https://datatracker.ietf.org/doc/html/rfc9700](https://datatracker.ietf.org/doc/html/rfc9700),
  verified 2026-08-02.
- J. Richer, RFC 7662, *OAuth 2.0 Token Introspection*, sections 1 and 2,
  October 2015,
  [https://datatracker.ietf.org/doc/html/rfc7662](https://datatracker.ietf.org/doc/html/rfc7662),
  verified 2026-08-02.
- Kubernetes documentation, *Managing Service Accounts*, sections on bound
  service account tokens, TokenRequest API, token deletion and invalidation,
  [https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/](https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/),
  verified 2026-08-02.
- AWS Identity and Access Management documentation, *Temporary security
  credentials in IAM*,
  [https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html),
  verified 2026-08-02.
- GitHub Docs, *Managing your personal access tokens*,
  [https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens),
  verified 2026-08-02.
- Google for Developers, *Using OAuth 2.0 to Access Google APIs*,
  [https://developers.google.com/identity/protocols/oauth2](https://developers.google.com/identity/protocols/oauth2),
  verified 2026-08-02.
