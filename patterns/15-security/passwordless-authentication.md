---
name: Passwordless Authentication
slug: passwordless-authentication
family: 15-security
category: Security
aliases: [Passwordless Login, Passwordless Sign-In, Passkey Authentication, Magic Link Login, FIDO2 Passwordless]
first_described: "FIDO Alliance FIDO2 and W3C WebAuthn, 2018"
maturity: established
related: [passkeys-webauthn, session-management, token-based-authentication, openid-connect, zero-trust, secure-by-default]
incompatible_with: [password-per-request, shared-secret-login, knowledge-based-authentication]
verified: 2026-08-02
---

# Passwordless Authentication

## 1. Name, aliases, and lineage

The canonical name is Passwordless Authentication. The name covers login systems
where the verifier does not ask the user to present a centrally verified
password during the normal sign-in ceremony. The strongest modern form uses a
public key credential bound to a relying party origin, exposed to web
applications through the W3C Web Authentication API. The W3C WebAuthn Level 3
Candidate Recommendation defines an API for creating and using public key
credentials scoped to a WebAuthn Relying Party, with user agent mediation and
authenticator consent
([https://www.w3.org/TR/webauthn-3/](https://www.w3.org/TR/webauthn-3/),
verified 2026-08-02).

The common aliases are these.

- **Passwordless login.** The product and support term. It is broad enough to
  include passkeys, email links, one-time codes, device certificates, and
  account broker flows.
- **Passwordless sign-in.** The enterprise identity term, common in Microsoft
  Entra material for FIDO2 passkeys
  ([https://learn.microsoft.com/en-us/entra/identity/authentication/concept-authentication-passkeys-fido2](https://learn.microsoft.com/en-us/entra/identity/authentication/concept-authentication-passkeys-fido2),
  verified 2026-08-02).
- **Passkey authentication.** The FIDO term for passwordless sign-in with FIDO
  credentials. FIDO describes passkeys as cryptographic credentials tied to a
  user account and built on FIDO2 specifications
  ([https://fidoalliance.org/passkeys/](https://fidoalliance.org/passkeys/),
  verified 2026-08-02).
- **Magic link login.** A lower-assurance email variant where possession of an
  email inbox is used to redeem a short-lived login URL.
- **FIDO2 passwordless.** The standards phrase for WebAuthn plus CTAP, where
  WebAuthn is the browser API and CTAP covers authenticator communication. FIDO
  states that passkeys are built on FIDO2, with WebAuthn and CTAP as the
  relevant standards
  ([https://fidoalliance.org/passkeys/](https://fidoalliance.org/passkeys/),
  verified 2026-08-02).

The lineage is mixed because the pattern is not a single protocol. Email-based
login grew from password reset flows and bearer-token session links. Enterprise
passwordless grew from smart cards, client certificates, and hardware security
keys. Consumer passkeys grew from the FIDO U2F and FIDO2 work, then reached the
web through WebAuthn. WebAuthn Level 1 became a W3C Recommendation in March
2019, Level 2 became a Recommendation in April 2021, and Level 3 is the fetched
Candidate Recommendation dated May 26, 2026
([https://www.w3.org/TR/webauthn-3/](https://www.w3.org/TR/webauthn-3/),
verified 2026-08-02).

This entry treats Passwordless Authentication as an established security
pattern. It is established because major identity platforms have shipped it to
large user populations, not because every variant has equal assurance. A magic
link and a WebAuthn passkey share the absence of a password prompt, but they do
not share the same phishing resistance, recovery model, or operational risk.

## 2. Problem and context

A user-facing system needs to authenticate people without making a reusable
shared secret the center of the login ceremony. The immediate pain is familiar.
Users reuse passwords, choose weak passwords, forget them, paste them into fake
sites, and then ask support to recover accounts. Operators store salted password
hashes, maintain breach blocklists, throttle guessing, tune bot defenses, and
still treat the password database as an asset that attackers want. NIST SP
800-63B states that centrally verified passwords are not phishing-resistant
([https://pages.nist.gov/800-63-4/sp800-63b.html](https://pages.nist.gov/800-63-4/sp800-63b.html),
verified 2026-08-02).

Passwordless Authentication changes the account proof. Instead of "the claimant
knows the current password," the ceremony asks for control of a registered
authenticator or a delivery channel. In the passkey form, the verifier stores a
public key and challenges the user's authenticator to sign fresh data. The
private key remains on the user's device or in a passkey provider. Google
describes its Google Account passkey flow as storing the private key on user
devices, uploading the corresponding public key to Google, asking the device to
sign a unique challenge, and verifying that signature with the public key
([https://security.googleblog.com/2023/05/so-long-passwords-thanks-for-all-phish.html](https://security.googleblog.com/2023/05/so-long-passwords-thanks-for-all-phish.html),
verified 2026-08-02).

The context that makes the pattern attractive has four traits.

- The service is exposed to remote attackers, so credential stuffing and
  phishing are material risks.
- Users already have devices that can hold authenticators, such as phones,
  laptops, platform authenticators, or external security keys.
- The system can carry an enrollment and recovery process, because losing every
  authenticator is an account continuity event.
- The application separates authentication from session management. Passwordless
  proves identity at sign-in. The application still needs session issuance,
  rotation, revocation, and reauthentication rules.

The pattern is not "no secrets." It is "no centrally verified user password in
the normal remote login path." A WebAuthn deployment still has private keys,
challenge nonces, session cookies, recovery tokens, device PINs, and
provider account secrets. The difference is where those secrets live and whether
an attacker can replay them at the relying party.

## 3. Forces

Engineering judgement. This dimension weighs operational forces. Citations
establish standards behavior and named deployments, not the ranking itself.

- **Phishing resistance.** Favoured when the variant is passkeys, FIDO2 security
  keys, or another origin-bound cryptographic protocol. Sacrificed when the
  variant is an email magic link, because a bearer link can be forwarded,
  stolen from a mailbox, or captured from a compromised endpoint.
- **Account recovery.** Sacrificed. Password reset has ugly security properties,
  but users understand it. Passwordless systems need recovery contacts, backup
  authenticators, support proofing, or provider sync, each with its own abuse
  cases.
- **Latency.** Mixed. A local passkey ceremony can be fast. An email link
  depends on mail delivery, spam filtering, and the user's ability to switch
  contexts.
- **Coupling.** Sacrificed at the platform boundary. The application becomes
  coupled to browser WebAuthn support, passkey provider behavior, email
  delivery, device policy, or an identity provider.
- **Consistency.** Favoured by cryptographic variants because the server
  verifies a uniform challenge-response transcript. Sacrificed by multi-channel
  variants where mobile, desktop, and support recovery paths may diverge.
- **Operability.** Sacrificed unless teams invest in telemetry. Login failures
  now involve browser capability, authenticator selection, origin checks, mail
  delivery, recovery policy, and device state.
- **Cost.** Mixed. A passkey deployment can reduce password reset and fraud
  costs, but it adds enrollment design, recovery operations, device support, and
  identity platform configuration. Hardware keys add purchase and inventory
  cost.
- **Team topology.** Favoured when a central identity team owns the ceremonies
  and applications consume a token. Sacrificed when each product team builds its
  own magic-link or WebAuthn verifier.
- **Cognitive load.** Sacrificed for engineers and support staff. They must
  distinguish passwordless variants, authenticator attachment, user
  verification, attestation, account recovery, and session risk.

The pattern favours resistance to reusable-secret compromise. It sacrifices the
simplicity of a password field and a hash comparison.

## 4. Applicability and non-applicability

Reach for Passwordless Authentication when these conditions hold.

- The service is a public or employee-facing application where password reuse,
  phishing, or credential stuffing drives measurable account risk.
- The user population has access to devices, browsers, or identity providers
  that support the chosen passwordless ceremony.
- The organization can operate recovery without converting recovery into a
  weaker password reset path.
- The application already has or can build a sound session layer after
  authentication succeeds.
- High-risk users can enroll more than one authenticator, so one lost device
  does not become an emergency support bypass.
- The security target is compatible with the chosen variant. Use passkeys or
  device-bound keys for phishing-resistant login. Use magic links only where
  email account possession is acceptable proof.
- The product can explain device sharing and account switching clearly. A
  passkey created on a shared machine may let another local user sign in if
  they can open that device.

Do NOT reach for Passwordless Authentication in these cases.

- **The only available fallback is a weak password reset path.** Reason. The
  attacker will ignore the stronger front door and attack recovery.
- **The user population lacks compatible devices or mail access.** Reason. The
  ceremony becomes a support queue rather than an authentication system.
- **The application cannot own session security.** Reason. Passwordless login
  does not protect a bearer session cookie after issuance.
- **The team wants to avoid MFA work.** Reason. A passkey may satisfy multiple
  factors when user verification is requested, but policy, enrollment, recovery,
  and step-up still need design. GitHub states that passkeys can count as two
  factors for its accounts because they validate identity and possession of a
  device
  ([https://github.blog/changelog/2023-09-21-passkeys-are-generally-available/](https://github.blog/changelog/2023-09-21-passkeys-are-generally-available/),
  verified 2026-08-02). That product decision does not transfer to every risk
  model.
- **The service needs AAL3 and plans to rely on syncable passkeys.** Reason.
  NIST SP 800-63B says syncable authenticators are not used at AAL3 because
  their private keys are exportable in the sync model
  ([https://pages.nist.gov/800-63-4/sp800-63b.html](https://pages.nist.gov/800-63-4/sp800-63b.html),
  verified 2026-08-02).
- **The login identifier is highly sensitive and enumeration cannot be masked.**
  Reason. Email-link and code flows often reveal whether an account exists
  through timing, copy, or delivery side effects.
- **The product cannot support accessible alternatives.** Reason. A biometric
  prompt, camera-based cross-device flow, or hardware key requirement may block
  users with disability, damaged devices, managed browsers, or restricted work
  environments.
- **The organization cannot accept external identity dependencies.** Reason.
  Passkey sync and identity-provider passwordless may depend on Apple, Google,
  Microsoft, 1Password, enterprise device management, or mail providers.
- **The threat is local device takeover.** Reason. Passwordless improves remote
  phishing resistance, but a local attacker who controls the device after sign-in
  may ride the user's session or use an available authenticator.

## 5. Structure

The participants are roles, not classes.

- **Claimant.** The person trying to sign in. The claimant controls an
  authenticator or delivery channel previously bound to the account.
- **Relying Party.** The application or identity service that accepts the
  passwordless proof and issues an application session or token.
- **Authenticator.** The device, key, app, or channel that produces the proof.
  In WebAuthn this is a platform authenticator, roaming security key, or
  passkey provider accessed through the browser.
- **Credential Binding Store.** The server-side record that binds an account to
  a public key, credential ID, authenticator metadata, email address, phone
  number, device certificate, or identity-provider subject.
- **Challenge Issuer.** The component that creates a fresh nonce, stores its
  purpose, expiry, account context, and request context, then rejects replay.
- **Verifier.** The component that checks the proof. For passkeys it validates
  the origin, relying-party ID, challenge, signature, user presence, user
  verification when required, and credential binding.
- **Recovery Authority.** The process that restores access after authenticator
  loss. It may be self-service with backup authenticators, administrator
  mediated, identity-provider mediated, or support mediated.
- **Session Issuer.** The component that converts a successful authentication
  event into a session cookie, OAuth or OIDC token, or device grant.
- **Risk Engine.** Optional but common. It decides when to require a stronger
  ceremony, deny a fallback, or step up before a sensitive action.

The relationship is a binding loop followed by an assertion loop. Enrollment
binds an authenticator to an account. Authentication proves current control of
that bound authenticator. Recovery binds a replacement authenticator after a
separate proof.

## 6. ASCII structure diagram

```text
        +------------------+          +-------------------------+
        |     Claimant     |          |     Recovery Authority  |
        |  person signing  |          |  backup and rebind path |
        +---------+--------+          +------------+------------+
                  |                                |
                  | unlocks                        | rebinds after
                  v                                | loss or risk
        +------------------+                       |
        |  Authenticator   |                       |
        | passkey, key,    |                       |
        | email, device    |                       |
        +---------+--------+                       |
                  | proof                          |
                  v                                v
        +------------------+      reads      +--------------------+
        |     Verifier     | <-------------  | Credential Binding |
        | checks challenge |                 | Store              |
        | and binding      | --------------> | account to proof   |
        +---------+--------+      updates    +--------------------+
                  ^
                  |
        +---------+--------+
        | Challenge Issuer |
        | nonce, expiry,   |
        | purpose, context |
        +---------+--------+
                  |
                  v
        +------------------+       emits     +--------------------+
        |  Relying Party   | ------------->  |   Session Issuer   |
        | app or IdP       |                 | cookie or token    |
        +------------------+                 +--------------------+
```

## 7. Dynamics

A WebAuthn passkey login has two ceremonies. Registration creates and stores a
public key credential. Authentication signs a fresh challenge. WebAuthn calls
these relying party operations "Registering a New Credential" and "Verifying an
Authentication Assertion"
([https://www.w3.org/TR/webauthn-3/](https://www.w3.org/TR/webauthn-3/),
verified 2026-08-02).

```text
Registration

Claimant     Browser     Authenticator     Relying Party     Binding Store
   |            |              |                 |                 |
   | enroll ---->              |                 |                 |
   |            |-- options request -----------> |                 |
   |            |<-- challenge, rp id, policy ---|                 |
   |            |-- create credential ---------->|                 |
   |            |              |-- user verify --|                 |
   |            |<-- public key, id, attestation-|                 |
   |            |-- registration response ------>|                 |
   |            |              |                 |-- store binding |
   |<-- enrolled|              |                 |                 |

Authentication

Claimant     Browser     Authenticator     Relying Party     Binding Store
   |            |              |                 |                 |
   | sign in -->|              |                 |                 |
   |            |-- challenge request ---------> |                 |
   |            |<-- nonce, rp id, allowed ids --|                 |
   |            |-- get assertion -------------->|                 |
   |            |              |-- user verify --|                 |
   |            |<-- signature, client data -----|                 |
   |            |-- assertion response --------->|                 |
   |            |              |                 |-- read public key
   |            |              |                 |-- verify origin |
   |            |              |                 |-- verify nonce  |
   |            |              |                 |-- verify sig    |
   |<-- session |              |                 |                 |
```

Magic-link login has the same challenge shape but different security
properties. The challenge is a bearer token in a URL delivered over email. The
verifier checks token hash, expiry, purpose, and single use, then creates a
session. There is no origin-bound private key, so the link must be treated as a
high-value bearer secret.

## 8. Implementation variants

**Passkeys with WebAuthn.** The preferred web variant. The server stores the
credential ID and public key. At login it issues a challenge, receives an
assertion, validates origin and relying-party ID, verifies the signature, checks
user presence, and checks user verification when policy requires it. NIST
describes phishing resistance for properly configured syncable authenticators
as coming from a key pair constrained to the domain where it was created
([https://pages.nist.gov/800-63-4/sp800-63b.html](https://pages.nist.gov/800-63-4/sp800-63b.html),
verified 2026-08-02). Trade-off. Best remote attack resistance, highest browser
and platform complexity.

**Device-bound FIDO2 security keys.** A roaming authenticator holds a credential
that is not synced. This is the usual high-assurance employee or administrator
variant. Microsoft notes that FIDO2 security keys are recommended for highly
regulated industries or elevated users, with cost and helpdesk impact when keys
are lost
([https://learn.microsoft.com/en-us/entra/identity/authentication/concept-authentication-passkeys-fido2](https://learn.microsoft.com/en-us/entra/identity/authentication/concept-authentication-passkeys-fido2),
verified 2026-08-02). Trade-off. Strong device provenance and loss resistance
when backup keys exist, weaker consumer convenience.

**Synced passkeys.** A passkey provider syncs encrypted credential material
across the user's devices. FIDO distinguishes synced passkeys from
device-bound passkeys
([https://fidoalliance.org/passkeys/](https://fidoalliance.org/passkeys/),
verified 2026-08-02). Trade-off. Better adoption and recovery, less control
over key copy count. NIST excludes syncable authenticators from AAL3 because
the private key is exportable in the sync model
([https://pages.nist.gov/800-63-4/sp800-63b.html](https://pages.nist.gov/800-63-4/sp800-63b.html),
verified 2026-08-02).

**Email magic links.** The server sends a short-lived, single-use URL to an
address already bound to the account. Trade-off. Very simple to adopt and easy
for many users, but security reduces to mailbox control plus link secrecy.
Use it for low to moderate assurance or as a recovery step protected by risk
controls.

**One-time email or SMS codes.** The user copies a numeric or alphanumeric code
from a delivery channel. NIST states that single-factor OTP authentication is
not phishing-resistant
([https://pages.nist.gov/800-63-4/sp800-63b.html](https://pages.nist.gov/800-63-4/sp800-63b.html),
verified 2026-08-02). Trade-off. Compatible with old clients, vulnerable to
real-time relay, SIM swap for SMS, mailbox compromise for email, and code
phishing.

**Native app device binding.** A mobile or desktop app stores a private key in
the platform keystore and signs server challenges. Trade-off. Good for native
control and device posture, but it needs platform-specific storage, key
rotation, account transfer, and jailbreak or rooted-device policy.

**IdP-mediated passwordless.** The application redirects to an identity
provider that owns passwordless enrollment and returns an OIDC assertion.
Trade-off. The application team avoids protocol complexity, but all assurance
and recovery depend on IdP configuration. OpenID Connect is the natural
companion when the relying party is not the authenticator verifier.

**Client certificate or smart-card login.** The user proves possession of a
certificate-backed key, often under enterprise device management. Trade-off.
Strong for managed fleets, brittle for public web users, proxies, mobile
browser support, and certificate lifecycle.

## 9. Known production uses

**GitHub.com passkeys.** GitHub announced passkeys as generally available for
all GitHub.com users on September 21, 2023. The changelog states that a passkey
can be used without entering a password or username and without a separate 2FA
step when 2FA is enabled, because the passkey validates identity and possession
of a device
([https://github.blog/changelog/2023-09-21-passkeys-are-generally-available/](https://github.blog/changelog/2023-09-21-passkeys-are-generally-available/),
verified 2026-08-02).

**Google Accounts passkeys.** Google announced passkey support for Google
Accounts in May 2023. Its security blog describes creating a passkey on a local
computer or mobile device, using the device screen lock to confirm the user,
and verifying a signed unique challenge with the stored public key
([https://security.googleblog.com/2023/05/so-long-passwords-thanks-for-all-phish.html](https://security.googleblog.com/2023/05/so-long-passwords-thanks-for-all-phish.html),
verified 2026-08-02).

**Microsoft Entra ID passkeys.** Microsoft documents passkeys for Microsoft
Entra ID and describes a sign-in flow where Entra sends a challenge, the
authenticator locates the key pair using the hashed relying-party ID and
credential ID, the user unlocks with biometric or PIN, and Entra verifies the
signature before issuing a token
([https://learn.microsoft.com/en-us/entra/identity/authentication/concept-authentication-passkeys-fido2](https://learn.microsoft.com/en-us/entra/identity/authentication/concept-authentication-passkeys-fido2),
verified 2026-08-02).

**Apple iCloud Keychain passkey sync.** Apple documents iCloud Keychain as
syncing passwords and passkeys between Apple devices without exposing them to
Apple. This entry cites Apple only for platform support, not for server-side
implementation detail, because the primary fetched production details above are
from GitHub, Google, and Microsoft
([https://support.apple.com/guide/security/icloud-keychain-security-overview-sec1c89c6f3b/web](https://support.apple.com/guide/security/icloud-keychain-security-overview-sec1c89c6f3b/web),
verified 2026-08-02).

**1Password passkey provider.** 1Password documents creating, storing,
managing, sharing, and using passkeys in 1Password for websites and apps
([https://1password.com/product/passkeys](https://1password.com/product/passkeys),
verified 2026-08-02). This is a production ecosystem use rather than a relying
party deployment.

## 10. Consequences

Engineering judgement. The consequences below describe design pressure from
the pattern rather than guarantees made by any one vendor.

Positive.

- The verifier no longer stores password hashes for normal login, which removes
  a database asset that supports offline guessing after breach.
- Passkey and FIDO2 variants reduce phishing value because the authenticator
  signs for the intended relying party rather than handing a reusable secret to
  the page.
- Credential stuffing loses most of its target when there is no password to try.
- Users can authenticate with a device approval action they already know.
- The server can represent authentication strength more accurately. A
  device-bound key, a synced passkey, an email link, and an SMS code can be
  tracked as different methods.
- A central identity provider can upgrade login policy for many applications
  without each application changing its own login screen.

Negative.

- Recovery becomes the main attack surface. If recovery is weak, the pattern is
  theater.
- Helpdesk and support staff need new playbooks for lost keys, new phones,
  shared devices, stale email addresses, browser errors, and authenticator
  enrollment disputes.
- Browser and platform compatibility shape the product. A server cannot force a
  client to have a working platform authenticator.
- Magic-link variants can create account takeover paths through mailbox
  compromise, URL logging, forwarded messages, or malware that reads browser
  history.
- Passkey sync shifts part of trust to a provider account and its recovery
  controls.
- Device-bound keys can lock users out unless backup keys or alternate
  authenticators are enrolled before loss.
- Compliance language may lag product language. "Passwordless" must be mapped
  to concrete authenticator types and assurance levels for auditors.

## 11. Failure modes and misuse

Engineering judgement. Each item is written as an observable Symptom, Cause,
Fix triple.

**Fallback takeover.** Symptom. Accounts with passkeys are still taken over
through "lost device" support tickets or email fallback. Cause. Recovery accepts
weaker proof than the normal login path. Fix. Treat recovery as a separate
high-risk ceremony, require backup authenticators where possible, delay risky
changes, notify existing channels, and block high-value actions after recovery
until risk settles.

**Magic-link replay.** Symptom. A login link works twice, or works after being
opened by a mail scanner before the user clicks it. Cause. The token is not
single use, or the scanner's request consumes it without a user confirmation
step. Fix. Store only a token hash, bind token purpose and expiry, mark it used
atomically, and require a confirmation page before issuing a session.

**User enumeration.** Symptom. The "check your email" screen appears faster or
with different copy for existing accounts. Cause. The request path exits early
for unknown users or sends different responses. Fix. Return uniform copy and
similar timing, throttle by IP and identifier, and move delivery differences out
of the observable response. OWASP warns that authentication responses can create
user enumeration discrepancies
([https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html),
verified 2026-08-02).

**Origin mismatch.** Symptom. Passkey login works in staging but fails in
production, or fails on one subdomain only. Cause. The relying-party ID or
origin used at registration does not match the authentication origin. Fix.
Model RP IDs explicitly, test every domain and environment, and never reuse a
production credential binding for an unrelated origin.

**Shared-device surprise.** Symptom. A family member or coworker signs in as the
account owner on a shared computer. Cause. A passkey was enrolled on a device
whose local access secret is shared or weak. Fix. Warn during enrollment on shared
devices, allow passkey names and revocation, and require step-up for sensitive
actions from newly enrolled authenticators.

**Unbounded challenge store.** Symptom. Redis or database rows for login
challenges grow during bot traffic. Cause. The server stores every issued
challenge until expiry without rate limits or cleanup. Fix. Set short TTLs,
rate-limit challenge issuance, cap outstanding challenges per identifier, and
garbage collect expired rows.

**Overclaiming assurance.** Symptom. Product copy says "phishing proof" while
the actual enabled method is email code or SMS. Cause. The team applies passkey
properties to every passwordless variant. Fix. Store authenticator type and
assurance in the login event, and use precise policy labels such as
`phishing_resistant`, `device_bound`, and `mailbox_possession`.

**No reauthentication path.** Symptom. A user signed in by magic link can
change payout details without fresh proof. Cause. The session layer treats all
passwordless logins as equal for all actions. Fix. Add step-up policy tied to
action risk, session age, device state, and authenticator type.

**Attestation policy breakage.** Symptom. A rollout blocks consumer passkeys
that worked in pilot. Cause. The relying party requires attestation that synced
passkey providers do not expose. Microsoft documents that, in Entra ID, enabling
attestation excludes synced passkeys
([https://learn.microsoft.com/en-us/entra/identity/authentication/concept-authentication-passkeys-fido2](https://learn.microsoft.com/en-us/entra/identity/authentication/concept-authentication-passkeys-fido2),
verified 2026-08-02). Fix. Apply attestation only to populations that need
device provenance, and run separate policies for workforce administrators and
general consumers.

## 12. Trade-off matrix

Compared against named alternatives, across the forces from dimension 3.

| Force | Passwordless Authentication | Password plus TOTP | Password plus SMS OTP | SAML or OIDC to external IdP | Client certificate login | Recovery-code login |
|---|---|---|---|---|---|---|
| Phishing resistance | High for passkeys, low for links | Low to medium. TOTP can be relayed | Low. SMS codes can be relayed | Depends on IdP method | High when bound to TLS client auth | Low. Codes are bearer secrets |
| Password database risk | Removed for normal login | Still present | Still present | Moved to IdP | Removed for app login | Usually secondary only |
| User recovery | Harder. Needs backup or support | Familiar password reset | Familiar password reset | Delegated to IdP | Hard for unmanaged users | Easy but dangerous if primary |
| Latency | Fast for passkeys, slow for email | Fast after app setup | Slow and carrier dependent | Redirect dependent | Fast when cert works | Fast |
| Device dependency | Medium to high | Medium | Low to medium | Depends on IdP | High | Low |
| Operability | Complex telemetry needed | Mature playbooks | Carrier and SIM issues | IdP logs needed | Certificate lifecycle issues | Abuse monitoring needed |
| Cost | Platform work and recovery cost | Low app cost | SMS fees and fraud cost | IdP licensing | PKI and device management | Low direct cost |
| Team topology | Best with central identity team | Product teams can own it | Product teams can own it | IdP team owns policy | Infrastructure team owns PKI | Support owns recovery |
| Accessibility | Good with alternatives | Good | Good but phone-dependent | Depends on IdP | Poor for public users | Good |
| Assurance clarity | Precise if method typed | Often overestimated | Often overestimated | Depends on token claims | Precise in managed fleets | Poor as a primary method |

Reading of the table. Passwordless wins when the normal login path can use
origin-bound cryptography and recovery is strong. Password plus TOTP wins where
compatibility matters more than phishing resistance. OIDC or SAML wins when an
identity provider can own the authenticator policy. Client certificates win in
managed fleets. Recovery codes should remain recovery, not a primary login
experience.

## 13. Related and incompatible patterns

- **Passkeys and WebAuthn.** The main implementation pattern for public web
  passwordless. Passwordless is the product-level goal. WebAuthn is the browser
  and server protocol shape for the strongest common web variant.
- **Session Management.** Always composes. Passwordless proves the claimant at
  one ceremony. Session Management governs what happens after that proof.
- **Token-Based Authentication.** Composes after verification. A successful
  passwordless event may mint a session cookie, access token, refresh token, or
  identity token.
- **OpenID Connect.** Replaces local passwordless verification when an external
  provider owns login. The relying party receives an ID Token rather than a raw
  WebAuthn assertion.
- **Zero Trust.** Composes at policy level. Passwordless can provide stronger
  user proof, while Zero Trust still evaluates device, network, resource, and
  action risk.
- **Secure By Default.** Composes during enrollment. The default should steer
  users toward phishing-resistant methods and multiple authenticators.
- **Account Recovery.** Not optional. Recovery is a companion pattern and the
  most common place where passwordless designs lose their value.
- **Shared-secret login.** Replaced by this pattern in normal sign-in. Keeping a
  password as an always-available fallback weakens the security claim.
- **Knowledge-based authentication.** Actively conflicts. Security questions
  reintroduce guessable shared secrets and are a poor recovery proof.
- **Service Locator.** Conflicts in implementation. Authentication policy should
  be explicit and auditable, not hidden behind global lookups in product code.

## 14. Refactoring path in and out

Introducing the pattern into an existing password login.

1. Inventory login, password reset, MFA, session issuance, support recovery,
   account change, and admin impersonation paths. Passwordless only works when
   all entry points are visible.
2. Add an authentication-method table before changing UX. Store account ID,
   method type, credential ID or delivery target, public key where applicable,
   enrollment time, last-used time, friendly name, risk flags, and revocation
   time.
3. Add a challenge table or cache with nonce hash, purpose, expiry, account or
   identifier, client context, and consumed-at timestamp.
4. Introduce passwordless enrollment after an existing strong login. Start with
   passkeys for compatible browsers or magic links for a lower-risk population.
5. Add login with the new method while keeping password login. Mark the session
   with `auth_method`, `phishing_resistant`, `user_verified`, and
   `authenticated_at`.
6. Add step-up rules for sensitive actions. Do this before removing passwords,
   because it exposes weak method classification early.
7. Add recovery policy. Require at least two authenticators for high-value
   accounts, or pair one authenticator with a delayed recovery process.
8. Move password login behind risk policy. For example, allow it only for
   recovery, legacy clients, or accounts not yet enrolled.
9. Remove password storage only after migration metrics show enrollment,
   recovery success, support readiness, and fallback abuse under control.

Named refactorings from the refactoring family apply at implementation level.
Extract Function separates challenge issuance from controller code. Introduce
Parameter Object helps carry verifier inputs without long argument lists.
Replace Conditional with Polymorphism can separate passkey, magic-link, and
device-certificate verifier code. Move Method can place proof verification next
to credential binding records.

Removing the pattern when it stops earning its place.

1. Identify why it is being removed. Common reasons are unsupported clients,
   regulated users needing smart cards instead, or recovery cost exceeding risk
   reduction.
2. Freeze new enrollments for the method being removed, but keep existing
   credentials valid during transition.
3. Add an alternate method that meets the same or higher assurance need.
4. Require users to enroll the replacement before revoking the old method.
5. Revoke unused credentials and delete public keys or token hashes according
   to retention policy.
6. Keep historical login events for audit, but remove active challenge and
   credential binding data that no longer serves a security purpose.

## 15. Testing and verification

Engineering judgement. The techniques below are practice guidance for code
using this pattern.

Test the ceremony, not only the happy path. For passkeys, a verifier test suite
needs valid assertion acceptance, stale challenge rejection, wrong origin
rejection, wrong RP ID rejection, wrong credential ID rejection, bad signature
rejection, missing user verification rejection when policy requires it, and
replay rejection. WebAuthn Level 3 includes user agent automation and virtual
authenticator material, which can support browser-level tests
([https://www.w3.org/TR/webauthn-3/](https://www.w3.org/TR/webauthn-3/),
verified 2026-08-02).

For magic links, test token entropy, hash-at-rest, expiry, atomic single use,
uniform response for unknown accounts, scanner-safe confirmation, rate limits,
and session issuance only after token consumption. For email delivery, fake the
mailer in unit tests and run integration tests against a sandbox provider.

For recovery, run abuse tests. A good test asks whether an attacker with only
an email inbox, only a phone number, only an old session, or only support
conversation history can replace the authenticator. Recovery tests should cover
delayed activation, notification, revocation, and high-risk action blocks.

Test doubles that fit.

- **Virtual authenticator.** Browser automation creates and uses synthetic
  WebAuthn credentials without a physical key.
- **Fake challenge store.** A deterministic in-memory store can prove replay
  and expiry behavior.
- **Spy session issuer.** Tests assert session claims without sending cookies to
  a browser.
- **Fake mailer.** Tests inspect the link target and token metadata without
  sending mail.
- **Clock fake.** Expiry and delayed recovery require controlled time.

What became harder. End-to-end tests now depend on browser capability and
authenticator behavior. Production parity is difficult because real biometric
or platform approval state cannot be reproduced in CI. The practical answer is a
test pyramid. Keep most verifier rules in deterministic unit tests, add browser
tests with virtual authenticators, and reserve real-device smoke tests for
release qualification.

## 16. Observability signals

Engineering judgement. Observability should reveal method health, user impact,
and abuse without logging secrets.

Record these fields on every authentication event.

- Account ID or stable internal subject, never the raw email in high-volume
  logs when a surrogate exists.
- Method type, such as `passkey_synced`, `passkey_device_bound`,
  `magic_link`, `email_code`, `fido2_security_key`, or `idp_passwordless`.
- Challenge ID hash, purpose, issued time, consumed time, and rejection reason.
- Result, such as success, expired, replayed, wrong origin, bad signature,
  user_cancelled, unsupported_client, delivery_failed, or throttled.
- User verification requirement and observed state for passkey ceremonies.
- Credential ID hash and authenticator friendly name.
- Enrollment, revocation, and recovery events with actor and approval path.
- Session claims emitted after login, especially `auth_method`,
  `authenticated_at`, and step-up status.

Healthy dashboards show stable passkey enrollment, low recovery rate, low
cancel rate after users learn the prompt, near-zero replay, no wrong-origin
success, low mail delivery latency for link flows, and clear separation between
low-assurance and high-assurance sessions.

Failing dashboards show rising recovery requests after a device release, high
mail-link open rates with low session issuance, replay attempts after mail
scanner activity, passkey failures isolated to one browser version, many
unknown-account requests from one network, or high-risk actions occurring soon
after authenticator replacement.

Do not log raw magic links, one-time codes, WebAuthn client data JSON before
redaction, biometric state beyond the boolean needed for policy, full email
addresses in general logs, or private key material. A good production rule is
that an authentication log should allow replay analysis but never provide a
credential an attacker can redeem.

## 17. Security and privacy implications

Engineering judgement. This pattern closes some attack paths and opens others.

The main security gain is removal of reusable, centrally verified passwords from
normal login. A stolen password database no longer gives attackers hashes to
guess for those accounts, and credential stuffing loses its direct input. In
passkey variants, the public key stored by the server cannot be used to sign a
challenge. The authenticator signs a fresh challenge only after local user
action. NIST describes replay resistance as making recorded authentication
messages impractical to reuse, with nonces or challenges used to prove
freshness
([https://pages.nist.gov/800-63-4/sp800-63b.html](https://pages.nist.gov/800-63-4/sp800-63b.html),
verified 2026-08-02).

Phishing resistance depends on the variant. Properly configured passkeys bind
use to the relying party domain. Email links, SMS codes, and many push approval
flows are not equivalent. Treat "passwordless" as a UX category and
`phishing_resistant` as a security property derived from the specific
authenticator.

Privacy has three major concerns. First, biometric data should stay local to
the device. Google states that biometric data is not shared with Google or
third parties during Google Account passkey approval, and that the screen lock
opens the passkey locally
([https://security.googleblog.com/2023/05/so-long-passwords-thanks-for-all-phish.html](https://security.googleblog.com/2023/05/so-long-passwords-thanks-for-all-phish.html),
verified 2026-08-02). FIDO likewise states that biometric information remains
on the device and is not sent to the remote server
([https://fidoalliance.org/passkeys/](https://fidoalliance.org/passkeys/),
verified 2026-08-02). Second, attestation can reveal authenticator model or
vendor, so do not collect it unless policy needs device provenance. Third,
credential IDs, method names, and recovery events can reveal device ownership
or work role, so retain them under authentication-log policy rather than
general analytics policy.

The dangerous edge is recovery. An attacker who cannot phish a passkey may
still steal a mailbox, social-engineer support, compromise an old session, or
abuse a phone-number change. The recovery authority must have rate limits,
separation of duties for privileged users, notification to existing channels,
delayed activation for risky changes, and an audit trail.

Magic-link systems have special handling needs. Store only a hash of the token.
Use short expiry. Make token redemption atomic. Bind the token to purpose.
Avoid putting the token in logs, referrers, analytics, crash reports, or
customer support screenshots. Consider a two-step flow where the email link
opens a confirmation page and the session is issued only after a deliberate
browser action.

The pattern is silent on authorization. A passkey can prove that the user
controls an authenticator, but it does not answer which resources the user may
access, whether a transaction is allowed, or whether a privileged action needs
approval. Pair it with authorization policy and audit logging.

## 18. References

1. World Wide Web Consortium. *Web Authentication. An API for accessing Public
   Key Credentials. Level 3*. Candidate Recommendation Snapshot, 26 May 2026.
   Sections Abstract, 7.1, 7.2, 11, 13, and 14.
   [https://www.w3.org/TR/webauthn-3/](https://www.w3.org/TR/webauthn-3/).
   Verified 2026-08-02.
2. NIST. *Digital Identity Guidelines. Authentication and Authenticator
   Management*, Special Publication 800-63B, 2026 draft publication branch.
   Sections on authenticator types, phishing resistance, replay resistance,
   authentication intent, passwords, syncable authenticators, and AAL3.
   [https://pages.nist.gov/800-63-4/sp800-63b.html](https://pages.nist.gov/800-63-4/sp800-63b.html).
   Verified 2026-08-02.
3. FIDO Alliance. *FIDO Passkeys. Passwordless Authentication*.
   [https://fidoalliance.org/passkeys/](https://fidoalliance.org/passkeys/).
   Verified 2026-08-02.
4. GitHub. *Passkeys are Generally Available*, GitHub Changelog,
   September 21, 2023.
   [https://github.blog/changelog/2023-09-21-passkeys-are-generally-available/](https://github.blog/changelog/2023-09-21-passkeys-are-generally-available/).
   Verified 2026-08-02.
5. Google. *So long passwords, thanks for all the phish*, Google Online
   Security Blog, May 3, 2023.
   [https://security.googleblog.com/2023/05/so-long-passwords-thanks-for-all-phish.html](https://security.googleblog.com/2023/05/so-long-passwords-thanks-for-all-phish.html).
   Verified 2026-08-02.
6. Microsoft. *Authentication methods in Microsoft Entra ID. Passkeys
   (FIDO2)*, Microsoft Learn.
   [https://learn.microsoft.com/en-us/entra/identity/authentication/concept-authentication-passkeys-fido2](https://learn.microsoft.com/en-us/entra/identity/authentication/concept-authentication-passkeys-fido2).
   Verified 2026-08-02.
7. Apple. *iCloud Keychain security overview*, Apple Platform Security.
   [https://support.apple.com/guide/security/icloud-keychain-security-overview-sec1c89c6f3b/web](https://support.apple.com/guide/security/icloud-keychain-security-overview-sec1c89c6f3b/web).
   Verified 2026-08-02.
8. 1Password. *Passkeys in 1Password. The Future of Passwordless
   Authentication*.
   [https://1password.com/product/passkeys](https://1password.com/product/passkeys).
   Verified 2026-08-02.
9. OWASP Foundation. *Authentication Cheat Sheet*, OWASP Cheat Sheet Series.
   Sections Authentication Responses, Logging and Monitoring, and Use of
   authentication protocols that require no password.
   [https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html).
   Verified 2026-08-02.
10. Jim Schaad. *RFC 9052. CBOR Object Signing and Encryption (COSE).
    Structures and Process*, IETF, August 2022. Jim Schaad. *RFC 9053. CBOR
    Object Signing and Encryption (COSE). Initial Algorithms*, IETF,
    August 2022. Used for COSE lineage referenced by WebAuthn.
    [https://www.rfc-editor.org/rfc/rfc9052](https://www.rfc-editor.org/rfc/rfc9052)
    and
    [https://www.rfc-editor.org/rfc/rfc9053](https://www.rfc-editor.org/rfc/rfc9053).
    Verified 2026-08-02.

## Code examples

The examples are minimal and runnable. They demonstrate pattern mechanics, not
a replacement for a WebAuthn library. Production WebAuthn verification should
use a maintained library that handles CBOR, COSE keys, authenticator data,
origin rules, and browser edge cases.

### TypeScript

This sample models a passkey-like challenge and signature check using Node
Ed25519 keys. It is not a WebAuthn parser.

```typescript
const nodeCrypto = require("crypto");

type StoredCredential = {
  id: string;
  publicKey: any;
};

type Challenge = {
  id: string;
  accountId: string;
  nonce: any;
  expiresAt: number;
  used: boolean;
};

class PasswordlessVerifier {
  private credentials = new Map<string, StoredCredential>();
  private challenges = new Map<string, Challenge>();

  register(accountId: string, publicKey: any): StoredCredential {
    const credential = {
      id: nodeCrypto.randomBytes(12).toString("hex"),
      publicKey,
    };
    this.credentials.set(accountId, credential);
    return credential;
  }

  issueChallenge(accountId: string, now: number): Challenge {
    const challenge = {
      id: nodeCrypto.randomBytes(12).toString("hex"),
      accountId,
      nonce: nodeCrypto.randomBytes(32),
      expiresAt: now + 60_000,
      used: false,
    };
    this.challenges.set(challenge.id, challenge);
    return challenge;
  }

  verify(challengeId: string, signature: any, now: number): boolean {
    const challenge = this.challenges.get(challengeId);
    if (!challenge || challenge.used || challenge.expiresAt < now) return false;
    const credential = this.credentials.get(challenge.accountId);
    if (!credential) return false;
    const ok = nodeCrypto.verify(null, challenge.nonce, credential.publicKey, signature);
    if (ok) challenge.used = true;
    return ok;
  }
}

const { publicKey, privateKey } = nodeCrypto.generateKeyPairSync("ed25519");
const verifier = new PasswordlessVerifier();
verifier.register("acct_123", publicKey);
const challenge = verifier.issueChallenge("acct_123", Date.now());
const signature = nodeCrypto.sign(null, challenge.nonce, privateKey);
console.log(verifier.verify(challenge.id, signature, Date.now()));
console.log(verifier.verify(challenge.id, signature, Date.now()));
```

### Python

This sample models a magic-link flow. It stores a token hash and consumes the
token once.

```python
from dataclasses import dataclass
import hashlib
import hmac
import secrets
import time


@dataclass
class LinkRecord:
    account_id: str
    token_hash: str
    expires_at: float
    used: bool = False


class MagicLinkLogin:
    def __init__(self) -> None:
        self.links: dict[str, LinkRecord] = {}

    def issue(self, account_id: str, now: float) -> str:
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        self.links[token_hash] = LinkRecord(account_id, token_hash, now + 300)
        return token

    def consume(self, token: str, now: float) -> str | None:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        record = self.links.get(token_hash)
        if record is None or record.used or record.expires_at < now:
            return None
        if not hmac.compare_digest(record.token_hash, token_hash):
            return None
        record.used = True
        return record.account_id


login = MagicLinkLogin()
issued = login.issue("acct_123", time.time())
print(login.consume(issued, time.time()))
print(login.consume(issued, time.time()))
```

### Go

This sample uses Ed25519 from the Go standard library to model a device-bound
credential signing a server challenge.

```go
package main

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"time"
)

type Credential struct {
	AccountID string
	PublicKey ed25519.PublicKey
}

type Challenge struct {
	ID        string
	AccountID string
	Nonce     []byte
	ExpiresAt time.Time
	Used      bool
}

type Verifier struct {
	credentials map[string]Credential
	challenges  map[string]*Challenge
}

func NewVerifier() *Verifier {
	return &Verifier{
		credentials: map[string]Credential{},
		challenges:  map[string]*Challenge{},
	}
}

func randomHex(n int) string {
	buf := make([]byte, n)
	if _, err := rand.Read(buf); err != nil {
		panic(err)
	}
	return hex.EncodeToString(buf)
}

func (v *Verifier) Register(accountID string, publicKey ed25519.PublicKey) {
	v.credentials[accountID] = Credential{AccountID: accountID, PublicKey: publicKey}
}

func (v *Verifier) Issue(accountID string, now time.Time) *Challenge {
	nonce := make([]byte, 32)
	if _, err := rand.Read(nonce); err != nil {
		panic(err)
	}
	challenge := &Challenge{
		ID:        randomHex(12),
		AccountID: accountID,
		Nonce:     nonce,
		ExpiresAt: now.Add(time.Minute),
	}
	v.challenges[challenge.ID] = challenge
	return challenge
}

func (v *Verifier) Verify(id string, sig []byte, now time.Time) bool {
	challenge := v.challenges[id]
	if challenge == nil || challenge.Used || now.After(challenge.ExpiresAt) {
		return false
	}
	credential, ok := v.credentials[challenge.AccountID]
	if !ok {
		return false
	}
	if !ed25519.Verify(credential.PublicKey, challenge.Nonce, sig) {
		return false
	}
	challenge.Used = true
	return true
}

func main() {
	publicKey, privateKey, _ := ed25519.GenerateKey(rand.Reader)
	verifier := NewVerifier()
	verifier.Register("acct_123", publicKey)
	challenge := verifier.Issue("acct_123", time.Now())
	signature := ed25519.Sign(privateKey, challenge.Nonce)
	fmt.Println(verifier.Verify(challenge.ID, signature, time.Now()))
	fmt.Println(verifier.Verify(challenge.ID, signature, time.Now()))
}
```
