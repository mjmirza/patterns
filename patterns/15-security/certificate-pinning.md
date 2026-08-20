---
name: Certificate Pinning
slug: certificate-pinning
family: 15-security
category: Transport Security
aliases: [Public Key Pinning, SPKI Pinning, Key Pinning, Trust Pinning]
first_described: "Evans, Palmer, Sleevi 2015"
maturity: established
related: [mutual-tls, certificate-transparency, key-rotation, trust-on-first-use]
incompatible_with: [transparent-tls-interception, unconstrained-ca-agility]
verified: 2026-08-02
---

# Certificate Pinning

## 1. Name, aliases, and lineage

The canonical name is Certificate Pinning. In current security engineering
usage the more precise name is often Public Key Pinning or SPKI Pinning,
because the safer production form pins the hash of a certificate chain member's
Subject Public Key Info rather than the entire leaf certificate. Android's
Network Security Configuration describes pinning as a domain rule where a
certificate chain is valid only when the chain contains at least one configured
public key hash, using the X.509 `SubjectPublicKeyInfo` value
([Android Network Security Configuration](https://developer.android.com/privacy-and-security/security-config),
verified 2026-08-02). RFC 7469, *Public Key Pinning Extension for HTTP*, was
published by Chris Evans, Chris Palmer and Ryan Sleevi in April 2015 and
specified the `Public-Key-Pins` HTTP response header for user agents
([RFC 7469](https://datatracker.ietf.org/doc/html/rfc7469), verified
2026-08-02).

The lineage has two branches that should not be merged in a design review.

- **Application certificate pinning.** A native, mobile, desktop, command line,
  agent, or embedded client carries a pinset in code, configuration, policy, or
  a signed update bundle. After normal TLS certificate path validation, the
  client compares the presented chain against that pinset. This entry is mainly
  about this form.
- **HTTP Public Key Pinning, HPKP.** A web server sent a `Public-Key-Pins`
  response header and the browser stored pins for later visits. RFC 7469
  defined that mechanism, including `pin-sha256`, `max-age`,
  `includeSubDomains`, `report-uri`, backup pins, and a report-only mode
  ([RFC 7469](https://datatracker.ietf.org/doc/html/rfc7469), verified
  2026-08-02). Browser HPKP is now treated as a bad deployment target. MDN
  marks the `Public-Key-Pins` header as deprecated
  ([Wikipedia, HTTP Public Key Pinning](https://en.wikipedia.org/wiki/HTTP_Public_Key_Pinning),
  verified 2026-08-20). Cloudflare says it does not support HPKP for its
  managed certificate products and recommends Certificate Transparency
  monitoring instead
  ([Cloudflare certificate pinning](https://developers.cloudflare.com/ssl/reference/certificate-pinning/),
  verified 2026-08-02).

The pattern is therefore established but narrowed. It remains a live pattern
for clients whose operator controls both the software update path and the TLS
identity lifecycle. It is no longer a good default for public websites using
browser HPKP.

## 2. Problem and context

TLS authenticates a server by building and validating a certificate chain from
the server's leaf certificate to a trusted root. For public HTTPS, a large set
of public certificate authorities can issue for a domain. Android explains the
risk in app terms: if any trusted CA issues a fraudulent certificate for the
app's server, an on-path attacker can present a chain that the platform would
otherwise accept
([Android security with network protocols](https://developer.android.com/privacy-and-security/security-ssl?authuser=2&hl=en),
verified 2026-08-02).

The codebase symptom is concrete. A client calls a high-value API over HTTPS.
The platform trust store says the chain is valid. The hostname matches. The
TLS version and cipher suite meet policy. Yet the product owner still does not
want any public CA, any enterprise-added root, or any local debugging proxy to
stand in for that API. The client is not trying to discover a new service. It
already knows which service it means to call. Certificate Pinning records a
small set of acceptable cryptographic identities for that service and rejects
otherwise valid TLS connections when the presented chain does not contain one
of those identities.

The pattern belongs in a narrow context.

- The client talks to a small set of known hosts.
- The team can ship client updates before old pins expire or old keys are
  retired.
- The server team can publish a future key before it is needed, or can keep a
  stable intermediate or backup key under control.
- The organization accepts that an error in the pinset can create a client-side
  outage that no server-side hotfix can repair.

Outside that context, the pattern often moves risk rather than reducing it.
Microsoft warns that pinning can create unacceptable certificate agility costs,
and that HPKP is deprecated
([Microsoft certificate pinning](https://learn.microsoft.com/en-us/azure/security/fundamentals/certificate-pinning),
verified 2026-08-02).

## 3. Forces

Judgement. This section weighs engineering pressures. The cited sources define
mechanics and platform behavior, while the force ranking is design judgement.

- **Authentication strength.** Favoured. A valid but unexpected CA chain is no
  longer enough. The chain must also contain a known public key or certificate.
- **Availability.** Sacrificed. A stale or incomplete pinset can deny every
  client even when the server is reachable and serving a CA-valid certificate.
  RFC 7469 warns that incorrect pinning can make a host unavailable
  ([RFC 7469](https://datatracker.ietf.org/doc/html/rfc7469), verified
  2026-08-02).
- **Certificate agility.** Sacrificed. CA migration, emergency revocation,
  certificate replacement, CDN migration, and disaster recovery all need pin
  planning.
- **Latency.** Near neutral. The pin check is a hash comparison after TLS chain
  building. The latency cost is small compared with the handshake. The failure
  path may be expensive because retries cannot repair a wrong identity.
- **Coupling.** Sacrificed. The client release train is coupled to the server
  certificate plan. That coupling is the point of the pattern, but it is still
  coupling.
- **Consistency.** Favoured. Every pinned client applies the same narrower
  trust rule for the target host, independent of local CA store changes unless
  the platform bypasses pins for a configured trust anchor.
- **Operability.** Sacrificed unless designed in. Operators need dashboards for
  pin failures, pinset versions, certificate chain fingerprints, expiration
  windows, and client app versions.
- **Team topology.** Mixed. Pinning helps when one team owns both the client
  and the service. It hurts when mobile, server, security, CDN, and vendor teams
  rotate certificates without a shared calendar.
- **Cognitive load.** Sacrificed. A developer must understand TLS path
  validation, hostname validation, public key extraction, hash format, backup
  pins, remote kill switches, and release lead time.
- **Privacy.** Mixed. Local interception tools lose visibility, which can
  protect users. Report-only mechanisms and failure telemetry can leak host and
  certificate details if logged carelessly. RFC 7469 has a privacy section for
  HPKP reports and pin state
  ([RFC 7469](https://datatracker.ietf.org/doc/html/rfc7469), verified
  2026-08-02).

Certificate Pinning favours narrow authentication over agility. Treat any
proposal that claims both as unfinished.

## 4. Applicability and non-applicability

Reach for Certificate Pinning when the following hold.

- A distributed client calls a small number of high-value, stable domains and
  the team controls the client release channel.
- The attacker model includes fraudulent public CA issuance, a locally
  installed user CA, hostile Wi-Fi interception, or enterprise TLS interception
  that the product is meant to resist.
- The service has a documented certificate rotation calendar, with backup keys
  generated and stored before they are required.
- The client can carry at least two valid pins per host, one active and one
  backup. Android tells app authors to include a backup key for forced key or
  CA changes
  ([Android Network Security Configuration](https://developer.android.com/privacy-and-security/security-config),
  verified 2026-08-02).
- The client has observable pin failure telemetry that is safe enough to send
  after a failed handshake through a separate path, or can be diagnosed during
  controlled rollout.
- The product can tolerate break-glass behavior such as a signed remote pinset,
  a short pin expiration, or a kill switch that disables pins only after strict
  authenticity checks.
- The host identity is part of the application trust model, such as a banking
  API, messaging service endpoint, device management server, software update
  service, or payment gateway.

Do NOT reach for Certificate Pinning in these cases.

- **Public websites served to browsers.** Browser HPKP is deprecated. Use HSTS,
  Certificate Transparency monitoring, CAA, ACME hygiene, and incident response
  instead. Cloudflare explicitly points site operators toward CT monitoring for
  the misissuance problem
  ([Cloudflare certificate pinning](https://developers.cloudflare.com/ssl/reference/certificate-pinning/),
  verified 2026-08-02).
- **Services whose certificates are managed by a third party without contract
  control.** If a CDN, SaaS vendor, payment processor, or enterprise gateway can
  rotate keys without notice, client pins will fail during a normal vendor
  operation.
- **Long-lived clients that are hard to update.** Devices in the field,
  abandoned mobile installs, appliance firmware, and air-gapped clients often
  cannot refresh pinsets before key changes. Android supports pin expiration to
  reduce old-client connectivity failures, while warning that expiration may
  let attackers bypass pins after the date
  ([Android Network Security Configuration](https://developer.android.com/privacy-and-security/security-config),
  verified 2026-08-02).
- **Teams without certificate ownership.** If security owns pins, platform owns
  mobile releases, infrastructure owns certificates, and no one owns the shared
  change process, the pattern is an outage multiplier.
- **General API clients and SDKs.** A library that pins on behalf of all
  applications takes away the host owner's certificate agility. Prefer a hook
  that lets the application supply a pin policy.
- **Environments that require lawful or administrative TLS inspection.**
  Pinning conflicts with transparent interception by design. Chrome's security
  FAQ describes that Chrome key pinning is not applied when a chain terminates
  at a private trust anchor, allowing managed interception in that model
  ([Chromium Security FAQ](https://chromium.googlesource.com/chromium/src/+/HEAD/docs/security/faq.md),
  verified 2026-08-02).
- **Self-signed certificate shortcuts.** Pinning is not a replacement for trust
  evaluation. OkHttp documents that its `CertificatePinner` cannot pin a
  self-signed certificate that the `TrustManager` does not already accept
  ([OkHttp CertificatePinner 3.0.0 API](https://javadoc.io/static/com.squareup.okhttp3/okhttp/3.0.0/okhttp3/CertificatePinner.html),
  verified 2026-08-02).
- **Pinning to volatile leaf certificates without automation.** Leaf
  certificates expire and are often renewed with new keys. SPKI or intermediate
  pins usually age better, but they still need rotation discipline.
- **First-connection discovery.** Trust on first use cannot stop a first
  connection attacker. RFC 7469 states that HPKP cannot detect a man in the
  middle on the first connection because the client lacks pin data then
  ([RFC 7469](https://datatracker.ietf.org/doc/html/rfc7469), verified
  2026-08-02).

## 5. Structure

The pattern has seven participants.

- **Pinned Host.** The DNS name or service identity whose TLS chain must match a
  narrowed identity set. The host is the lookup key for the pin policy.
- **Pinset.** The allowed cryptographic identities for that host. A production
  pinset contains at least one active pin and at least one backup pin, and may
  contain an expiration date, a version, and a policy mode.
- **Pin Material.** The exact bytes to compare. In current practice this is
  commonly the SHA-256 hash of `SubjectPublicKeyInfo` from a chain certificate.
  RFC 7469 used base64-encoded SHA-256 SPKI fingerprints for `pin-sha256`
  ([RFC 7469](https://datatracker.ietf.org/doc/html/rfc7469), verified
  2026-08-02).
- **Trust Evaluator.** The platform or library component that performs normal
  TLS path validation and hostname validation before the pin check. Pinning
  narrows trust after this step. It must not replace this step.
- **Pin Verifier.** The code that extracts comparable material from the peer
  chain, finds the host's pinset, compares pins in constant-shape code, and
  returns allow or deny.
- **Update Channel.** The app release, signed configuration, mobile device
  management policy, or other authenticated path that distributes new pinsets.
- **Operator Feedback Loop.** Logging, metrics, synthetic probes, crash
  reports, rollout dashboards, and alerts that tell the team when a pin is
  stale, missing, or blocking real users.

The relationship is sequential. The client first asks the Trust Evaluator
whether TLS is valid. Only after that succeeds does the Pin Verifier narrow the
accepted identities for selected hosts. The Update Channel changes the pinset,
not the peer chain. The Feedback Loop watches both allowed and denied outcomes.

## 6. ASCII structure diagram

```text
  +-------------------+        HTTPS        +----------------------+
  | Pinned Client     | ------------------> | Pinned Host          |
  |-------------------|                     |----------------------|
  | host policy map   | <------------------ | certificate chain    |
  | pin verifier      |       chain         | active public key    |
  +---------+---------+                     +----------+-----------+
            |                                          ^
            | uses                                     |
            v                                          |
  +-------------------+        validates      +---------+-----------+
  | Trust Evaluator   | -------------------> | Public or private   |
  |-------------------|                      | trust anchors       |
  | path validation   |                      +---------------------+
  | hostname check    |
  +---------+---------+
            |
            | if normal TLS trust passes
            v
  +-------------------+       reads          +---------------------+
  | Pin Verifier      | ------------------> | Pinset              |
  |-------------------|                     |---------------------|
  | extract SPKI      |                     | host -> pins        |
  | hash and compare  |                     | active, backup      |
  +---------+---------+                     | expiry, version     |
            |                               +----------+----------+
            | emits                                    ^
            v                                          |
  +-------------------+       updates        +----------+----------+
  | Feedback Loop     | <------------------ | Update Channel      |
  |-------------------|                     |---------------------|
  | metrics, logs     |                     | signed app release  |
  | alerts, probes    |                     | or signed config    |
  +-------------------+                     +---------------------+
```

## 7. Dynamics

At runtime, a pin check is a second authorization decision over a TLS chain that
already passed normal validation. It should not run before hostname validation,
because a pin collision across two hosts in the same app would be easier to
hide if the host name was never bound to the peer.

```text
Client             TLS stack          Trust evaluator      Pin verifier
  |                    |                     |                   |
  | connect host       |                     |                   |
  |------------------->|                     |                   |
  |                    | receive chain       |                   |
  |                    |-------------------->|                   |
  |                    |                     | validate path     |
  |                    |                     | validate hostname |
  |                    |                     |------------------>| no
  |                    |                     |<------------------| pins yet
  |                    |<--------------------| trust ok          |
  |                    |                     |                   |
  | peer chain         |                     |                   |
  |------------------------------------------------------------->|
  |                    |                     |                   |
  |                    |                     |     find pinset   |
  |                    |                     |     extract SPKI  |
  |                    |                     |     SHA-256 hash  |
  |                    |                     |     compare set   |
  |                    |                     |                   |
  | allow request      |<-----------------------------------------| match
  |------------------->|                     |                   |
  |                    |                     |                   |
  | cancel request     |<-----------------------------------------| no match
  | emit safe signal   |                     |                   |
```

The denial path should be final for that connection. Retrying the same host
with the same pinset cannot repair a mismatch. A retry loop that repeats a pin
failure turns an identity error into a battery, bandwidth, and rate-limit
problem.

For HPKP, the dynamics were different. The server transmitted a pin policy in a
response header, and the user agent remembered it for later requests. RFC 7469
therefore had to define storage, expiry, report-only behavior, and hostile
pinning cases
([RFC 7469](https://datatracker.ietf.org/doc/html/rfc7469), verified
2026-08-02). Application pinning often moves those concerns into release
engineering and signed configuration.

## 8. Implementation variants

**SPKI hash pinning.** Hash the DER bytes of `SubjectPublicKeyInfo` for one or
more certificates in the peer chain and compare the base64 SHA-256 result with
the pinset. This is the common app form because a certificate can be reissued
with different validity dates and extensions while the key remains the same.
Android and RFC 7469 both describe SPKI-style public key pinning
([Android Network Security Configuration](https://developer.android.com/privacy-and-security/security-config),
verified 2026-08-02; [RFC 7469](https://datatracker.ietf.org/doc/html/rfc7469),
verified 2026-08-02).

**Leaf certificate pinning.** Store a hash of the full leaf certificate. This
is easy to reason about and catches any leaf replacement, but it is brittle
during ordinary renewal. Use it only when the certificate lifecycle is slow,
manual, and fully owned by the same group that ships the client.

**Intermediate or CA pinning.** Pin an issuing intermediate or private root
rather than the leaf. This allows leaf rotation under the same issuer but still
narrows the trust universe. The cost is broader acceptance: any certificate for
the host issued under that pinned authority can pass if normal hostname
validation also passes.

**Declarative platform pinning.** Android Network Security Configuration lets
an app express pinsets in XML, with optional expiration and debug behavior
([Android Network Security Configuration](https://developer.android.com/privacy-and-security/security-config),
verified 2026-08-02). This reduces code risk and centralizes policy, but it is
platform-specific.

**Manual challenge handling.** Apple documents manual server trust
authentication through an `NSURLSessionDelegate` challenge handler, including
the case where an app pins itself to specific keys or certificates under its
control
([Apple manual server trust authentication](https://developer.apple.com/documentation/foundation/performing-manual-server-trust-authentication?changes=l_9&language=objc),
verified 2026-08-02). This gives fine control but places more responsibility on
application code.

**Library-managed pinning.** OkHttp exposes `CertificatePinner`, and its API
documentation says pinning is per hostname or wildcard pattern and runs against
peer certificates
([OkHttp CertificatePinner 3.0.0 API](https://javadoc.io/static/com.squareup.okhttp3/okhttp/3.0.0/okhttp3/CertificatePinner.html),
verified 2026-08-02). This is often the right level for JVM and Android
clients already using OkHttp.

**Signed remote pinset.** The app ships with a bootstrap pinset and accepts a
new pinset only when it is signed by a trusted offline key. This variant reduces
app-store release pressure. Judgement. It also creates a new root of trust and
needs replay protection, version monotonicity, audit logs, and a tested
break-glass plan.

**Trust on first use.** The client stores the first seen key and rejects later
changes. RFC 7469 describes HPKP as a TOFU mechanism for first dynamic pin
storage and states that the first connection cannot be protected by pins
([RFC 7469](https://datatracker.ietf.org/doc/html/rfc7469), verified
2026-08-02). TOFU fits private tools better than hostile public networks.

Minimal runnable examples follow. They model the pin decision, not the full TLS
stack.

TypeScript:

```typescript
type PinDecision = "allow" | "deny";

function verifyPin(host: string, presentedPins: string[],
  policy: Record<string, string[]>): PinDecision {
  const allowed = policy[host] ?? [];
  if (allowed.length === 0) return "allow";
  return presentedPins.some((pin) => allowed.includes(pin)) ? "allow" : "deny";
}

const policy = {
  "api.example.com": [
    "sha256/active-public-key",
    "sha256/backup-public-key",
  ],
};

console.log(verifyPin("api.example.com", ["sha256/backup-public-key"], policy));
console.log(verifyPin("api.example.com", ["sha256/unknown"], policy));
```

Python:

```python
import base64
import hashlib


def spki_pin(spki_der: bytes) -> str:
    digest = hashlib.sha256(spki_der).digest()
    return "sha256/" + base64.b64encode(digest).decode("ascii")


def verify_pin(host: str, chain_spki: list[bytes],
               policy: dict[str, set[str]]) -> bool:
    allowed = policy.get(host)
    if not allowed:
        return True
    presented = {spki_pin(value) for value in chain_spki}
    return not allowed.isdisjoint(presented)


active = b"demo active subject public key info"
backup = b"demo backup subject public key info"
policy = {"api.example.com": {spki_pin(active), spki_pin(backup)}}

print(verify_pin("api.example.com", [active], policy))
print(verify_pin("api.example.com", [b"attacker key"], policy))
```

Go:

```go
package main

import (
	"crypto/sha256"
	"encoding/base64"
	"fmt"
)

func pin(spki []byte) string {
	sum := sha256.Sum256(spki)
	return "sha256/" + base64.StdEncoding.EncodeToString(sum[:])
}

func verify(host string, chain [][]byte, policy map[string]map[string]bool) bool {
	allowed, ok := policy[host]
	if !ok {
		return true
	}
	for _, spki := range chain {
		if allowed[pin(spki)] {
			return true
		}
	}
	return false
}

func main() {
	active := []byte("demo active subject public key info")
	backup := []byte("demo backup subject public key info")
	policy := map[string]map[string]bool{
		"api.example.com": {pin(active): true, pin(backup): true},
	}
	fmt.Println(verify("api.example.com", [][]byte{active}, policy))
	fmt.Println(verify("api.example.com", [][]byte{[]byte("attacker")}, policy))
}
```

## 9. Known production uses

**Chrome key pinning.** Chrome has shipped key pinning in Chrome-branded
non-iOS builds under conditions described by the Chromium Security FAQ. The FAQ
says Chrome key pinning requires a valid chain and at least one known public
key in the chain, and it describes private trust anchor behavior and a test
site for pinning errors
([Chromium Security FAQ](https://chromium.googlesource.com/chromium/src/+/HEAD/docs/security/faq.md),
verified 2026-08-02). Chrome's modern public-web strategy has shifted toward
Certificate Transparency, with Chrome requiring publicly trusted TLS
certificates issued after April 30, 2018 to be CT-compliant
([Certificate Transparency in Chrome](https://googlechrome.github.io/CertificateTransparency/),
verified 2026-08-02).

**Android Network Security Configuration.** Android applications can declare
certificate pins for domains in `res/xml/network_security_config.xml`. The
Android documentation gives the pin format, the `pin-set` element, expiration,
backup key guidance, and debug override behavior
([Android Network Security Configuration](https://developer.android.com/privacy-and-security/security-config),
verified 2026-08-02). This is a platform-level production facility used by
Android apps rather than a research prototype.

**OkHttp `CertificatePinner`.** OkHttp is a production HTTP client for JVM and
Android clients. Its README lists certificate pinning among the TLS features it
supports
([OkHttp README](https://github.com/square/okhttp/blob/master/README.md),
verified 2026-08-02). The `CertificatePinner` API documentation describes host
and wildcard pinning, setup through observed peer-chain hashes, and warnings
about operational complexity
([OkHttp CertificatePinner 3.0.0 API](https://javadoc.io/static/com.squareup.okhttp3/okhttp/3.0.0/okhttp3/CertificatePinner.html),
verified 2026-08-02).

**Windows Enterprise Certificate Pinning.** Windows includes Enterprise
Certificate Pinning for Windows 10 and Windows 11. Microsoft describes it as a
feature for pinning a domain name to a root issuing CA or end-entity
certificate, with Windows certificate APIs checking whether a site's chain
matches configured pin rules
([Microsoft Windows enterprise certificate pinning](https://learn.microsoft.com/en-us/windows/security/identity-protection/enterprise-certificate-pinning),
verified 2026-08-02).

These production uses differ in control model. Chrome used browser-managed
pinning with auto-update assumptions. Android and OkHttp give application
developers a pinning tool. Windows gives enterprises a policy mechanism.

## 10. Consequences

Judgement. Consequences depend on update cadence, certificate ownership, and
failure telemetry.

Positive consequences:

- The client no longer trusts every public CA equally for the pinned host.
- User-added or attacker-added local roots can be blocked in clients that apply
  pins even when the normal trust store would accept the chain.
- A compromised or mistaken CA issuance is less useful unless the attacker can
  also present a chain containing a pinned key.
- A narrow host trust policy becomes reviewable as code or signed
  configuration.
- Pin failure telemetry can expose unexpected certificate changes before they
  become silent data exposure.
- Backup pins can turn key rotation into a planned client and server migration
  rather than a scramble after a revocation event.

Negative consequences:

- A bad pinset can create a total client outage for the pinned host.
- Certificate operations become cross-team work. Release, mobile, backend, CDN,
  security, and customer support need the same schedule.
- Emergency CA changes become harder. CA/B Forum and platform changes may
  require fast certificate replacement, while pinned clients may lag.
- Debugging gets harder. Local proxies, traffic capture tools, and enterprise
  security appliances may fail unless explicitly bypassed in debug builds.
- Pin state can become a privacy concern if reports contain hostnames,
  certificate details, account identifiers, or stable client IDs.
- Remote pin update systems add another trust root. If that signing key is
  compromised, an attacker may be able to publish a malicious pinset.
- The pattern can hide a deeper certificate hygiene issue. CT monitoring, CAA,
  revocation drills, and inventory still matter.

## 11. Failure modes and misuse

Judgement. The triples below are production-oriented diagnostics.

| Symptom | Cause | Fix |
|---|---|---|
| All clients on a new app version fail to connect immediately after launch. | The shipped pinset omitted the active production key or used a hash of the wrong certificate bytes. | Roll back the app if possible, publish a fixed app build, and add a pre-release test that extracts pins from the live chain and compares them with the release artifact. |
| Only old app versions fail after certificate renewal. | The server rotated to a key that was not present as a backup pin in those old clients. | Restore a chain containing an old pinned key if that is still safe, then publish a client with active and future pins. |
| Failures appear only behind a corporate proxy. | The proxy terminates TLS with a private CA that normal platform trust accepts, while the pin check rejects the substituted chain. | Decide whether the product supports interception. If yes, design an explicit enterprise policy. If no, return a clear identity error and document the conflict. |
| Debug builds fail when using Charles, Fiddler, mitmproxy, or an internal CA. | Debug trust anchors do not bypass or replace the production pin policy. | Use platform debug overrides or a separate debug pinset that cannot ship in release builds. Android documents debug overrides whose trust anchors can bypass pinning in debug mode. |
| Pin failures spike in one geography or ISP. | A CDN edge, regional certificate, or traffic management layer serves a different chain from the one tested in the primary region. | Probe every serving path, collect chain fingerprints by region, and pin a stable SPKI that appears on all valid chains. |
| Hostname validation errors are reported as pin errors. | The application collapsed all TLS failures into one exception or ran custom pinning before normal trust evaluation. | Preserve error categories. Run platform trust and hostname checks first, then pin checks. |
| A self-signed test server still fails after adding its pin. | The TLS trust manager rejects the chain before the pin verifier runs. | Add a test-only trust anchor, or run a local CA for test. Do not treat pinning as a replacement for trust validation. |
| Users cannot recover until they update the app. | The pinset has no expiration, no signed remote update, and no backup key. | Add a future-key process, a short enough pin lifetime for the product, and a signed recovery channel. |
| Logs contain full certificates, account IDs, or long-lived device IDs on failure. | The feedback path was written for debugging rather than privacy. | Log host, app version, pinset version, failure class, and short chain fingerprints. Avoid raw certificates and user identifiers unless a separate privacy review approves them. |
| The app accepts an attacker chain after a remote config change. | The remote pinset channel was not signed or did not reject replayed old policy. | Sign pinsets offline, include monotonically increasing versions, bind policy to hostnames, and audit every published policy. |

Misuse patterns:

- Pinning without backup pins. This converts every unplanned key change into a
  client outage.
- Pinning a third-party SaaS domain without a contractual certificate policy.
  The vendor will rotate on its schedule.
- Pinning as a substitute for TLS validation. The correct order is normal trust
  and hostname validation, then pin narrowing.
- Copying pins from a failure message on an untrusted network. OkHttp's setup
  guidance says to do that only on a trusted network and without interception
  tools
  ([OkHttp CertificatePinner 3.0.0 API](https://javadoc.io/static/com.squareup.okhttp3/okhttp/3.0.0/okhttp3/CertificatePinner.html),
  verified 2026-08-02).
- Shipping release builds with debug bypasses. Debug CA behavior must be tied
  to build system flags or app store debuggable controls, not runtime user
  preferences.

## 12. Trade-off matrix

Judgement. The table compares named trust-hardening alternatives against the
forces from dimension 3.

| Option | Authentication strength | Availability risk | Certificate agility | Operability | Best fit |
|---|---|---|---|---|---|
| Certificate Pinning | High for known clients and hosts. | High when pins are stale. | Low unless rotation is planned. | Hard without telemetry. | Owned apps calling owned high-value APIs. |
| Certificate Transparency Monitoring | Detects misissuance rather than blocking each client. | Low, because client connections continue. | High. | Moderate, alert quality matters. | Public websites and domains using public CAs. |
| HSTS | Forces HTTPS after policy is learned or preloaded. | Moderate if deployed with bad subdomain policy. | High for certificate changes. | Moderate. | Browser-facing sites that must prevent downgrade to HTTP. |
| CAA DNS Records | Narrows which CAs should issue for a domain. | Low to moderate. Misconfiguration can block issuance. | Moderate. CA changes need DNS changes. | Moderate. | Domains that want issuance policy at CA validation time. |
| Mutual TLS | Authenticates both parties with certificates. | Moderate to high due to client certificate lifecycle. | Moderate. | Hard at large client counts. | Service-to-service or managed device fleets. |
| Private PKI Trust Anchors | Narrows trust to an organization CA. | Moderate. Root rollover is hard. | Moderate inside one organization. | Moderate to hard. | Internal systems and managed endpoints. |
| Trust On First Use | Protects only after first clean contact. | Moderate. Key changes look like attacks. | Low unless reset UX exists. | Simple for small tools. | Developer tools, SSH-style workflows, private utilities. |

Certificate Pinning blocks some attacks that CT monitoring only detects, but
CT monitoring keeps the public web more agile. The better choice depends on
whether the client operator can ship policy changes fast enough to keep pins
fresh.

## 13. Related and incompatible patterns

**Mutual TLS** composes with Certificate Pinning when a managed client must
authenticate to a service and also restrict which server identity it accepts.
The two patterns solve opposite sides of the TLS authentication exchange.

**Certificate Transparency** is often the replacement for HPKP on public
websites. Chrome documents CT as a protocol for logging certificates in a
public append-only structure so site operators and the community can detect
unauthorized issuance
([Certificate Transparency in Chrome](https://googlechrome.github.io/CertificateTransparency/),
verified 2026-08-02).

**Key Rotation** is a required companion. A pinset without a rotation procedure
is a delayed outage. Backup pins, overlapping deployments, staged rollout, and
certificate inventory all belong in the same plan.

**Trust On First Use** is a weaker cousin. It records the first observed
identity instead of shipping an out-of-band identity. It can be useful for
private tools, but it is weak against a first-contact attacker.

**Defense in Depth** frames the pattern correctly. Pinning should sit beside
TLS validation, CT monitoring, CAA, HSTS where browsers are involved, secure
release signing, and incident response. It should not be the only control.

**Feature Flags** can compose only if the flag state is authenticated and
fail-closed enough for the risk model. A plain remote config flag that disables
pins over the same pinned channel can fail during the incident it is meant to
repair. A plain remote config flag over an unpinned channel can become a bypass.

**Transparent TLS Interception** conflicts with Certificate Pinning unless the
client has an explicit enterprise mode. That conflict is intentional. A pinned
client says a locally trusted intermediary is not the intended peer.

**Unconstrained CA Agility** conflicts with the pattern. If the server team
must be able to change CA, intermediate, and key at any moment without client
coordination, pinning is the wrong control.

## 14. Refactoring path in and out

Judgement. Introduce pinning with the smallest blast radius first.

Path in:

1. Inventory every hostname the client contacts. Separate owned hosts,
   third-party hosts, CDN vanity domains, telemetry endpoints, and emergency
   update endpoints.
2. Define the attacker model for each host. Pin only hosts where narrower trust
   changes a real decision.
3. Extract the live certificate chains from all production regions, staging,
   canary, and disaster recovery paths. Store SPKI hashes and certificate
   metadata in a reviewable artifact.
4. Pick pin granularity. Prefer SPKI pins for keys under your control. Use
   intermediate pins only when leaf agility matters and the issuer boundary is
   acceptable.
5. Generate at least one offline backup key and add its SPKI hash to the
   pinset before it is served.
6. Add the Pin Verifier after existing TLS trust and hostname validation. Do
   not replace platform validation code.
7. Add a report-only or shadow mode where the client records would-block
   decisions while still allowing the connection. HPKP had a report-only header
   for this kind of dry run
   ([RFC 7469](https://datatracker.ietf.org/doc/html/rfc7469), verified
   2026-08-02).
8. Roll out by channel and version. Watch pin failures by app version, host,
   region, pinset version, and certificate chain fingerprint.
9. Turn on enforcement for a small population, then expand only after a full
   certificate renewal rehearsal passes.
10. Write a rotation runbook. It should cover normal renewal, CA migration,
    emergency revocation, lost private key, CDN change, and app-store delay.

Path out:

1. Decide why pinning no longer earns its cost. Common reasons are third-party
   certificate control, app update lag, CT monitoring maturity, or support for
   enterprise inspection.
2. Ship a client version that accepts both pinned and unpinned valid TLS, while
   still logging pin matches and mismatches.
3. Let that version age until the vast majority of active clients have it.
4. Remove server or remote configuration assumptions that require old pins.
5. Delete pin policy from code and tests after the oldest supported client
   release no longer enforces it.
6. Keep CT monitoring, CAA, inventory, and certificate rotation tests in place.

Related refactorings from the refactoring family include Extract Function for
the pin comparison, Replace Conditional with Polymorphism when multiple host
policies have different behavior, and Encapsulate Record for pinset metadata.
Do not use these as ceremony. Use them when the pinning code begins to mix TLS
validation, policy lookup, telemetry, and update parsing in one function.

## 15. Testing and verification

Judgement. Pinning tests must cover identity, rollout, and operability rather
than only code branches.

Unit tests should cover:

- No policy for host returns allow after normal TLS succeeds.
- Empty pinset behavior is explicit and reviewed.
- Active pin match returns allow.
- Backup pin match returns allow.
- Unknown pin returns deny.
- Hostname lookup is exact where expected and wildcard behavior matches the
  chosen library or platform.
- Expired pins behave according to policy.
- Malformed pins fail closed during build or startup, not mid-request.
- Remote pinset signatures reject tampering, replay, host mismatch, and
  version rollback.

Integration tests should use a local TLS server with two or more generated
certificates. The test should prove that normal platform trust succeeds for
both chains, then the pin verifier accepts one chain and rejects the other. For
Android, include a resource test that parses the XML and verifies active and
backup pins exist for every pinned domain. For Apple clients, test that the
server trust challenge path only handles `serverTrust` challenges for intended
hosts, as Apple instructs manual trust handlers to check challenge type and
host
([Apple manual server trust authentication](https://developer.apple.com/documentation/foundation/performing-manual-server-trust-authentication?changes=l_9&language=objc),
verified 2026-08-02).

Release verification should include:

- A script that extracts SPKI hashes from live production chains and compares
  them with the release pinset.
- A synthetic probe from each production region and major CDN path.
- A staged rollout alarm on pin failures per app version.
- A certificate renewal rehearsal using the backup key.
- A negative test through a local interception proxy in release mode.
- A positive test through a debug proxy in debug mode, if the product supports
  debug bypass.

The easiest parts to test are pure pinset parsing and hash comparison. The hard
parts are long-lived clients, regional serving differences, app-store release
delay, and emergency rotation. Those need rehearsals, not only unit tests.

The code samples in dimension 8 were compiled or run locally with `npx tsc`,
`python3`, and `go run`.

## 16. Observability signals

Judgement. Treat pinning as an availability risk with a security purpose.

Log or measure:

- Pin decision. `allow`, `deny`, `shadow_allow`, or `shadow_would_deny`.
- Failure class. Normal TLS path failure, hostname failure, pin mismatch,
  malformed policy, expired policy, remote policy signature failure.
- Hostname and coarse region. Avoid full URLs.
- Pinset version and app version.
- Short hash prefixes of presented SPKI pins, with enough bits to debug but not
  enough to become a raw certificate dump.
- Certificate not-before and not-after dates, if privacy review permits.
- Whether a backup pin matched.
- Whether the decision came from bundled policy or signed remote policy.
- Retry count after denial, which should be near zero.
- Client update age, because old clients are the pinning risk pool.

A healthy dashboard shows no enforced pin mismatches for stable releases, no
shadow mismatches after a planned certificate change, at least one synthetic
success per pinned host and region, and a visible future-pin inventory. A
failing dashboard shows mismatch spikes after certificate renewal, mismatch
clusters by app version, regional mismatches at CDN edges, or many denied
connections followed by retry storms.

Alert thresholds should be low. One pin mismatch in production can represent a
real attack, a regional certificate drift, or a release mistake. The alert
should route to both security and the service owner, because neither group
alone can repair every cause.

## 17. Security and privacy implications

Judgement. Pinning closes one trust gap and opens an operational attack
surface.

Security benefits:

- Reduces reliance on the full CA ecosystem for selected hosts.
- Blocks some local TLS interception when the client does not grant private
  trust anchors a bypass.
- Makes unauthorized certificate issuance harder to exploit against pinned
  clients.
- Gives incident responders a crisp signal when a chain changes unexpectedly.

Security costs:

- Pinset update systems become sensitive infrastructure. Their signing keys
  need hardware or offline protection, dual control, audit logs, and replay
  defense.
- A malicious or mistaken pinset can create a denial of service.
- Pinning can reduce security if it forces teams to reuse old keys beyond their
  planned lifetime to avoid breaking clients.
- Debug bypasses can become production bypasses if not tied to build identity
  and release controls.
- Users may be trained to disable security tools or install special builds to
  get around pin failures.

Privacy considerations:

- Pin failure reports can reveal which service a user contacted, when, from
  which network region, and which certificate chain they saw.
- Full certificate chains can contain organization names and internal hostnames
  in private environments.
- Stable device identifiers are rarely needed for pinning telemetry. Prefer
  aggregate counts by app version, host, region, and pinset version.
- HPKP-style reporting needs care because a report path may itself fail or leak
  information. RFC 7469 discusses privacy considerations for pinning
  ([RFC 7469](https://datatracker.ietf.org/doc/html/rfc7469), verified
  2026-08-02).

The safest privacy posture is small telemetry: host, failure class, app
version, pinset version, region, and short fingerprints. Collect raw chains
only in controlled diagnostics with retention limits.

## 18. References

- Chris Evans, Chris Palmer, Ryan Sleevi, *RFC 7469. Public Key Pinning
  Extension for HTTP*, IETF, April 2015, sections 1, 2, 3, 4, 5 and Appendix B.
  https://datatracker.ietf.org/doc/html/rfc7469, verified 2026-08-02.
- Android Developers, *Network Security Configuration*, sections "Pin
  certificates", "debug-overrides", "trust-anchors", and "pin-set".
  https://developer.android.com/privacy-and-security/security-config, verified
  2026-08-02.
- Android Developers, *Security with network protocols*, section "Restricting
  your app to specific certificates".
  https://developer.android.com/privacy-and-security/security-ssl?authuser=2&hl=en,
  verified 2026-08-02.
- Apple Developer Documentation, *Performing Manual Server Trust
  Authentication*, section "Handle server trust authentication challenges".
  https://developer.apple.com/documentation/foundation/performing-manual-server-trust-authentication?changes=l_9&language=objc,
  verified 2026-08-02.
- Apple Developer Library, *Technical Note TN2232. HTTPS Server Trust
  Evaluation*, section "NSURLSession".
  https://developer.apple.com/library/ios/technotes/tn2232/_index.html,
  verified 2026-08-02.
- OkHttp project, *README*, TLS feature list.
  https://github.com/square/okhttp/blob/master/README.md, verified 2026-08-02.
- OkHttp, *CertificatePinner 3.0.0 API*, class documentation.
  https://javadoc.io/static/com.squareup.okhttp3/okhttp/3.0.0/okhttp3/CertificatePinner.html,
  verified 2026-08-02.
- Chromium project, *Chrome Security FAQ*, sections "How does key pinning
  interact with local proxies and filters?" and "When is key pinning enabled?"
  https://chromium.googlesource.com/chromium/src/+/HEAD/docs/security/faq.md,
  verified 2026-08-02.
- Google Chrome, *Certificate Transparency in Chrome*, overview.
  https://googlechrome.github.io/CertificateTransparency/, verified
  2026-08-02.
- Cloudflare Docs, *Certificate pinning*, sections "Recommended alternative"
  and "If you must pin certificates".
  https://developers.cloudflare.com/ssl/reference/certificate-pinning/,
  verified 2026-08-02.
- Microsoft Learn, *Certificate pinning and Azure services*, sections
  "Certificate pinning history" and "Certificate pinning limitations".
  https://learn.microsoft.com/en-us/azure/security/fundamentals/certificate-pinning,
  verified 2026-08-02.
- Microsoft Learn, *Enterprise certificate pinning overview*, sections
  "Deployment" and "Additional pin rules logging".
  https://learn.microsoft.com/en-us/windows/security/identity-protection/enterprise-certificate-pinning,
  verified 2026-08-02.
- Wikipedia, *HTTP Public Key Pinning*, deprecation status and timeline.
  https://en.wikipedia.org/wiki/HTTP_Public_Key_Pinning,
  verified 2026-08-20.
- OWASP Cheat Sheet Series, *Pinning Cheat Sheet*, sections "What Is Pinning",
  "When to Add a Pin", and "What Should Be Pinned".
  https://cheatsheetseries.owasp.org/cheatsheets/Pinning_Cheat_Sheet.html,
  verified 2026-08-02.
