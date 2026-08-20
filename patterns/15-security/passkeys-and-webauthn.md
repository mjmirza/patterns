---
name: Passkeys and WebAuthn
slug: passkeys-and-webauthn
family: 15-security
category: Security
aliases: [WebAuthn, Passkey Authentication, FIDO2, Public Key Credentials]
first_described: "W3C WebAuthn Level 1, 2019"
maturity: established
related: [passwordless-authentication, session-management, zero-trust, mutual-tls, openid-connect]
incompatible_with: [password-per-request, shared-secret-login, sms-otp-primary-factor]
verified: 2026-08-02
---

# Passkeys and WebAuthn

## 1. Name, aliases, and lineage

The canonical name for this entry is Passkeys and WebAuthn. The two names
refer to different layers of the same design. A passkey is the user and product
term for a FIDO credential that can sign a challenge for one relying party.
WebAuthn is the W3C browser API that lets a web application create and use
public key credentials. FIDO describes passkeys as FIDO credentials for
passwordless authentication, built on FIDO2, meaning WebAuthn and CTAP
([https://fidoalliance.org/passkeys/](https://fidoalliance.org/passkeys/),
verified 2026-08-02). W3C WebAuthn Level 3 defines the API for creating and
using strong, scoped, public key credentials for web authentication
([https://www.w3.org/TR/webauthn-3/](https://www.w3.org/TR/webauthn-3/),
verified 2026-08-02).

Common aliases and near aliases are these.

- **WebAuthn.** The standards and browser API name. It covers registration,
  authentication, attestation, assertion verification, extensions, and the
  relying party operations.
- **Passkey authentication.** The product name used when the relying party wants
  a primary sign-in factor that avoids a password prompt. The FIDO Alliance says
  the term passkey is a common noun, not a vendor brand
  ([https://fidoalliance.org/passkeys/](https://fidoalliance.org/passkeys/),
  verified 2026-08-02).
- **FIDO2.** The standards family behind passkeys. In common deployment speech
  it means the WebAuthn browser API plus the CTAP authenticator protocol
  ([https://fidoalliance.org/passkeys/](https://fidoalliance.org/passkeys/),
  verified 2026-08-02).
- **Public key credentials.** The WebAuthn data model term. The credential has a
  private key controlled by the authenticator and a public key stored by the
  relying party.
- **Discoverable credential.** The WebAuthn term for a credential that can be
  found by the authenticator from the relying party ID without the server first
  sending a credential ID list. WebAuthn Level 3 treats passkey as a term for
  this client-side discoverable credential class
  ([https://www.w3.org/TR/webauthn-3/](https://www.w3.org/TR/webauthn-3/),
  verified 2026-08-02).
- **Resident key.** The older term retained in WebAuthn option names for
  compatibility. Level 3 marks the terminology as historical while the API keeps
  fields such as `residentKey`
  ([https://www.w3.org/TR/webauthn-3/](https://www.w3.org/TR/webauthn-3/),
  verified 2026-08-02).

The lineage is standards driven rather than book driven. W3C WebAuthn Level 1
became a Recommendation in 2019, Level 2 became a Recommendation in 2021, and
the fetched Level 3 document is a Candidate Recommendation Snapshot dated May
26, 2026
([https://www.w3.org/TR/webauthn-3/](https://www.w3.org/TR/webauthn-3/),
verified 2026-08-02). The pattern in this catalog is the server-side and
product architecture around those standards. It is established, because major
consumer and developer platforms have shipped passkeys, but its deployment
model is still moving in details such as cross-device flows, recovery policy,
sync provider choice, and enterprise attestation.

## 2. Problem and context

A web service needs strong user authentication, but passwords have become the
wrong primitive. A password is a shared secret. The server stores a verifier,
the user can type the secret into any page that asks, attackers can replay it
after phishing, and support teams must keep recovery channels strong enough to
restore real users without gifting accounts to attackers. NIST SP 800-63B says
AAL2 verifiers must offer at least one phishing-resistant option, and AAL3 uses
proof of possession of a key through a public key cryptographic protocol
([https://pages.nist.gov/800-63-4/sp800-63b.html](https://pages.nist.gov/800-63-4/sp800-63b.html),
verified 2026-08-02).

Passkeys and WebAuthn replace the shared secret ceremony with challenge
signing. During registration, the relying party sends options that include a
fresh challenge, a relying party ID, a user handle, acceptable public key
algorithms, and authenticator preferences. The browser calls
`navigator.credentials.create()` with `publicKey` options. The authenticator
creates a key pair scoped to the relying party, returns the public key and
attestation data, and keeps control of the private key. During sign-in, the
relying party sends a fresh challenge, the browser calls
`navigator.credentials.get()`, and the authenticator returns an assertion
signature over authenticator data and client data. The relying party verifies
the challenge, origin, relying party ID hash, flags, signature, credential ID,
and sign count according to the WebAuthn relying party operations
([https://www.w3.org/TR/webauthn-3/](https://www.w3.org/TR/webauthn-3/),
verified 2026-08-02).

The context matters. This pattern is for human account sign-in where the client
has a browser, operating system, password manager, platform authenticator, or
roaming authenticator that can mediate the ceremony. It fits public web
applications, enterprise SaaS, developer platforms, and native apps that bind a
web domain through the platform passkey APIs. It does not replace service to
service authentication, database credentials, API keys, session cookies, or
authorization policy. After a WebAuthn ceremony succeeds, the application still
issues and protects a session.

The design also changes who is trusted. The relying party no longer trusts a
typed password. It trusts a public key credential scoped to its relying party
ID, a browser that enforces origin rules, an authenticator that asks for user
consent and optionally user verification, and server code that performs the
verification steps with no skipped checks. The pattern is therefore a
distributed contract, not a library call.

## 3. Forces

Judgement. The following force analysis weighs operational pressure from real
login systems against the guarantees defined by the fetched standards and
platform material.

- **Phishing resistance.** Favoured. A WebAuthn credential is scoped to a relying
  party ID and used through origin-aware client code, so a lookalike site cannot
  make the authentic credential sign for the real site. FIDO and WebAuthn both
  describe this relying party scoping
  ([https://fidoalliance.org/passkeys/](https://fidoalliance.org/passkeys/),
  verified 2026-08-02;
  [https://www.w3.org/TR/webauthn-3/](https://www.w3.org/TR/webauthn-3/),
  verified 2026-08-02).
- **User reach.** Sacrificed during adoption. Some users lack current operating
  systems, browsers, or managed devices that handle passkeys well. GitHub
  reported needing cross-device registration because some platform combinations
  were not ready for direct passkey use
  ([https://github.blog/news-insights/product-news/passkeys-are-generally-available/](https://github.blog/news-insights/product-news/passkeys-are-generally-available/),
  verified 2026-08-02).
- **Recovery strength.** Favoured only if recovery is redesigned. The login
  ceremony can resist phishing while the account recovery path still relies on
  email, SMS, support desk checks, or weak identity proofing. The pattern
  improves the front door. It does not automatically harden every side door.
- **Latency.** Mixed. The server verification is cheap compared with network
  time, but the user ceremony crosses browser, operating system, authenticator,
  and sometimes a second device. Google reported passkeys being faster than
  passwords for Google Account sign-in, but local product latency still depends
  on prompt timing and recovery fallback design
  ([https://blog.google/innovation-and-ai/technology/safety-security/passkeys-default-google-accounts/](https://blog.google/innovation-and-ai/technology/safety-security/passkeys-default-google-accounts/),
  verified 2026-08-02).
- **Coupling.** Sacrificed at the platform boundary. The relying party couples
  login to browser WebAuthn behavior, device credential managers, authenticator
  transports, and JSON to binary conversions.
- **Consistency.** Favoured when verification is centralised. A single passkey
  verifier can apply the same challenge store, relying party ID, origin allow
  list, counter policy, and user verification policy to all login surfaces.
- **Operability.** Sacrificed unless telemetry is designed up front. User agent
  dialogs fail with terse client errors. The server sees only what returns from
  the ceremony. Teams need span attributes, result codes, and platform
  categorisation to debug failed registrations.
- **Cost.** Mixed. Password reset volume and credential stuffing exposure can
  fall, but implementation needs protocol parsing, test fixtures, support
  scripts, user education, credential lifecycle screens, and recovery redesign.
- **Team topology.** Favoured where identity is platform-owned. A central
  identity team can publish one verifier and account settings model. It is
  harmed when every product team implements WebAuthn parsing on its own.
- **Cognitive load.** Sacrificed. Teams must understand challenge freshness,
  origin checks, RP ID scoping, attestation choice, user verification flags,
  discoverable credentials, sign counts, backup state, and browser support.

The pattern favours phishing resistance and server-side secret reduction. It
pays for that with platform dependency, recovery complexity, and a login flow
whose failures are harder to reproduce than a rejected password.

## 4. Applicability and non-applicability

Reach for Passkeys and WebAuthn when these conditions hold.

- The product has human users and browser or native app clients that can call
  WebAuthn or platform passkey APIs.
- Phishing, credential stuffing, password reuse, or password reset abuse is a
  material risk for the accounts being protected.
- The relying party can centralise verification in one identity service rather
  than scattering WebAuthn parsing across product code.
- Account settings can expose credential naming, credential removal, backup
  credential enrollment, and recovery review.
- The product can tolerate a staged rollout where passwords, existing MFA, or
  help desk recovery remain while passkeys gain coverage.
- The security target values origin binding more than memorability. A user must
  possess a device or synced credential provider rather than remember a secret.
- The team can test with virtual authenticators, real browsers, and at least one
  platform authenticator path.
- The product can store user handles and credential IDs as opaque bytes, not as
  usernames or emails.

Do NOT reach for Passkeys and WebAuthn in these cases.

- **Machine to machine authentication.** WebAuthn is for user ceremonies
  mediated by a client and authenticator. Use mutual TLS, workload identity,
  OAuth client credentials, SPIFFE, or signed requests for services.
- **A command line tool with no browser or broker.** If the login surface cannot
  open a WebAuthn-capable browser or device broker, use device authorization
  grant, SSH keys, client certificates, or a platform credential helper.
- **Single device kiosks with shared operating system accounts.** Passkeys bind
  to a user-controlled authenticator or synced provider. Shared stations make
  account selection and recovery ambiguous.
- **A threat model that forbids synced private keys.** Consumer synced passkeys
  trade recoverability for key mobility. Use device-bound FIDO2 security keys or
  platform credentials with attestation policy where exportability is not
  acceptable. NIST states that syncable authenticators are not used at AAL3
  because sync requires exportable private keys
  ([https://pages.nist.gov/800-63-4/sp800-63b.html](https://pages.nist.gov/800-63-4/sp800-63b.html),
  verified 2026-08-02).
- **The real risk sits in recovery.** If support can reset an account after a
  weak phone call, passkeys protect only the normal path. Fix recovery first or
  in the same release.
- **The product has no session discipline.** WebAuthn proves a sign-in event. It
  does not protect long-lived bearer cookies, missing CSRF controls, or session
  fixation.
- **The team plans to skip server verification details.** A wrapper library is
  fine. Treating `navigator.credentials.get()` success as login success is not.
  The relying party still verifies challenge, origin, RP ID hash, flags, and
  signature.
- **Passwords are needed for offline local encryption.** If the password derives
  a local encryption key, replacing it with a passkey leaves a key derivation
  gap. Use a local key-wrapping design.
- **Regulated assurance demands known authenticator provenance.** Basic
  passkeys can use attestation conveyance of `none`. If policy requires
  certified hardware, design an attestation allow list and an exception process.

## 5. Structure

The pattern has seven participants.

- **Relying Party.** The web service that owns the account and RP ID. It
  generates registration and authentication challenges, stores credential public
  keys, verifies assertions, and issues sessions.
- **User Account.** The application subject. It has a stable internal account
  ID and one or more registered public key credentials. The WebAuthn `user.id`
  is an opaque handle, not an email address.
- **Credential Record.** Server-side storage for credential ID, public key,
  algorithm, sign count, transports when recorded, backup state when returned,
  user verification policy metadata, creation time, last use time, nickname,
  and revocation status.
- **Client.** The browser, web view, or native platform API caller. It enforces
  origin rules, mediates user consent, serializes client data, and talks to
  authenticators.
- **Authenticator.** The platform authenticator, roaming security key, phone, or
  credential manager component that controls the private key. It creates
  credentials, prompts for user presence and user verification as configured,
  and signs assertions.
- **Challenge Store.** A short-lived server record binding a random challenge to
  account state, ceremony type, RP ID, origin policy, and expiration. It must be
  single use.
- **Session Issuer.** The application component that turns a verified assertion
  into a session cookie, token, or federated assertion. It is separate because a
  verified WebAuthn assertion is not itself an application session.

Relationships. The relying party stores only public material and metadata. The
authenticator controls the private key. The client is not trusted to decide that
login succeeded. It is trusted to provide the browser-mediated ceremony output
that the server then verifies. The challenge store is the replay boundary. The
session issuer is the handoff into the rest of the security architecture.

## 6. ASCII structure diagram

```text
+===================+       options        +=======================+
|  Relying Party    |=====================>| Browser or App Client |
|  identity service |                      | WebAuthn API caller   |
+=========+=========+                      +===========+===========+
          |                                             |
          | stores                                      | mediates
          v                                             v
+===================+                      +=======================+
| Credential Record |<==== public key =====|     Authenticator     |
| id, key, counter  |                      | private key holder    |
+===================+                      +=======================+
          ^
          |
          | binds random bytes to ceremony
+=========+=========+
| Challenge Store   |
| expires, one use  |
+=========+=========+
          |
          | after verified assertion
          v
+===================+
|  Session Issuer   |
| cookie or token   |
+===================+

The private key never enters the relying party database.
The client never grants a session without server verification.
```

## 7. Dynamics

Registration and authentication are separate ceremonies. Registration creates a
credential record. Authentication proves control of one credential and then
continues into normal session issuance.

```text
Registration

User        Browser        Relying Party       Challenge Store   Authenticator
 |             |                 |                   |                |
 | create key  |                 |                   |                |
 |============>| POST begin      |                   |                |
 |             |================>| create challenge  |                |
 |             |                 |==================>| save, expire   |
 |             |<================| options           |                |
 |             | navigator.credentials.create()      |                |
 |             |====================================================>|
 |             |                 user consent, key pair, attestation |
 |             |<====================================================|
 |             | POST finish     |                   |                |
 |             |================>| consume challenge |                |
 |             |                 |==================>| mark used      |
 |             |                 | verify fields, store public key    |
 |<============| success         |                   |                |

Authentication

User        Browser        Relying Party       Challenge Store   Authenticator
 |             |                 |                   |                |
 | sign in     |                 |                   |                |
 |============>| POST begin      |                   |                |
 |             |================>| create challenge  |                |
 |             |                 |==================>| save, expire   |
 |             |<================| request options   |                |
 |             | navigator.credentials.get()         |                |
 |             |====================================================>|
 |             |               user verification, assertion signature|
 |             |<====================================================|
 |             | POST finish     |                   |                |
 |             |================>| consume challenge |                |
 |             |                 |==================>| mark used      |
 |             |                 | verify signature, flags, origin    |
 |             |                 | issue session                      |
 |<============| session cookie  |                   |                |
```

Operationally, begin endpoints are not authentication. They prepare a ceremony.
Finish endpoints are not trusted because a browser returned an object. They are
trusted only after the server performs the relying party verification steps.
Username-less sign-in changes the first authentication step. The server may send
an empty `allowCredentials` list, then use the returned credential ID or user
handle to locate the account. That flow improves usability, but it raises the
value of good anti-enumeration behavior and clear account picker handling.

## 8. Implementation variants

**Passwordless primary passkeys.** The user signs in with a discoverable
credential and no password prompt. This is the product shape most people mean
by passkeys. It gives the clearest user benefit, but it requires account
recovery, credential management, and backup credential enrollment to be ready.

**Passkey as second factor.** The relying party keeps the password and uses a
WebAuthn assertion as MFA. This gives phishing-resistant MFA when the password
is already deployed. It does not remove password reuse, password reset cost, or
credential stuffing at the first step. It can be a migration stage, not the end
state.

**Discoverable credentials.** The authenticator can find a credential from RP ID
without an allow list supplied by the server. This supports username-less
sign-in. The cost is greater reliance on user handles, account pickers, and
server handling of returned credential IDs.

**Non-discoverable credentials.** The server sends allowed credential IDs after
the user identifies the account. This works well for second factor and older
security key patterns. It is less smooth because username input comes first.

**Synced passkeys.** The private key material is made available across devices
through a passkey provider. FIDO describes synced and device-bound passkeys as
deployment choices
([https://fidoalliance.org/passkeys/](https://fidoalliance.org/passkeys/),
verified 2026-08-02). Synced credentials reduce device loss pain and make first
sign-in on a new device easier. They introduce provider account security and
enterprise policy questions.

**Device-bound passkeys and security keys.** The credential remains on one
authenticator. This is better for high-assurance workforce use, shared admin
accounts that are being retired, and regulated environments. It raises recovery
burden and hardware logistics.

**Attestation ignored or set to none.** Consumer sites often avoid identifying
authenticator models because attestation can add privacy and compatibility
cost. WebAuthn defines attestation conveyance preferences and attestation
formats
([https://www.w3.org/TR/webauthn-3/](https://www.w3.org/TR/webauthn-3/),
verified 2026-08-02). Ignoring attestation is usually lower friction, but it
cannot prove hardware provenance.

**Enterprise attestation policy.** The relying party verifies attestation
against allowed models or enterprise roots. This can satisfy managed-device
requirements. It needs certificate path validation, revocation policy, vendor
metadata operations, and a break-glass path when a supply chain changes.

**Native app associated domain flow.** A mobile or desktop app uses platform
APIs tied to a web domain. Apple documents AuthenticationServices APIs for
passkey registration and authentication in browser apps and related passkey use
cases
([https://developer.apple.com/documentation/authenticationservices/passkey-use-in-web-browsers](https://developer.apple.com/documentation/authenticationservices/passkey-use-in-web-browsers),
verified 2026-08-02). This gives a native experience, but app association files
and domain ownership become part of the auth deployment.

**Library-backed verifier.** The recommended server shape is a small identity
module around a mature WebAuthn library, with tests for local policy. The
library parses CBOR and COSE, verifies signatures, and handles browser encoding
differences. The application still owns challenge storage, account lookup,
session issuance, recovery, and telemetry.

## 9. Known production uses

**GitHub.com.** GitHub announced general availability of passkeys for all
GitHub.com users on September 21, 2023. The announcement says users can register
a passkey and sign in without a password, and it describes lessons from rollout
such as cross-device registration and security key upgrades
([https://github.blog/news-insights/product-news/passkeys-are-generally-available/](https://github.blog/news-insights/product-news/passkeys-are-generally-available/),
verified 2026-08-02). GitHub Docs also describes passkeys as usable for account
authentication
([https://docs.github.com/en/authentication/authenticating-with-a-passkey/about-passkeys](https://docs.github.com/en/authentication/authenticating-with-a-passkey/about-passkeys),
verified 2026-08-02).

**Google Accounts.** Google announced that passkeys became the default option
across personal Google Accounts in October 2023. The same post states that
Google Account passkeys use device checks such as fingerprint, face scan, or
PIN, and reported sign-ins being faster than passwords
([https://blog.google/innovation-and-ai/technology/safety-security/passkeys-default-google-accounts/](https://blog.google/innovation-and-ai/technology/safety-security/passkeys-default-google-accounts/),
verified 2026-08-02). Google also publishes passkey developer guidance for
sites and apps
([https://developers.google.com/identity/passkeys](https://developers.google.com/identity/passkeys),
verified 2026-08-02).

**Amazon customer accounts.** Amazon announced passkey support for browsers and
shopping apps in October 2023, then updated the post in October 2024 to state
that more than 175 million customers were using passkeys on Amazon accounts
([https://www.aboutamazon.com/news/retail/amazon-passwordless-sign-in-passkey](https://www.aboutamazon.com/news/retail/amazon-passwordless-sign-in-passkey),
verified 2026-08-02).

**Microsoft consumer accounts.** Microsoft announced passkey support for
consumer accounts in May 2024, including Microsoft 365 and Copilot on desktop
and mobile browsers. The post describes signing in with face, fingerprint, PIN,
or a security key across Windows, Google, and Apple platforms
([https://www.microsoft.com/en-us/security/blog/2024/05/02/microsoft-introduces-passkeys-for-consumer-accounts/](https://www.microsoft.com/en-us/security/blog/2024/05/02/microsoft-introduces-passkeys-for-consumer-accounts/),
verified 2026-08-02).

## 10. Consequences

Judgement. These consequences follow from the structure above and from running
account systems that must support both early adopters and recovery-heavy users.

Positive.

- The relying party no longer stores a password verifier for users who rely on
  passkeys as the primary factor.
- A phishing site cannot reuse a passkey assertion against the real origin
  because the credential is scoped to the relying party ID and the signed client
  data contains the challenge and origin.
- Credential stuffing pressure falls for enrolled users because there is no
  password to replay.
- The user can authenticate with a local device check instead of inventing, typing, and
  remembering a shared secret.
- A single account can hold several credentials, allowing staged migration,
  device diversity, and backup enrollment.
- The verifier can require user verification for higher risk actions and can
  record whether user verification occurred in the assertion flags.
- Session issuance becomes decoupled from passwords. The same verifier can feed
  web sessions, native sessions, and federated login flows.

Negative.

- The login system now depends on browser and operating system behavior that the
  relying party does not control.
- Recovery can become the weakest path. An attacker who cannot phish the
  passkey may target help desk, email recovery, phone number takeover, or an old
  password fallback.
- Support volume may rise during rollout because user agent error messages are
  difficult to translate into clear support actions.
- Attestation policy, if required, adds certificate processing and vendor
  metadata operations to the identity service.
- Some users will create credentials they do not understand, rename devices, or
  lose access to a synced provider account.
- A passkey-first flow changes analytics. The product must distinguish begin
  failures, prompt cancellations, no credential found, verification failure, and
  session issuance failure.
- The team must maintain old login paths during migration, which can leave
  mixed assurance states on the same account.

## 11. Failure modes and misuse

**Challenge replay accepted.** Symptom. A captured assertion can be submitted
twice and both requests create sessions, or a delayed finish request succeeds
after a new begin request. Cause. Challenges are not single use, not bound to
ceremony type, or not expired. Fix. Store challenges server-side with account
context, consume them atomically, and reject second use.

**Origin validation skipped.** Symptom. Assertions from a staging domain,
embedded frame, or lookalike host authenticate against production. Cause. The
server verifies the signature but ignores `clientDataJSON.origin` or uses a
loose suffix match. Fix. Compare against an explicit origin allow list for the
RP ID and environment.

**RP ID hash mismatch ignored.** Symptom. A credential created for one sibling
domain works on another domain that was not meant to share login. Cause. The
verifier accepts the credential ID and signature without checking that
authenticator data contains the expected RP ID hash. Fix. Hash the exact RP ID
policy value and reject mismatch before session issuance.

**User verification policy drift.** Symptom. A privileged action is approved by
an assertion where the UV flag is false, even though product policy says a PIN
or biometric check is needed. Cause. Begin options ask for `preferred` or finish
code does not enforce UV. Fix. Treat UV as a server-side policy check and test
both login and step-up actions.

**Account recovery bypass.** Symptom. Accounts with passkeys are still taken
over through SMS, email reset, or support override. Cause. The passkey ceremony
was hardened while recovery remained password-era policy. Fix. Require a
passkey or comparably strong proof for sensitive recovery, add waiting periods,
and alert existing sessions.

**Credential ID stored as text incorrectly.** Symptom. Some users can register
but cannot sign in, often after credentials contain bytes outside UTF-8. Cause.
Credential IDs, challenges, and user handles were stored through lossy string
conversion. Fix. Store bytes as binary or base64url, and test round trips with
random byte arrays.

**Username-less sign-in leaks account existence.** Symptom. Different error text
or timing reveals whether a returned user handle maps to an active account.
Cause. The finish endpoint exposes lookup differences. Fix. Normalize error
responses, log precise server causes privately, and rate-limit credential
discovery failures.

**Sign counter treated as a hard universal rule.** Symptom. Legitimate synced
passkey users are locked out after counter values do not increase as expected.
Cause. The verifier applies old security-key clone detection policy to all
authenticators. Fix. Store counter observations, alert on impossible movement,
but tailor enforcement to authenticator behavior and backup state.

**Browser feature detection blocks valid flows.** Symptom. Users on Linux,
Firefox, hardware keys, or cross-device sign-in see no passkey option even
though WebAuthn could work. Cause. The product gates on one platform
authenticator availability API rather than offering compatible WebAuthn paths.
Fix. Detect the WebAuthn API, then allow cross-device or security-key paths with
clear failure handling. GitHub reported this lesson from rollout
([https://github.blog/news-insights/product-news/passkeys-are-generally-available/](https://github.blog/news-insights/product-news/passkeys-are-generally-available/),
verified 2026-08-02).

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

```text
Force                Passkeys/WebAuthn        Password + TOTP
Phishing resistance  Strong by RP scoping      Weak against proxy phishing
User reach           Growing, platform bound   Very broad
Recovery pressure    Lower if redesigned       High password reset load
Server secret risk   Public keys stored        Password verifier stored
Operability          Needs ceremony telemetry  Familiar logs and errors
Team topology        Best in identity service  Often scattered in apps

Force                Magic Link                SMS OTP
Phishing resistance  Weak bearer link          Weak code relay
User reach           Email dependent           Phone dependent
Recovery pressure    Moves risk to mailbox     Moves risk to carrier
Server secret risk   Token hashes stored       OTP state stored
Operability          Link delivery debugging   Telecom delivery debugging
Team topology        Product teams can add it  Product teams can add it

Force                Mutual TLS                OpenID Connect
Phishing resistance  Strong for devices        Depends on IdP method
User reach           Poor for consumers        Good if IdP is available
Recovery pressure    Certificate lifecycle     Delegated to IdP
Server secret risk   Public certs stored       Token validation keys
Operability          Certificate debugging     Federation debugging
Team topology        Platform owned            Identity team owned
```

Reading of the matrix. Passkeys and WebAuthn win when human user phishing is
the risk and the platform can support the ceremony. Password plus TOTP wins
when every client must work today and phishing resistance is not the highest
requirement. Magic links and SMS are recovery or low-assurance options, not
peers for high-value accounts. Mutual TLS is better for managed devices and
services. OpenID Connect may wrap passkeys inside an identity provider, but OIDC
itself does not say which primary authenticator the provider used.

## 13. Related and incompatible patterns

- **Passwordless Authentication.** Passkeys are the strongest common web form of
  the broader passwordless pattern. Magic links and OTP codes fit the same
  family but do not share the same phishing resistance.
- **Session Management.** Composes after WebAuthn. A verified assertion should
  produce a session with secure cookie attributes, idle timeout, absolute
  timeout, rotation on privilege change, and revocation.
- **OpenID Connect.** Often wraps the result. An identity provider can use
  passkeys to authenticate the user, then issue OIDC tokens to relying party
  applications. The relying party must know whether it needs an authentication
  method reference or assurance claim from the provider.
- **Zero Trust.** Composes through continuous evaluation. A passkey proves a
  login event, while zero trust policy can still evaluate device state, network,
  risk, resource sensitivity, and session age.
- **Mutual TLS.** A substitute for device or workload identity, not for consumer
  human sign-in. It can compose with passkeys for managed workforce devices.
- **Risk-Based Authentication.** Composes as a step-up trigger. Risk scoring can
  decide when to ask for WebAuthn user verification again, but it should not
  silently downgrade a missing passkey to SMS for high-risk actions.
- **Shared Secret Login.** In tension with the pattern. Keeping passwords as a
  full fallback means attackers will target passwords. During migration this may
  be necessary, but the assurance story must name which accounts remain
  password-reachable.
- **Service Locator.** Conflicts in implementation. A verifier that pulls policy
  from global mutable state makes origin, RP ID, and user verification behavior
  hard to test. Prefer explicit verifier configuration.

## 14. Refactoring path in and out

Introducing Passkeys and WebAuthn into an existing password system.

1. Inventory current login, MFA, reset, support override, account deletion, and
   privileged action flows. Mark every path that can issue a session.
2. Add a credential table with binary-safe fields for credential ID, public key,
   user handle, algorithm, sign count, transports, backup state, nickname,
   creation time, last used time, and revoked time.
3. Build challenge storage before touching UI. Challenges need ceremony type,
   account or anonymous context, RP ID, allowed origins, expiration, and atomic
   consume.
4. Wrap WebAuthn verification in one server module. Use a library for CBOR,
   COSE, and signature details, but keep local policy in your code.
5. Add registration for signed-in users first. This avoids solving account
   discovery and recovery on day one.
6. Require a recent session or existing MFA before adding the first passkey to a
   sensitive account. Notify existing sessions and account email after a new
   credential is registered.
7. Add authentication using `allowCredentials` for users who type a username.
   Prove that password plus passkey and passkey-only states are represented
   clearly in account metadata.
8. Add discoverable credential sign-in only after account lookup, error
   normalization, and analytics are ready.
9. Rework recovery. Decide which recovery paths remain for accounts with
   passkeys, what waiting periods apply, and when old credentials are revoked.
10. Make passwords optional only when the account has enough recovery strength
   and at least one backup path.

Removing or reducing the pattern when it stops fitting.

1. Identify whether the issue is passkeys themselves or one variant, such as
   synced credentials, discoverable login, or attestation policy.
2. Stop new enrollment for the failing variant while keeping existing sessions
   and recovery stable.
3. Add a replacement authenticator, such as device-bound security keys,
   federated identity, or mutual TLS for managed fleets.
4. Migrate accounts by adding the replacement credential before revoking the old
   WebAuthn credential.
5. Keep verification code until the last credential record expires or is
   revoked. Deleting the verifier first strands users.
6. Archive credential metadata according to retention policy, but delete public
   keys and credential IDs when the account lifecycle requires it.

The refactoring names that apply are Extract Module for the verifier, Replace
Primitive with Object for challenge state, Introduce Parameter Object for
ceremony options, and Replace Conditional with Polymorphism only if different
authenticator policies become complex enough to deserve separate policy types.

## 15. Testing and verification

Judgement. The test plan should prove both protocol correctness and account
system behavior, because most production failures come from the glue around the
standard.

Unit tests.

- Challenge generation returns high-entropy byte arrays, stores them once, and
  rejects reuse after successful or failed finish.
- Base64url and binary fields round trip random bytes for credential IDs,
  challenges, user handles, and signatures.
- The verifier rejects wrong challenge, wrong origin, wrong RP ID hash, missing
  user presence, missing user verification when policy requires it, unknown
  credential ID, revoked credential, unsupported algorithm, expired challenge,
  and malformed client data.
- The credential store updates sign count and last-used time only after a fully
  verified assertion.
- Account lookup for discoverable credentials returns the same public error for
  unknown, disabled, and revoked credentials.

Integration tests.

- Use WebDriver virtual authenticators. WebAuthn Level 3 includes user agent
  automation support and virtual authenticator operations
  ([https://www.w3.org/TR/webauthn-3/](https://www.w3.org/TR/webauthn-3/),
  verified 2026-08-02).
- Run registration and authentication in a real browser for each supported
  origin. Include production-like HTTPS hostnames, not only localhost.
- Test cross-device and roaming key flows manually before public rollout, since
  these paths depend on operating system and browser UX.
- Test credential removal and recovery with existing active sessions.
- Test step-up flows for high-risk actions with UV required.

Security tests.

- Replay an assertion body after challenge consumption and expect rejection.
- Change `clientDataJSON.origin` and expect rejection even when the signature
  bytes are otherwise valid for the original client data.
- Substitute a credential ID from another account and expect rejection.
- Attempt registration with an excluded existing credential and expect the
  browser or server path to block duplicate enrollment.
- Exercise rate limits on begin and finish endpoints separately.

Code samples below compile or run locally. They do not implement full WebAuthn.
They isolate the server-side challenge and signature verification core so the
sample remains runnable without browser CBOR fixtures.

## 16. Observability signals

What to record.

- Ceremony type. `registration_begin`, `registration_finish`,
  `authentication_begin`, `authentication_finish`, `step_up_finish`.
- Result. Use stable private codes such as `challenge_expired`,
  `origin_mismatch`, `rp_hash_mismatch`, `signature_invalid`,
  `uv_required_missing`, `credential_revoked`, `user_cancelled`, and
  `session_issued`.
- RP ID and origin policy name, not raw user-supplied origins.
- Credential record ID or hash, account ID, and authenticator attachment when
  known. Avoid logging credential public keys, raw challenges, signatures, or
  full client data.
- Browser, operating system, and passkey provider category when available from
  client hints or support diagnostics.
- Registration funnel counts by screen and result.
- Authentication success rate by credential age, platform category, and account
  assurance state.
- Recovery attempts for passkey-enabled accounts, with reason and support path.

A healthy dashboard shows registration finish rates that are lower than begin
rates but stable by platform, authentication finish failure dominated by user
cancel and no-credential cases rather than verifier errors, and recovery volume
falling as backup credentials rise. Step-up prompts should be rare and tied to
policy.

A failing dashboard shows a spike in `origin_mismatch` after a domain change,
`challenge_expired` after client-side latency or clock changes, many
`uv_required_missing` events after policy rollout, or high registration
abandonment on one browser. A security-relevant dashboard shows a rise in
unknown credential IDs, repeated finish attempts against consumed challenges,
or recovery attempts clustered after failed passkey sign-ins.

## 17. Security and privacy implications

Judgement. The security gain is real only when the relying party verifies every
ceremony field and closes fallback paths that would otherwise issue sessions.

Security benefits.

- No reusable password is presented to the relying party during passkey login.
- A database breach of credential records exposes public keys and metadata, not
  password hashes.
- Origin and RP ID binding resist classic credential phishing.
- User verification can combine possession of the authenticator with a local
  biometric or PIN check. NIST treats biometrics as an activation factor used
  with a physical authenticator, not as a standalone authenticator
  ([https://pages.nist.gov/800-63-4/sp800-63b.html](https://pages.nist.gov/800-63-4/sp800-63b.html),
  verified 2026-08-02).

Security risks.

- Weak recovery paths become the preferred attack path.
- XSS on the real origin can still start a ceremony or confuse the user,
  although the attacker does not obtain the private key. WebAuthn Level 3 lists
  code injection among relying party security considerations
  ([https://www.w3.org/TR/webauthn-3/](https://www.w3.org/TR/webauthn-3/),
  verified 2026-08-02).
- A compromised endpoint can authenticate as the user while the attacker
  controls the session after the local device check.
- Synced passkeys move part of account security to the sync provider account.
- Attestation allow lists can lock out valid users if vendor metadata, browser
  behavior, or enterprise roots change.

Privacy implications.

- User handles should be opaque and should not contain email addresses. WebAuthn
  includes relying party privacy considerations for user handle contents
  ([https://www.w3.org/TR/webauthn-3/](https://www.w3.org/TR/webauthn-3/),
  verified 2026-08-02).
- Attestation can reveal authenticator model or enterprise device information.
  Use `none` unless policy needs provenance.
- Credential IDs are stable account artifacts. Treat them as personal account
  metadata for access control, retention, and deletion.
- Logs must not contain raw challenges, signatures, public keys, or
  authenticator data. The values are not passwords, but they can aid replay
  investigation or account correlation if mishandled.
- Cross-device flows may reveal device presence and account picker details to
  the user. Keep UI copy precise and avoid exposing account existence in server
  errors.

## Code examples

Three languages are used because they are common for identity services and can
verify the same challenge-signature idea without browser scaffolding.
TypeScript shows the JSON boundary. Python shows a compact server verifier.
Go shows explicit byte handling. Java, Rust, and Swift are omitted here because
the three selected languages cover the server-side shape without repeating the
same ECDSA flow.

### TypeScript

```typescript
const { createHash, createSign, createVerify, generateKeyPairSync } = require("crypto");

type StoredPasskey = {
  id: string;
  publicKeyPem: string;
  signCount: number;
};

function b64url(input: Buffer): string {
  return input.toString("base64url");
}

function clientData(challenge: Buffer, origin: string): Buffer {
  return Buffer.from(JSON.stringify({
    type: "webauthn.get",
    challenge: b64url(challenge),
    origin,
  }));
}

function verifyAssertion(
  credential: StoredPasskey,
  challenge: Buffer,
  origin: string,
  authenticatorData: Buffer,
  signature: Buffer,
  nextSignCount: number,
): boolean {
  if (nextSignCount <= credential.signCount) return false;
  const client = clientData(challenge, origin);
  const signedBytes = Buffer.concat([
    authenticatorData,
    createHash("sha256").update(client).digest(),
  ]);
  const verifier = createVerify("sha256");
  verifier.update(signedBytes);
  verifier.end();
  return verifier.verify(credential.publicKeyPem, signature);
}

const { publicKey, privateKey } = generateKeyPairSync("ec", {
  namedCurve: "prime256v1",
});
const challenge = Buffer.from("0123456789abcdef0123456789abcdef");
const authenticatorData = Buffer.from("rp-hash-flags-counter");
const client = clientData(challenge, "https://example.com");
const signedBytes = Buffer.concat([
  authenticatorData,
  createHash("sha256").update(client).digest(),
]);
const signer = createSign("sha256");
signer.update(signedBytes);
signer.end();
const signature = signer.sign(privateKey);

const credential = {
  id: "cred-1",
  publicKeyPem: publicKey.export({ type: "spki", format: "pem" }).toString(),
  signCount: 3,
};

console.log(verifyAssertion(
  credential,
  challenge,
  "https://example.com",
  authenticatorData,
  signature,
  4,
));
```

### Python

```python
import base64
import hashlib
import json

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def client_data(challenge: bytes, origin: str) -> bytes:
    body = {
        "type": "webauthn.get",
        "challenge": b64url(challenge),
        "origin": origin,
    }
    return json.dumps(body, separators=(",", ":")).encode("utf-8")


def signed_bytes(authenticator_data: bytes, client: bytes) -> bytes:
    return authenticator_data + hashlib.sha256(client).digest()


def verify_assertion(public_pem: bytes, authenticator_data: bytes,
                     client: bytes, signature: bytes) -> bool:
    public_key = serialization.load_pem_public_key(public_pem)
    try:
        public_key.verify(
            signature,
            signed_bytes(authenticator_data, client),
            ec.ECDSA(hashes.SHA256()),
        )
        return True
    except Exception:
        return False


private_key = ec.generate_private_key(ec.SECP256R1())
public_pem = private_key.public_key().public_bytes(
    serialization.Encoding.PEM,
    serialization.PublicFormat.SubjectPublicKeyInfo,
)
challenge = b"0123456789abcdef0123456789abcdef"
authenticator_data = b"rp-hash-flags-counter"
client = client_data(challenge, "https://example.com")
signature = private_key.sign(
    signed_bytes(authenticator_data, client),
    ec.ECDSA(hashes.SHA256()),
)

print(verify_assertion(public_pem, authenticator_data, client, signature))
```

### Go

```go
package main

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/sha256"
	"encoding/asn1"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"math/big"
)

type ClientData struct {
	Type      string `json:"type"`
	Challenge string `json:"challenge"`
	Origin    string `json:"origin"`
}

type ecdsaSignature struct {
	R *big.Int
	S *big.Int
}

func b64url(data []byte) string {
	return base64.RawURLEncoding.EncodeToString(data)
}

func clientData(challenge []byte, origin string) []byte {
	body, err := json.Marshal(ClientData{
		Type:      "webauthn.get",
		Challenge: b64url(challenge),
		Origin:    origin,
	})
	if err != nil {
		panic(err)
	}
	return body
}

func signedBytes(authenticatorData []byte, client []byte) []byte {
	hash := sha256.Sum256(client)
	return append(authenticatorData, hash[:]...)
}

func verifyAssertion(publicKey *ecdsa.PublicKey, authenticatorData []byte,
	client []byte, signature []byte) bool {
	var sig ecdsaSignature
	if _, err := asn1.Unmarshal(signature, &sig); err != nil {
		return false
	}
	digest := sha256.Sum256(signedBytes(authenticatorData, client))
	return ecdsa.Verify(publicKey, digest[:], sig.R, sig.S)
}

func main() {
	privateKey, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		panic(err)
	}
	challenge := []byte("0123456789abcdef0123456789abcdef")
	authenticatorData := []byte("rp-hash-flags-counter")
	client := clientData(challenge, "https://example.com")
	digest := sha256.Sum256(signedBytes(authenticatorData, client))
	r, s, err := ecdsa.Sign(rand.Reader, privateKey, digest[:])
	if err != nil {
		panic(err)
	}
	signature, err := asn1.Marshal(ecdsaSignature{R: r, S: s})
	if err != nil {
		panic(err)
	}
	fmt.Println(verifyAssertion(
		&privateKey.PublicKey,
		authenticatorData,
		client,
		signature,
	))
}
```

## 18. References

1. W3C Web Authentication Working Group. *Web Authentication: An API for
   accessing Public Key Credentials, Level 3*. Candidate Recommendation
   Snapshot, 26 May 2026.
   [https://www.w3.org/TR/webauthn-3/](https://www.w3.org/TR/webauthn-3/).
   Verified 2026-08-02. Source for WebAuthn terminology, ceremony structure,
   relying party operations, authenticator model, attestation, automation,
   security considerations, and privacy considerations.
2. W3C Web Authentication Working Group. *Web Authentication: An API for
   accessing Public Key Credentials, Level 2*. W3C Recommendation, 8 April
   2021.
   [https://www.w3.org/TR/2021/REC-webauthn-2-20210408/](https://www.w3.org/TR/2021/REC-webauthn-2-20210408/).
   Verified 2026-08-02. Source for lineage as a stable W3C Recommendation.
3. FIDO Alliance. *Passkeys FAQ*.
   [https://fidoalliance.org/passkeys/](https://fidoalliance.org/passkeys/).
   Verified 2026-08-02. Source for passkey terminology, FIDO2 relationship,
   synced and device-bound passkey distinction, and phishing-resistance claims.
4. passkeys.dev contributors. *Terms*.
   [https://passkeys.dev/docs/reference/terms/](https://passkeys.dev/docs/reference/terms/).
   Verified 2026-08-02. Source for implementation vocabulary used by passkey
   deployment guides.
5. MDN Web Docs. *Web Authentication API*.
   [https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API).
   Verified 2026-08-02. Source for browser API context.
6. National Institute of Standards and Technology. *Digital Identity Guidelines,
   Authentication and Authenticator Management, SP 800-63B*.
   [https://pages.nist.gov/800-63-4/sp800-63b.html](https://pages.nist.gov/800-63-4/sp800-63b.html).
   Verified 2026-08-02. Source for AAL2 phishing-resistant option, AAL3 public
   key and non-exportability requirements, and biometric activation-factor
   treatment.
7. GitHub. Hirsch Singhal. *Passkeys are generally available*. GitHub Blog,
   21 September 2023.
   [https://github.blog/news-insights/product-news/passkeys-are-generally-available/](https://github.blog/news-insights/product-news/passkeys-are-generally-available/).
   Verified 2026-08-02. Source for GitHub production use and rollout lessons.
8. GitHub Docs. *About passkeys*.
   [https://docs.github.com/en/authentication/authenticating-with-a-passkey/about-passkeys](https://docs.github.com/en/authentication/authenticating-with-a-passkey/about-passkeys).
   Verified 2026-08-02. Source for GitHub account passkey documentation.
9. Google. Sriram Karra and Christiaan Brand. *Passwordless by default: Make the
   switch to passkeys*. Google Blog, 10 October 2023.
   [https://blog.google/innovation-and-ai/technology/safety-security/passkeys-default-google-accounts/](https://blog.google/innovation-and-ai/technology/safety-security/passkeys-default-google-accounts/).
   Verified 2026-08-02. Source for Google Account production use.
10. Google for Developers. *Passkeys*.
   [https://developers.google.com/identity/passkeys](https://developers.google.com/identity/passkeys).
   Verified 2026-08-02. Source for Google developer guidance.
11. Amazon Staff. *Amazon is making it easier and safer for you to access your
   account with passwordless sign-in*. About Amazon, 23 October 2023, updated
   15 October 2024.
   [https://www.aboutamazon.com/news/retail/amazon-passwordless-sign-in-passkey](https://www.aboutamazon.com/news/retail/amazon-passwordless-sign-in-passkey).
   Verified 2026-08-02. Source for Amazon production use and adoption number.
12. Microsoft Security. Vasu Jakkal and Joy Chik. *Microsoft introduces passkeys
   for consumer accounts*. Microsoft Security Blog, 2 May 2024.
   [https://www.microsoft.com/en-us/security/blog/2024/05/02/microsoft-introduces-passkeys-for-consumer-accounts/](https://www.microsoft.com/en-us/security/blog/2024/05/02/microsoft-introduces-passkeys-for-consumer-accounts/).
   Verified 2026-08-02. Source for Microsoft consumer account production use.
13. Apple Developer Documentation. *Passkey use in web browsers*.
   [https://developer.apple.com/documentation/authenticationservices/passkey-use-in-web-browsers](https://developer.apple.com/documentation/authenticationservices/passkey-use-in-web-browsers).
   Verified 2026-08-02. Source for Apple AuthenticationServices browser passkey
   API context.
