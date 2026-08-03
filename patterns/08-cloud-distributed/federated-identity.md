---
name: Federated Identity
slug: federated-identity
family: 08-cloud-distributed
category: Cloud and Distributed
aliases: [Identity Federation, Single Sign-On Federation, Cross-Domain Authentication, Claims-Based Identity]
first_described: "OASIS SSTC, SAML 1.0, 2002; Kim Cameron, The Laws of Identity, 2005; OpenID Foundation, OpenID Connect Core 1.0, 2014"
maturity: canonical
related: [api-gateway, backend-for-frontend, circuit-breaker, saga, strangler-fig, event-sourcing]
incompatible_with: []
verified: 2026-08-02
---

# Federated Identity

## 1. Name, aliases, and lineage

The canonical name in production systems is Federated Identity, sometimes
written Identity Federation. The idea predates any single specification. an
organization authenticates a person once, at a source it trusts, and hands a
signed statement about that person to a second, independent organization,
which accepts the statement instead of asking the person to authenticate
again. The two organizations do not share a password database and do not
need to trust each other beyond the specific claims in the statement.

Two protocol families carry this idea in production today, and they are not
interchangeable, which is the first thing a reader needs settled before
anything else in this entry makes sense.

**SAML (Security Assertion Markup Language)** is an XML-based protocol
standardized by the OASIS Security Services Technical Committee. Version 1.0
shipped in 2002, version 1.1 in 2003, and the version almost everyone means
when they say "SAML" today, SAML 2.0, was approved as an OASIS Standard in
March 2005, unifying SAML 1.1 with the Liberty Alliance's ID-FF work and
Shibboleth's contributions. The formative document for the wire protocol is
"Assertions and Protocols for the OASIS Security Assertion Markup Language
(SAML) V2.0", OASIS Standard, 15 March 2005, published at
docs.oasis-open.org/security/saml/v2.0/saml-core-2.0-os.pdf. SAML is built on
assertions, XML documents an Identity Provider (IdP) signs and hands to a
Service Provider (SP), typically via an HTTP redirect or an HTTP POST binding
through the person's browser.

**OpenID Connect (OIDC)** is a JSON and JWT-based identity layer built on top
of OAuth 2.0. The core specification is "OpenID Connect Core 1.0 incorporating
errata set 2", OpenID Foundation, published at
openid.net/specs/openid-connect-core-1_0.html, verified 2026-08-02. OIDC
defines the ID Token as, in the specification's own words, a security token
that contains claims about the authentication of an end user by an
authorization server when using a client, and potentially other requested
claims (OpenID Connect Core 1.0, section 2, same source). Where SAML
assertions are signed XML, ID Tokens are signed JWTs, defined independently
in RFC 7519, "JSON Web Token (JWT)", IETF, May 2015, which describes a JWT,
in its own words, as a compact, URL-safe means of representing claims to be
transferred between two parties (RFC 7519, section 1,
www.rfc-editor.org/rfc/rfc7519, verified 2026-08-02).

A third term shows up constantly in casual usage and deserves a precise
boundary here rather than later. "OAuth" by itself is an AUTHORIZATION
protocol, RFC 6749, that issues an access token scoped to an API. OAuth alone
says nothing about who the person is, only what the bearer of the token is
allowed to do. OIDC adds authentication on top of OAuth's authorization
mechanics by defining the ID Token and the userinfo endpoint. Treating a raw
OAuth access token as proof of identity, without an ID Token, is a documented
and recurring security mistake, covered in dimension 11.

Kim Cameron's 2005 essay "The Laws of Identity" is widely cited as the
conceptual groundwork that motivated claims-based identity as an
architectural style, independent of any specific protocol, and is the source
most engineering-judgement claims about why federation is designed the way it
is trace back to. That essay is judgement and philosophy, not a wire protocol,
and is cited here as lineage, not as a technical claim to verify against.

## 2. Problem and context

An organization runs several applications. a payroll system, a ticketing
tool, a source control host, a cloud console. Each application historically
maintained its own username and password table. This produces three
compounding problems that get worse, not better, as the application count
grows.

First, a person accumulates one credential per application, which they reuse,
write down, or forget, and every reused password is a single point of
compromise across every application that shares it. Second, when a person
leaves the organization, someone must remember to disable their account in
every one of those separate tables, and in practice this step is missed
often enough that stale accounts are a standard finding in access reviews.
Third, every application that stores a password becomes a target, because a
breach of the weakest application leaks credentials usable, through reuse,
against the strongest one.

The context in which federated identity becomes the right answer, rather
than an unnecessary layer, is specifically when authentication must cross a
trust boundary between two systems that do not want to share a password
store. That boundary can be organizational, a vendor's SaaS product accepting
sign-in from a customer's corporate directory. It can be infrastructural, a
CI pipeline authenticating to a cloud provider without a stored secret. Or it
can be a public consumer flow, an e-commerce site letting a shopper sign in
with an existing Google or Apple account rather than creating a new one.

In every one of these cases the pattern's job is narrow and specific. move
the origin of authentication to a single trusted party, the Identity
Provider, and let every other party, the Relying Party, or in SAML
terminology the Service Provider, consume a signed, time-bounded statement
about the outcome, instead of independently verifying a password. The
Relying Party's job shrinks from authenticating the person to verifying a
signature and a set of claims, which is a much smaller and much more
auditable surface.

## 3. Forces

**Trust versus autonomy.** The Relying Party gains the convenience of not
managing credentials, at the cost of depending entirely on the Identity
Provider's availability and correctness. An IdP outage becomes an outage for
every downstream application that federates against it. This is a real
production failure mode, not a hypothetical, and it is why large deployments
often run a fallback local admin account outside the federation path.

**Latency versus statelessness.** A signed token that a Relying Party can
verify locally, using a cached public key, costs one signature verification
and zero network calls per request. A design that instead calls back to the
Identity Provider on every request, an OAuth token introspection call per
RFC 7662, is simpler to reason about for revocation but adds a network round
trip to the hot path. Production federated-identity systems overwhelmingly
choose the stateless, locally verifiable form, SAML assertions and OIDC ID
Tokens, for authentication, and accept the resulting revocation lag as a
bounded cost, addressed with a short token lifetime rather than a
synchronous check.

**Coupling to a wire format.** SAML's XML and XML Digital Signature stack
(XML-DSig) is heavier to implement correctly than JSON and JWT, and XML
signature wrapping attacks against poorly implemented SAML libraries are a
well-documented class of vulnerability, covered in dimension 17. OIDC's JSON
and JWT stack is lighter and has fewer historical parser-level
vulnerabilities, but it inherits every weakness of JWT signature validation,
including the notorious "alg equal to none" and algorithm-confusion classes,
also covered in dimension 17. Neither format is free of implementation risk.
the forces trade XML complexity for JWT signature-validation discipline.

**Operability versus flexibility.** SAML's browser-redirect, form-POST
bindings integrate cleanly with legacy enterprise directories, Active
Directory Federation Services, Shibboleth, Okta, PingFederate, that many
large organizations already run. OIDC's authorization code flow integrates
more naturally with mobile apps, single-page applications, and
machine-to-machine flows because it has native, first-class support for
public clients, PKCE per RFC 7636, and for non-browser flows, client
credentials and device code grants. A vendor selling into large enterprises
typically must support SAML because that is what the customer's IdP already
speaks. a vendor building consumer or developer-facing products defaults to
OIDC.

**Cost of clock discipline.** Both protocol families bind an assertion's
validity to a wall-clock window, and both explicitly tolerate a small amount
of drift between the Identity Provider's clock and the Relying Party's
clock. Getting that tolerance wrong, in either direction, is the single most
common production failure mode this entry documents, and it is a direct
force this pattern imposes that a locally issued session cookie never had to
consider. dimension 11 covers this in detail.

## 4. Applicability and non-applicability

**Reach for federated identity when.**

- Authentication must cross an organizational trust boundary. a SaaS product
  accepting sign-in from a customer's own corporate directory, enterprise
  SSO, which is almost always requested through SAML because that is the
  protocol the customer's IdP already speaks.
- A workload needs to call a cloud provider's API without embedding a
  long-lived secret. GitHub Actions authenticating to AWS, Azure, or GCP via
  OIDC, covered in dimension 9, is the reference case.
- Multiple independent applications should share one sign-in experience for
  the same population of people, and a single team already operates a
  central Identity Provider for that population.
- A consumer-facing product wants to lower signup friction by accepting an
  existing account from a large identity provider, Google, Apple, or
  Microsoft, instead of collecting and storing a new password.
- A machine identity, a CI job, a Kubernetes service account, a compute
  instance, needs to prove who it is to a service outside its own cluster or
  cloud account, without a shared static credential.

**Do NOT reach for federated identity when.**

- The application has one, self-contained user base with no requirement to
  ever cross a trust boundary. A single-tenant internal tool with ten known
  users gains nothing from SAML or OIDC beyond substantial integration
  complexity, key rotation obligations, and the entire clock-skew failure
  class described in dimension 11. A local username and a well-hashed
  password, or a simple session, is the right-sized answer.
- The two systems that need to share identity are under one team's direct
  control and already share a database or an internal service mesh with
  mutual TLS. Federated identity is designed for the case where the team
  does not control the other party's user store. Introducing SAML or OIDC
  between two microservices already owned by one team, instead of a
  service-mesh identity like SPIFFE and SPIRE or a shared internal auth
  token, adds an external-grade protocol surface to solve an internal-grade
  problem.
- Low-latency, high-frequency service-to-service calls where a network round
  trip or even a signature-verification cost per call is unacceptable. Prefer
  a short-lived, locally minted internal token or mutual TLS for that path,
  and reserve the federated identity flow for establishing the initial
  trust, not for every subsequent call.
- The team has no operational capacity to run or consume a metadata refresh
  and key-rotation process. Both SAML IdP certificates and OIDC JWKS signing
  keys rotate, and a Relying Party that hardcodes a public key instead of
  fetching it from the IdP's metadata endpoint or JWKS URI will break, often
  without warning, the day the IdP rotates. If the team cannot commit to
  handling rotation, federated identity introduces an outage risk larger than
  the problem it solves.
- Offline or air-gapped authentication, where the Relying Party cannot reach
  the Identity Provider even for a metadata or key fetch. Federated identity
  assumes network reachability to at least fetch signing keys periodically.
- Very high assurance, regulator-mandated hardware-bound authentication where
  the entire value of the credential depends on it never leaving a specific
  device, a smart card or a hardware security module bound directly to a
  local verifier. Federating that assertion across a network boundary to a
  third party can undermine the assurance property the hardware binding was
  meant to provide, unless the federation protocol itself carries a matching
  assurance-level claim, SAML's AuthnContextClassRef or OIDC's acr claim,
  that the Relying Party actually checks.

## 5. Structure

Federated identity has a small, stable set of participants across both
SAML and OIDC, named by role rather than by protocol-specific terminology.

- **Principal.** The person or machine identity being authenticated. In SAML
  terminology this is the Subject. In OIDC terminology this is the End-User
  for interactive login, or the client itself for machine-to-machine
  client-credentials flows.
- **Identity Provider (IdP).** The party that authenticates the Principal and
  issues a signed statement about the outcome. In OIDC this role is called
  the OpenID Provider, or OP. Owns the password, MFA, or other primary
  credential check. Never shares that credential with the Relying Party.
- **Relying Party (RP) or Service Provider (SP).** The application that
  wants to know who the Principal is. In SAML terminology this is the
  Service Provider. Trusts the IdP's signature, never re-authenticates the
  Principal directly.
- **User Agent.** The browser or device through which the assertion or token
  is transported, in the classic redirect-and-POST flows. For
  machine-to-machine federation, dimension 9's GitHub Actions to AWS case,
  there is no User Agent. the workload calls the IdP directly.
- **Assertion or ID Token.** The signed statement itself. A SAML Assertion is
  an XML document containing an Issuer, a Subject with a NameID, one or more
  Statements, Authentication, Attribute, or AuthorizationDecision, and a
  Conditions element carrying the NotBefore and NotOnOrAfter validity
  window plus an AudienceRestriction. An OIDC ID Token is a signed JWT
  carrying, at minimum, the iss, sub, aud, exp, and iat claims, each of
  which is defined in OpenID Connect Core 1.0 section 2, verified
  2026-08-02. iss is defined as the issuer identifier for the issuer of the
  response, aud is defined as the value that must contain the OAuth 2.0
  client_id of the Relying Party as an audience value, exp is defined as the
  expiration time on or after which the ID Token must not be accepted, and
  iat is defined as the time at which the JWT was issued.
- **Trust anchor.** What lets the Relying Party verify the signature without
  calling the Identity Provider synchronously. For SAML this is the IdP's
  X.509 signing certificate, distributed out of band via SAML metadata
  exchange. For OIDC this is the IdP's public signing key, published at a
  well-known JWKS URI which is itself discovered from the OIDC Discovery
  document. OpenID Connect Discovery 1.0 states that OpenID Providers
  supporting Discovery must make a JSON document available at the path
  formed by concatenating the string well-known slash openid-configuration
  to the Issuer, openid.net/specs/openid-connect-discovery-1_0.html,
  verified 2026-08-02, and that document publishes the issuer,
  authorization_endpoint, token_endpoint, and jwks_uri values the Relying
  Party needs.

## 6. ASCII structure diagram

```
                    +----------------------------+
                    |     Identity Provider       |
                    |  (OpenID Provider / SAML IdP)|
                    |------------------------------|
                    | - authenticates Principal    |
                    | - holds signing key/cert     |
                    | - publishes metadata/JWKS    |
                    | - issues Assertion/ID Token  |
                    +---------------+--------------+
                                    ^
                       signs and issues
                                    |
     +-------------+   redirect    |    POST assertion
     | User Agent  |-------------->|<-------------------+
     | (browser)   |               |                     |
     +------+------+               |                     |
            |                      |                     |
   initiates login                 |                     |
            |                      v                     |
            |          +-----------------------+          |
            +--------->|     Relying Party      |----------+
                       |  (Service Provider /    |
                       |   OIDC Client)           |
                       |--------------------------|
                       | - fetches trust anchor   |
                       |   (metadata / JWKS)       |
                       | - verifies signature      |
                       | - checks iss, aud,        |
                       |   exp/iat or NotBefore/    |
                       |   NotOnOrAfter, with       |
                       |   clock skew tolerance     |
                       | - establishes local       |
                       |   session for Principal   |
                       +---------------------------+

   Machine-to-machine variant (no User Agent), e.g. CI to cloud

   +----------------+   OIDC token request   +----------------+
   | CI Workload    |----------------------->| CI's OIDC IdP  |
   | (GitHub Action)|<-----------------------| (GitHub)       |
   +--------+-------+   short lived ID token +----------------+
            |
            | presents ID token as proof of workflow identity
            v
   +----------------+   validates iss/sub/aud    +----------------+
   | Cloud Provider  |<--------------------------| Cloud STS      |
   | trust policy    |   against configured OIDC  | issues short   |
   | (AWS/Azure/GCP) |   provider and claims       | lived cloud    |
   +-----------------+                             | credentials    |
                                                     +----------------+
```

## 7. Dynamics

The interactive, browser-mediated flow, SP-initiated SAML, or OIDC
Authorization Code Flow, shares the same shape, differing in wire format.
The description below follows OIDC's Authorization Code Flow, whose steps
OpenID Connect Core 1.0 walks through in eight stages, request preparation,
transmission to the authorization server, end-user authentication,
consent and authorization, returning an authorization code, exchanging the
code at the token endpoint, receiving tokens in the response body, and
validating the ID token to retrieve the subject identifier, verified
2026-08-02.

```
User Agent          Relying Party (RP)         Identity Provider (IdP)
    |                       |                            |
    |-- GET /login -------->|                             |
    |                       |-- redirect to authorization endpoint,
    |                       |   with client_id, redirect_uri, scope,
    |                       |   state, nonce ------------------------>|
    |<-- 302 redirect ------|                             |
    |------------------------------------------------------------------------------->|
    |                       |                             |-- authenticates
    |                       |                             |   Principal (password,
    |                       |                             |   MFA, or existing
    |                       |                             |   session cookie)
    |<---------------------------- 302 redirect with authorization code --------------|
    |-- GET redirect_uri?code=...&state=... ------------->|
    |                       |-- POST /token with code,   |
    |                       |   client credentials -------------------->|
    |                       |<---- ID Token + access token -------------|
    |                       |                             |
    |                       |-- verify ID Token signature |
    |                       |   using cached JWKS         |
    |                       |-- check iss, aud, exp, iat, |
    |                       |   nonce, with clock skew    |
    |                       |   tolerance                 |
    |                       |-- establish local session   |
    |<-- set-cookie, 302 to app --                          |
```

Two properties of this exchange matter more than the diagram alone conveys.
First, the authorization code returned to the browser in the redirect is a
one-time-use value exchanged for the ID Token over a direct, back-channel
HTTPS call from the Relying Party to the Identity Provider's token endpoint,
never through the browser again. this keeps the actual token off the
browser's history and off any intermediate logs that capture the redirect
URL. Second, the nonce value the Relying Party generated at request time
and the state value both round-trip through the flow specifically to
defeat replay and cross-site request forgery against the login flow itself.
a Relying Party that skips checking the returned nonce against the one it
sent is vulnerable to an ID Token replay, covered in dimension 11.

The machine-to-machine variant, used by CI systems federating to cloud
providers, drops the User Agent and the interactive authentication step
entirely, since the workload's identity, which workflow, which repository,
which branch, is itself what the Identity Provider asserts.

```
CI Workload                    CI Platform's OIDC IdP        Cloud Provider STS
    |                                   |                            |
    |-- request ID token for this ---->|                             |
    |   specific job run                |-- issues signed ID token   |
    |                                   |   scoped to repo, workflow,|
    |                                   |   ref, run id --------------|
    |<---- short lived ID token --------|                            |
    |                                                                 |
    |-- present ID token, requested cloud role ---------------------->|
    |                                                                 |-- fetches CI
    |                                                                 |   platform's
    |                                                                 |   JWKS
    |                                                                 |-- verifies
    |                                                                 |   signature,
    |                                                                 |   iss, sub
    |                                                                 |   pattern, aud
    |<---- short lived cloud credentials (STS token) ----------------|
    |                                                                 |
    |-- calls cloud API with short lived credentials, then discards -->
```

GitHub's own description of this mechanism, in its own words, states that
every time a job runs, GitHub's OIDC provider auto-generates an OIDC token,
and that once the cloud provider successfully validates the claims
presented in the token, it then provides a short-lived cloud access token
that is available only for the duration of the job, GitHub Docs, "About
security hardening with OpenID Connect", verified 2026-08-02. No cloud
secret is stored in the CI system at rest.

## 8. Implementation variants

**SP-initiated versus IdP-initiated flow.** SP-initiated means the person
starts at the Relying Party, which redirects them to the Identity Provider.
This is the flow shown in dimension 7, and it is the recommended default
because the Relying Party controls the state and nonce or RelayState
values from the start, closing off a class of forged-assertion replay
attacks. IdP-initiated means the person starts at the Identity Provider's own
portal and clicks a tile to be pushed, unsolicited, to the Relying Party.
IdP-initiated SAML in particular has a documented history of enabling
assertion replay when the Relying Party does not independently generate and
verify an InResponseTo correlation value, because there was no original
request from the SP to correlate against.

**Front-channel versus back-channel token delivery.** SAML's HTTP-POST
binding and OIDC's Authorization Code Flow both deliver the actual signed
credential via a back-channel or a same-origin POST rather than a URL
fragment. OIDC's older Implicit Flow, by contrast, returned the ID Token
directly in the URL fragment, which then sits in browser history and can leak
via the Referer header or browser extensions. The OAuth Security Best Current
Practice, and the OIDC community broadly, now recommend Authorization Code
Flow with PKCE over Implicit Flow for every client type, including
single-page applications.

**Broker versus direct federation.** A Relying Party can integrate with one
IdP directly, or integrate once with an identity broker that itself
federates to many upstream IdPs and presents a single, normalized protocol to
the Relying Party. Auth0 describes its own role this way, in its own words.
Auth0 sits between an application and its sources of users, which adds a
level of abstraction, so the application is isolated from any changes to
and idiosyncrasies of each source's implementation, Auth0 Docs, "Identity
Providers", verified 2026-08-02. Okta, Microsoft Entra External ID, and
AWS Cognito's identity pools play the same broker role for their respective
ecosystems. The broker variant trades a second hop and a second party to
trust for dramatically less integration work when the Relying Party must
support many different upstream IdPs.

**Attribute-based versus claims-minimal assertions.** Some deployments push
a large set of user attributes, department, manager, cost center, group
memberships, into every assertion, which is convenient for the Relying Party
but grows the Identity Provider's per-login payload and, more seriously,
means every downstream Relying Party receives personal data it may not need,
an unnecessary data-minimization and privacy exposure covered in dimension
17. The claims-minimal variant requests only what is strictly needed. a
stable subject identifier, and the minimum attributes the authorization
decision actually depends on, fetching anything richer via a separate,
scoped API call, OIDC's userinfo endpoint, or a direct call to the IdP's
directory API, only when needed.

**Federation for machines versus federation for people.** Everything
described so far concerns a human Principal. the same pattern, with the same
Identity Provider, Relying Party, and signed-assertion structure, also
federates a machine identity, where the authentication step is not a
password prompt but a platform-level fact the IdP already knows, this exact
CI job is running, in this exact repository, on this exact branch. This is
the variant behind dimension 9's GitHub Actions and Kubernetes examples, and
it is the modern replacement for a long-lived static cloud credential stored
as a CI secret.

## 9. Known production uses

**AWS IAM SAML 2.0 federation, AssumeRoleWithSAML.** AWS documents, in its
own words, that AWS supports identity federation with SAML 2.0, and that this
feature enables federated single sign-on, so users can log into the AWS
Management Console or call AWS API operations without an administrator
creating an IAM user for everyone in the organization. The flow is explicit.
the IdP constructs a SAML assertion with information about the user and
sends the assertion to the client app, the client app calls the AWS STS
AssumeRoleWithSAML API, passing the ARN of the SAML provider, the ARN of the
role to assume, and the SAML assertion from the IdP, and the API response to
the client app includes temporary security credentials. AWS Identity and
Access Management User Guide, "SAML 2.0 federation",
docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_saml.html,
verified 2026-08-02. This is a textbook production instance of the IdP,
Relying Party, and Assertion structure from dimension 5, with AWS STS acting
as the Relying Party's trust boundary.

**GitHub Actions OpenID Connect to cloud providers.** GitHub's
documentation states, in its own words, that every time a job runs, GitHub's
OIDC provider auto-generates an OIDC token, that this token contains
multiple claims to establish a security-hardened and verifiable identity
about the specific workflow that is trying to authenticate, and that once
the cloud provider successfully validates the claims presented in the
token, it then provides a short-lived cloud access token that is available
only for the duration of the job, eliminating the need to duplicate cloud
credentials as long-lived GitHub secrets. GitHub Docs, "About security
hardening with OpenID Connect",
docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect,
verified 2026-08-02. This is the machine-to-machine variant from dimension
8, and it is the recommended replacement, across AWS, Azure, and GCP, for a
static cloud secret stored in CI.

**Kubernetes API server, OpenID Connect Tokens authentication.** The
Kubernetes reference documentation lists OpenID Connect Tokens among the
API server's external authentication integrations, alongside X.509 client
certificates, bootstrap tokens, and webhook token authentication.
Kubernetes Documentation, "Authenticating",
kubernetes.io/docs/reference/access-authn-authz/authentication/, verified
2026-08-02. In practice, an operator configures the API server with an OIDC
issuer URL, a client ID, and a username or groups claim mapping, so that a
cluster's authorization layer, RBAC, makes decisions against identities
asserted by an external Identity Provider, such as Google, Okta, or a
self-hosted Dex or Keycloak instance, rather than against a Kubernetes-local
credential store. Kubernetes itself plays the Relying Party role, it never
authenticates the person directly.

**Auth0 as a multi-provider identity broker.** Auth0's own documentation
describes the broker variant from dimension 8 directly, in its own words.
Auth0 sits between an application and its sources of users, which adds a
level of abstraction, so the application is isolated from any changes to
and idiosyncrasies of each source's implementation, Auth0 Docs, "Identity
Providers", auth0.com/docs/authenticate/identity-providers, verified
2026-08-02. A Relying Party integrates once, against Auth0's own OIDC or
SAML surface, and Auth0 in turn federates to whichever social or enterprise
IdP the end customer actually uses, which is the standard commercial
Identity-Provider-as-a-Service shape shared by Okta and Microsoft Entra
External ID.

**Ruby SAML (OneLogin) clock-drift tolerant assertion validation.** The
widely used ruby-saml library documents the exact failure this entry's
dimension 11 covers, and its remedy, directly in its README, in its own
words. server clocks tend to drift naturally, and if during validation of
the response the error current time is earlier than the NotBefore condition
appears, this may be due to clock differences between the local system and
that of the Identity Provider, and the library exposes an
allowed_clock_drift parameter for exactly this purpose. onelogin/ruby-saml,
README, github.com/onelogin/ruby-saml/blob/master/README.md, verified
2026-08-02. This is cited here as a real, maintained library's own
operational documentation of the clock-skew problem this pattern imposes on
every implementer, not as a novel claim invented for this entry.

## 10. Consequences

Positive.

- Passwords, and the breach surface a password database represents, live in
  exactly one place, the Identity Provider, instead of being duplicated
  across every application a person uses.
- Deprovisioning a person is a single action at the Identity Provider. every
  Relying Party that trusts that IdP loses the person's access on the next
  token or assertion request, without an administrator having to visit each
  application separately.
- The Relying Party's authentication code shrinks to signature verification
  and claims checking, a small, reviewable surface, instead of owning
  password hashing, reset flows, and MFA enrollment.
- Machine-to-machine federation, dimension 9, removes long-lived static
  secrets from CI systems entirely, closing an entire class of leaked-secret
  incidents where a CI log or a misconfigured repository exposes a stored
  cloud key.
- A person authenticates once per Identity Provider session and reaches
  every federated Relying Party without a second login prompt, which is a
  genuine usability win at scale, not only a security one.

Negative.

- The Identity Provider becomes a single point of failure for every
  federated Relying Party at once. An IdP outage is not one application's
  outage, it is every application's outage simultaneously, and this blast
  radius is the direct cost of the trust consolidation described above.
- Revocation is not instantaneous by default. A stateless, locally verified
  assertion or ID Token remains technically valid until its exp, or
  NotOnOrAfter, time passes, even if the Identity Provider disables the
  account a second later, unless the Relying Party also performs an
  online revocation or introspection check, which reintroduces the network
  round trip dimension 3 describes trading away.
- Debugging a federated login failure crosses an organizational boundary.
  the Relying Party's logs alone often cannot show why the Identity Provider
  rejected a request, and vice versa, which materially slows incident
  response compared to a self-contained login system.
- Clock discipline becomes a hard operational requirement across two
  independently operated systems, and getting it wrong produces the specific,
  recurring failure class documented in dimension 11.
- Implementing the cryptographic verification correctly, XML-DSig for SAML
  or JWT signature and algorithm checking for OIDC, is not trivial, and a
  flawed implementation converts the pattern's security benefit into a
  security liability, covered in dimension 17.

## 11. Failure modes and misuse

**Clock skew rejecting valid assertions.** Symptom. Users intermittently see
assertion is not yet valid, or invalid audience restriction, errors that
disappear on retry, and correlate with slightly different server hardware or
virtualization hosts. Cause. The Identity Provider's clock and the Relying
Party's clock disagree by more than the validator's tolerance, so a
newly issued assertion's NotBefore, or a JWT's iat, appears to be in the
future from the Relying Party's point of view, or a still-valid assertion's
NotOnOrAfter, or exp, appears to have already passed. RFC 7519 addresses
this directly for JWT, stating in its own words that implementers may
provide for some small leeway, usually no more than a few minutes, to
account for clock skew, when validating exp and nbf, RFC 7519, section
4.1.4 and 4.1.5, verified 2026-08-02. OpenID Connect Core 1.0 states the
equivalent for exp validation in nearly identical language, verified
2026-08-02. Fix. Add an explicit clock-skew tolerance, typically 60 to 180
seconds, to every time-based claim check, in both directions, not-yet-valid
and expired, and never set that tolerance to zero on the theory that it is
more secure, because a zero-tolerance validator against two real,
independently operated clocks fails intermittently and unpredictably in
production, which is worse for security posture than a small, deliberate,
and documented tolerance. The ruby-saml library's own allowed_clock_drift
parameter and README guidance, cited in dimension 9, exist specifically
because this failure is common enough to need a first-class configuration
knob.

**Missing or wrong audience check.** Symptom. A token or assertion issued
for one application is accepted by a completely different application that
also trusts the same Identity Provider. Cause. The Relying Party verifies
the signature and checks that the issuer is trusted, but never checks that
the aud claim in OIDC, or the AudienceRestriction in SAML, names its own
client ID or entity ID specifically. Any valid token from the shared IdP,
issued for any other client, is then accepted. Fix. Always check aud
against the Relying Party's own registered client identifier, as a required,
non-optional step, exactly as shown in the code samples in this entry.

**Confusing an OAuth access token with proof of identity.** Symptom. An
application treats a successful OAuth access-token exchange as evidence of
who the user is, and grants access based on the access token alone. Cause.
OAuth 2.0 access tokens authorize API calls, they carry no standardized,
verifiable claim about who obtained them, and their format and content are
opaque by design in the base OAuth specification. Only the OIDC ID Token
carries signed, verifiable identity claims, sub, iss, aud. Fix. For any
authentication decision, verify the ID Token, never the access token, and
treat this as a hard architectural boundary, not a style preference.

**Stale trust anchor after key rotation.** Symptom. Every federated login
suddenly fails, cluster-wide, immediately after the Identity Provider
rotates its signing certificate or key, with a signature-verification
failure. Cause. The Relying Party hardcoded the IdP's public key or
certificate at integration time instead of fetching it dynamically from the
IdP's SAML metadata endpoint or OIDC JWKS URI and caching it with a
refresh interval shorter than the IdP's rotation cadence. Fix. Always
resolve the trust anchor from the IdP's published metadata or JWKS document,
cache it with a bounded TTL, and alert on JWKS or metadata fetch failures
well before the cached key would otherwise go stale.

**IdP-initiated SAML replay.** Symptom. A captured or resent SAML Response,
originally delivered via IdP-initiated SSO, is successfully replayed against
the Relying Party to establish a second, unauthorized session. Cause. In an
IdP-initiated flow there was no originating request from the Service
Provider to correlate against, no InResponseTo value to check, and the
Relying Party did not otherwise track and reject already-consumed assertion
IDs within their validity window. Fix. Track consumed assertion IDs, or JWT
jti values, for the duration of their validity window and reject a repeat,
and prefer SP-initiated flows wherever the Identity Provider supports them.

**Trusting an unverified alg field.** Symptom. A forged token with a
tampered signature, or no signature at all, is accepted. Cause. A JWT
library that reads the alg header from the token itself and uses it to
decide how to verify the signature, rather than having the caller pin the
expected algorithm, allows an attacker to submit a token with alg set to
none, or to swap an asymmetric algorithm for a symmetric one, using the
IdP's known public key as the HMAC secret. This class of vulnerability is
well documented across multiple JWT libraries historically. Fix. Configure
the verifier with an explicit, expected algorithm, for example, only accept
RS256, signed with this specific key, never let the token's own header
dictate the verification method.

## 12. Trade-off matrix

| Concern | Federated Identity (SAML/OIDC) | Centralized Password Store per App | Internal Service Mesh Identity (mTLS/SPIFFE) |
|---|---|---|---|
| Password sprawl across apps | Eliminated, one IdP holds credentials | High, every app owns a table | Not applicable, machine identity, no passwords |
| Deprovisioning speed | One action at the IdP, propagates on next token issuance | Manual, per-app, error prone | One action at the mesh control plane |
| Cross-organization trust | Designed for this, explicit trust boundary and signed assertions | Cannot cross a boundary without sharing credentials | Not designed for cross-organization use |
| Latency per request | Low, local signature verification against cached key | Low, local session lookup | Low, TLS handshake amortized over connection |
| Single point of failure | The Identity Provider, across all Relying Parties | Each app's own store, isolated blast radius | The mesh control plane or CA |
| Revocation immediacy | Bounded by token lifetime unless online check added | Immediate, session invalidated centrally in that one app | Immediate with short-lived certs and CA revocation |
| Implementation complexity | High, XML-DSig or JWT verification, clock skew, metadata rotation | Low to moderate, standard password hashing and sessions | Moderate to high, certificate issuance and rotation infrastructure |
| Best fit | Enterprise SSO, consumer social login, CI-to-cloud machine identity | Small, single-tenant internal tools | Service-to-service calls within one team's infrastructure |

## 13. Related and incompatible patterns

**Backend for Frontend.** A BFF commonly owns the browser-facing side of the
OIDC Authorization Code Flow, holding the session cookie and the tokens
server-side, so that the browser-facing single-page application never
handles a raw ID Token or access token directly. This pairs the federation
pattern's identity assertion with the BFF's job of shielding the browser
from token handling risk.

**API Gateway.** An API Gateway is a common place to terminate and verify an
OIDC access token or a federated identity's derived session token before
routing a request onward to backend services, centralizing the
signature-verification and claims-checking logic from dimension 11 in one
place rather than duplicating it in every service.

**Circuit Breaker.** Because the Identity Provider is a single point of
failure, dimension 10, a Relying Party that calls the IdP synchronously,
for token introspection, or for the userinfo endpoint, should wrap that
call in a circuit breaker, so an IdP outage degrades gracefully rather than
cascading into every dependent request hanging.

**Saga.** Not directly related to authentication, but a federated identity
system that issues a machine identity used to kick off a distributed
transaction, dimension 9's CI-to-cloud case extended into a deployment
pipeline that provisions resources across services, may need Saga-style
compensation if a downstream step in that pipeline fails after the
short-lived credential has already been used.

**Strangler Fig.** Migrating a legacy application from its own local
password store to federated identity is a textbook Strangler Fig migration.
introduce the federated login path alongside the legacy one, migrate users
incrementally, and retire the legacy password store once federation is the
only active path.

Federated identity is not incompatible with any pattern in this catalog in
the strict architectural sense. it is an authentication concern that composes
with, rather than conflicts with, the structural and resilience patterns
above.

## 14. Refactoring path in and out

**Introducing federation into an application with its own password store.**
Add the federated login path as an additional entry point first, never as a
replacement, so existing users are not locked out mid-migration. Map the
Identity Provider's stable subject identifier, the SAML NameID with a
persistent format, or the OIDC sub claim, to the application's existing
internal user record, either by an explicit account-linking step the user
performs once, or by matching a verified email claim if the organization's
policy allows implicit linking. Keep the legacy password path functional
until account linking coverage is confirmed for the active user base, then
disable new local-password signups, and finally retire the legacy path for
existing accounts on an announced timeline, which is the Strangler Fig shape
from dimension 13 applied to authentication specifically.

**Removing federation, or moving from one Identity Provider to another.**
Because the Relying Party never stored the person's actual credential, this
migration is materially safer than the equivalent for a locally hosted
password store. export the mapping between the old IdP's subject identifiers
and the application's internal user records, establish federation with the
new IdP, and re-link each user's internal record to the new IdP's subject
identifier, either through a one-time re-authentication and linking step or,
where policy allows, an administrator-driven bulk remap keyed on a verified
email address. Removing federation entirely, back to a local password store,
requires an explicit password-set flow for every affected user, since the
Relying Party never had a password to fall back to.

## 15. Testing and verification

Federated identity introduces testing obligations that a locally hosted
password system does not have, because the Relying Party is now trusting a
signed artifact from an external party rather than a value it generated
itself.

- **Test the negative claims path explicitly**, not only the happy path. a
  wrong issuer, a wrong audience, an expired token, a not-yet-valid token,
  and a token signed by a key not in the trusted set must all be rejected,
  each as its own test case, exactly as the code samples in this entry
  demonstrate for the positive and one representative negative case.
- **Test clock-skew tolerance as a first-class case**, both directions.
  a token that is expired by exactly one second past the configured
  tolerance must be rejected, and a token that is expired by one second
  less than the tolerance must be accepted. This is the failure class from
  dimension 11 and it deserves boundary-condition tests, not only a manual
  smoke test.
- **Use a local, fully controlled test Identity Provider** for automated
  tests rather than the real, shared corporate or vendor IdP. Open source
  options include Keycloak or Dex for OIDC, and simplesamlphp for SAML,
  which lets the test suite mint tokens and assertions with deliberately
  broken claims to exercise the negative paths above without depending on
  network access to a real IdP.
- **Test key rotation handling** by rotating the test IdP's signing key
  mid-suite and confirming the Relying Party's cached-key refresh picks up
  the new key within its configured refresh interval, rather than only
  testing against a single, static key for the life of the test suite.
- **What becomes easier because of this pattern.** authorization logic
  becomes testable independently of authentication, since the Relying
  Party's tests can construct a signed test token directly, as the code
  samples do, instead of driving a real login form.
- **What becomes harder.** end-to-end tests that exercise the full
  browser-redirect flow require either a real or a well-simulated Identity
  Provider in the test environment, and CI systems running these end-to-end
  flows need to handle the redirect chain, which is materially more setup
  than posting credentials to a local login endpoint.

## 16. Observability signals

- **Assertion or token validation failure rate, broken down by reason.**
  Signature mismatch, wrong issuer, wrong audience, expired, not yet valid,
  and unknown signing key should each be a distinct counted metric, not one
  combined authentication-failed counter, because the reasons point to
  entirely different root causes, dimension 11, and an operator debugging a
  spike needs to know which one fired.
- **Key or metadata refresh success and age.** Track the age of the
  currently cached JWKS or SAML metadata and alert well before the IdP's
  documented rotation window, so a stale-key failure, dimension 11, is
  caught before it becomes a user-facing outage.
- **Clock-skew-triggered rejections specifically**, separated from other
  expired-token rejections, since a rising rate of expired-but-within-a-few-
  seconds-of-the-boundary rejections is the earliest signal of clock drift
  between the Relying Party's fleet and the Identity Provider, well before
  it becomes visible as a general outage.
- **Identity Provider round-trip latency**, for any flow that does call the
  IdP synchronously, token endpoint exchange, userinfo calls, introspection,
  since this is now an external dependency on the login critical path and
  its latency distribution should be tracked the same way any external API
  dependency's latency is tracked.
- **A healthy instance's dashboard** shows a validation-failure rate near
  zero, a key-cache age well within the IdP's rotation window, and a stable,
  low IdP round-trip latency. **A failing instance's dashboard** shows a
  spike in one specific rejection reason, most commonly clock skew or a
  stale key immediately after an IdP-side rotation, which is exactly why
  the reason needs to be a labeled dimension on the metric rather than
  folded into one generic counter.

## 17. Security and privacy implications

Federated identity both closes and opens attack surface, and both sides
deserve equal weight.

**What it closes.** Removing per-application password storage removes the
per-application password-database breach as an attack vector for those
applications, and centralizes the credential-hardening investment, rate
limiting, MFA, anomaly detection, at one Identity Provider instead of
requiring every application to reimplement it correctly.

**What it opens.** The Identity Provider becomes the single highest-value
target in the whole architecture. compromising it compromises every
federated Relying Party at once, which is exactly the blast-radius cost
named in dimension 10. The signature-verification code path itself is
security-critical and has a documented history of implementation flaws
across the industry. SAML implementations have suffered from XML Signature
Wrapping attacks, where an attacker inserts a forged, unsigned element
alongside a legitimately signed one and exploits a parser that validates the
signature against one element but processes a different one for the actual
authentication decision. JWT implementations have suffered from acceptance
of an alg value of none and algorithm-confusion attacks, accepting an
asymmetric public key as an HMAC secret, both covered as concrete failure
modes in dimension 11. Neither of these is a theoretical concern. both
classes recur across poorly maintained or hand-rolled implementations,
which is the strongest practical argument for using a mature, actively
maintained library, the kind cited in dimension 9, rather than writing
SAML XML parsing or JWT signature verification from scratch.

**Data minimization.** Every claim or attribute an Identity Provider pushes
into an assertion or ID Token is personal data that now travels to, and
often gets logged or cached by, every Relying Party that requests it. the
claims-minimal variant from dimension 8 is a genuine privacy control, not
only an engineering-elegance preference, and a Relying Party requesting more
attributes than an authorization decision actually needs is taking on
unnecessary data-protection obligations for no functional benefit.

**Token storage on the Relying Party side.** An ID Token or SAML assertion,
once validated, is often exchanged for a locally issued session, and that
session's cookie or token must itself follow standard web session security
practice, HttpOnly, Secure, an appropriately scoped SameSite value, since
the federated identity pattern's own security guarantees end at the point
of validation and do not extend to how the Relying Party subsequently
manages its own session state.

## Code examples

Every sample below implements the same claim-validation logic from dimension
11, decode an ID Token or a SAML-style assertion's conditions, and reject it
on a wrong issuer, a wrong audience, or a time window violated beyond a
configured clock-skew tolerance. Each sample was compiled or run against the
toolchain listed in the repository's entry template, and each intentionally
omits real cryptographic signature verification (which requires a live key
pair) so the claims logic itself, the part responsible for the majority of
real-world federated identity bugs per dimension 11, can be read and run
standalone. A production implementation still verifies the cryptographic
signature FIRST, using a library, before ever trusting the claims below.

### TypeScript, OIDC ID Token claims validation

Compiled with `tsc --target es2020 --module commonjs` and run with `node`.

```typescript
interface IdTokenClaims {
  iss: string;
  aud: string;
  sub: string;
  exp: number;
  iat: number;
}

class ClaimsError extends Error {}

const B64_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

function base64Encode(input: string): string {
  let out = "";
  let i = 0;
  const bytes: number[] = [];
  for (let c = 0; c < input.length; c++) bytes.push(input.charCodeAt(c));
  while (i < bytes.length) {
    const b0 = bytes[i++];
    const b1 = i < bytes.length ? bytes[i++] : NaN;
    const b2 = i < bytes.length ? bytes[i++] : NaN;
    out += B64_CHARS[b0 >> 2];
    out += B64_CHARS[((b0 & 3) << 4) | (isNaN(b1) ? 0 : b1 >> 4)];
    out += isNaN(b1) ? "=" : B64_CHARS[((b1 & 15) << 2) | (isNaN(b2) ? 0 : b2 >> 6)];
    out += isNaN(b2) ? "=" : B64_CHARS[b2 & 63];
  }
  return out;
}

function base64UrlEncode(input: string): string {
  return base64Encode(input).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function base64UrlDecode(segment: string): string {
  const padded = segment.replace(/-/g, "+").replace(/_/g, "/");
  const pad = padded.length % 4 === 0 ? "" : "=".repeat(4 - (padded.length % 4));
  const table = B64_CHARS;
  const clean = (padded + pad).replace(/=+$/, "");
  let bits = "";
  for (const ch of clean) {
    const val = table.indexOf(ch);
    bits += val.toString(2).padStart(6, "0");
  }
  let out = "";
  for (let i = 0; i + 8 <= bits.length; i += 8) {
    out += String.fromCharCode(parseInt(bits.slice(i, i + 8), 2));
  }
  return out;
}

function decodeIdTokenClaims(idToken: string): IdTokenClaims {
  const parts = idToken.split(".");
  if (parts.length !== 3) {
    throw new ClaimsError("malformed JWT, expected three dot separated parts");
  }
  return JSON.parse(base64UrlDecode(parts[1])) as IdTokenClaims;
}

function validateClaims(
  claims: IdTokenClaims,
  expectedIssuer: string,
  expectedAudience: string,
  now: number,
  clockSkewSeconds: number
): void {
  if (claims.iss !== expectedIssuer) {
    throw new ClaimsError(`iss mismatch: got ${claims.iss}, want ${expectedIssuer}`);
  }
  if (claims.aud !== expectedAudience) {
    throw new ClaimsError(`aud mismatch: got ${claims.aud}, want ${expectedAudience}`);
  }
  if (now > claims.exp + clockSkewSeconds) {
    throw new ClaimsError(`token expired at ${claims.exp}, now is ${now}`);
  }
  if (now < claims.iat - clockSkewSeconds) {
    throw new ClaimsError(`token issued in the future: iat ${claims.iat}, now ${now}`);
  }
}

function main(): void {
  const header = base64UrlEncode(JSON.stringify({ alg: "RS256", typ: "JWT" }));
  const now = Math.floor(Date.now() / 1000);
  const payload = base64UrlEncode(
    JSON.stringify({
      iss: "https://idp.example.com",
      aud: "relying-party-123",
      sub: "user-42",
      iat: now - 30,
      exp: now + 300,
    })
  );
  const fakeToken = header + "." + payload + ".signature-omitted";

  const claims = decodeIdTokenClaims(fakeToken);
  validateClaims(claims, "https://idp.example.com", "relying-party-123", now, 60);
  console.log("claims valid, subject is " + claims.sub);

  try {
    validateClaims(claims, "https://wrong-issuer.example.com", "relying-party-123", now, 60);
  } catch (err) {
    console.log("correctly rejected: " + (err as Error).message);
  }
}

main();

```

### Python, OIDC ID Token claims validation

Run with `python3`.

```python
import base64
import json
import time


class ClaimsError(Exception):
    pass


def base64url_decode(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def decode_id_token_claims(id_token: str) -> dict:
    parts = id_token.split(".")
    if len(parts) != 3:
        raise ClaimsError("malformed JWT, expected three dot separated parts")
    return json.loads(base64url_decode(parts[1]))


def validate_claims(
    claims: dict,
    expected_issuer: str,
    expected_audience: str,
    now: int,
    clock_skew_seconds: int,
) -> None:
    if claims.get("iss") != expected_issuer:
        raise ClaimsError(f"iss mismatch: got {claims.get('iss')}, want {expected_issuer}")
    if claims.get("aud") != expected_audience:
        raise ClaimsError(f"aud mismatch: got {claims.get('aud')}, want {expected_audience}")
    if now > claims["exp"] + clock_skew_seconds:
        raise ClaimsError(f"token expired at {claims['exp']}, now is {now}")
    if now < claims["iat"] - clock_skew_seconds:
        raise ClaimsError(f"token issued in the future: iat {claims['iat']}, now {now}")


def main() -> None:
    header = base64url_encode(json.dumps({"alg": "RS256", "typ": "JWT"}).encode("utf-8"))
    now = int(time.time())
    payload_obj = {
        "iss": "https://idp.example.com",
        "aud": "relying-party-123",
        "sub": "user-42",
        "iat": now - 30,
        "exp": now + 300,
    }
    payload = base64url_encode(json.dumps(payload_obj).encode("utf-8"))
    fake_token = f"{header}.{payload}.signature-omitted"

    claims = decode_id_token_claims(fake_token)
    validate_claims(claims, "https://idp.example.com", "relying-party-123", now, 60)
    print(f"claims valid, subject is {claims['sub']}")

    try:
        validate_claims(claims, "https://idp.example.com", "relying-party-123", now + 400, 60)
    except ClaimsError as err:
        print(f"correctly rejected: {err}")


if __name__ == "__main__":
    main()

```

### Go, SAML-style assertion Conditions validation

Run with `go run`. This sample models the SAML Conditions element's
NotBefore and NotOnOrAfter window and its AudienceRestriction, the two
checks documented in the ruby-saml README cited in dimension 9, applying
the same clock-skew tolerance from RFC 7519 to a non-JWT, XML-shaped
assertion structure to show the check is protocol-independent.

```go
package main

import (
	"errors"
	"fmt"
	"time"
)

type Conditions struct {
	NotBefore    time.Time
	NotOnOrAfter time.Time
	Audience     string
}

type Assertion struct {
	Issuer     string
	Subject    string
	Conditions Conditions
}

func validateConditions(c Conditions, expectedAudience string, now time.Time, clockSkew time.Duration) error {
	if c.Audience != expectedAudience {
		return fmt.Errorf("audience mismatch: got %s, want %s", c.Audience, expectedAudience)
	}
	if now.Before(c.NotBefore.Add(-clockSkew)) {
		return errors.New("current time is earlier than NotBefore condition")
	}
	if !now.Before(c.NotOnOrAfter.Add(clockSkew)) {
		return errors.New("current time is on or after NotOnOrAfter condition")
	}
	return nil
}

func main() {
	now := time.Now().UTC()
	assertion := Assertion{
		Issuer:  "https://idp.example.com/saml",
		Subject: "user-42",
		Conditions: Conditions{
			NotBefore:    now.Add(-2 * time.Minute),
			NotOnOrAfter: now.Add(3 * time.Minute),
			Audience:     "https://sp.example.com/metadata",
		},
	}

	if err := validateConditions(assertion.Conditions, "https://sp.example.com/metadata", now, 90*time.Second); err != nil {
		fmt.Println("rejected:", err)
	} else {
		fmt.Println("assertion valid for subject", assertion.Subject)
	}

	skewedIdP := now.Add(320 * time.Second)
	staleConditions := assertion.Conditions
	if err := validateConditions(staleConditions, "https://sp.example.com/metadata", skewedIdP, 90*time.Second); err != nil {
		fmt.Println("correctly rejected under large skew:", err)
	}
}

```

## 18. References

1. OASIS Security Services Technical Committee. "Assertions and Protocols for
   the OASIS Security Assertion Markup Language (SAML) V2.0", OASIS Standard,
   15 March 2005. docs.oasis-open.org/security/saml/v2.0/saml-core-2.0-os.pdf,
   verified 2026-08-02.
2. OpenID Foundation. "OpenID Connect Core 1.0 incorporating errata set 2".
   openid.net/specs/openid-connect-core-1_0.html, verified 2026-08-02. Cited
   for the ID Token definition, the iss, aud, exp, iat claim definitions,
   the Authorization Code Flow steps, and the exp clock-skew leeway
   statement.
3. OpenID Foundation. "OpenID Connect Discovery 1.0 incorporating errata set
   2". openid.net/specs/openid-connect-discovery-1_0.html, verified
   2026-08-02. Cited for the well-known discovery document requirement and
   the issuer, authorization_endpoint, token_endpoint, jwks_uri fields.
4. Internet Engineering Task Force. RFC 7519, "JSON Web Token (JWT)", May
   2015. www.rfc-editor.org/rfc/rfc7519, verified 2026-08-02. Cited for the
   JWT definition, the exp, nbf, iat, iss, aud, sub registered claims, and
   the clock-skew leeway language for exp and nbf.
5. Internet Engineering Task Force. RFC 6749, "The OAuth 2.0 Authorization
   Framework", October 2012, and RFC 7636, "Proof Key for Code Exchange by
   OAuth Public Clients (PKCE)", September 2015. Cited for the boundary
   between OAuth authorization and OIDC authentication described in
   dimension 1, and the PKCE recommendation in dimension 8.
6. Amazon Web Services. "SAML 2.0 federation", AWS Identity and Access
   Management User Guide.
   docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_saml.html,
   verified 2026-08-02. Cited for the AssumeRoleWithSAML production use in
   dimension 9.
7. GitHub, Inc. "About security hardening with OpenID Connect", GitHub Docs.
   docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect,
   verified 2026-08-02. Cited for the machine-to-machine OIDC federation
   production use in dimension 9.
8. The Kubernetes Authors. "Authenticating", Kubernetes Documentation.
   kubernetes.io/docs/reference/access-authn-authz/authentication/, verified
   2026-08-02. Cited for the Kubernetes API server OIDC integration in
   dimension 9.
9. Okta, Inc. (Auth0). "Identity Providers", Auth0 Docs.
   auth0.com/docs/authenticate/identity-providers, verified 2026-08-02.
   Cited for the identity-broker variant in dimension 8 and its production
   use in dimension 9.
10. OneLogin. ruby-saml library README.
    github.com/onelogin/ruby-saml/blob/master/README.md, verified
    2026-08-02. Cited for the allowed_clock_drift parameter and its
    documented rationale, referenced in dimensions 9 and 11.
11. Kim Cameron. "The Laws of Identity", Microsoft, 2005. Cited in dimension
    1 as the conceptual lineage for claims-based identity as an
    architectural style, presented as engineering philosophy and historical
    context, not as a technical specification to verify claims against.
