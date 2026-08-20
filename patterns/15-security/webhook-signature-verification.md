---
name: Webhook Signature Verification
slug: webhook-signature-verification
family: 15-security
category: Security
aliases: [Signed Webhook, HMAC Webhook Verification, Request Signing, Webhook HMAC Verification]
first_described: "Krawczyk, Bellare, Canetti 1997"
maturity: established
related: [complete-mediation, fail-securely, secrets-management, idempotency-key, audit-log, mutual-tls, token-based-authentication]
incompatible_with: [unsigned-webhook-endpoint, parse-before-verify, shared-secret-in-client-code]
verified: 2026-08-02
---

# Webhook Signature Verification

## 1. Name, aliases, and lineage

The canonical name in this entry is Webhook Signature Verification. In product
documentation it appears as **validating webhook deliveries**, **verifying
requests**, **HMAC verification**, **request signing**, and **signed webhooks**.
GitHub documents "validating webhook deliveries" with the
`X-Hub-Signature-256` header, an HMAC hex digest, and a shared webhook secret
([https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries),
verified 2026-08-02). Slack documents "verifying requests from Slack" with
`X-Slack-Signature`, `X-Slack-Request-Timestamp`, and an HMAC SHA-256 base
string
([https://docs.slack.dev/authentication/verifying-requests-from-slack/](https://docs.slack.dev/authentication/verifying-requests-from-slack/),
verified 2026-08-02). Shopify calls the same receiver-side step HMAC
verification for HTTPS webhook deliveries and names the
`X-Shopify-Hmac-SHA256` header
([https://shopify.dev/docs/apps/build/webhooks/verify-deliveries](https://shopify.dev/docs/apps/build/webhooks/verify-deliveries),
verified 2026-08-02). Stripe documents signature verification through the
`Stripe-Signature` header and endpoint secret
([https://docs.stripe.com/webhooks/signature](https://docs.stripe.com/webhooks/signature),
verified 2026-08-02).

The cryptographic lineage is HMAC, not webhooks. RFC 2104, authored by Hugo
Krawczyk, Mihir Bellare, and Ran Canetti in 1997, specifies HMAC as a keyed
message authentication code built from a cryptographic hash function
([https://datatracker.ietf.org/doc/html/rfc2104](https://datatracker.ietf.org/doc/html/rfc2104),
verified 2026-08-02). HMAC gives a receiver with the same secret a way to
detect that the received bytes match the bytes used by the sender when it made
the MAC. That is the small primitive this pattern wraps in HTTP receiver code.

The HTTP lineage matters because a webhook is an HTTP request sent by another
system. RFC 9110 defines HTTP field names as case-insensitive
([https://datatracker.ietf.org/doc/html/rfc9110](https://datatracker.ietf.org/doc/html/rfc9110),
verified 2026-08-02). Receiver code that treats `X-Slack-Signature` and
`x-slack-signature` as different fields is therefore not implementing HTTP
header lookup correctly. RFC 9421 later standardized HTTP Message Signatures as
a broader mechanism for signing selected HTTP components with digital
signatures or MACs
([https://datatracker.ietf.org/doc/html/rfc9421](https://datatracker.ietf.org/doc/html/rfc9421),
verified 2026-08-02). Webhook Signature Verification is narrower. It usually
signs a provider-specific base string, often the raw body alone or a timestamp
plus raw body, and the verifier is an application endpoint rather than a generic
HTTP signature stack.

This entry treats HMAC-based webhook verification as the main form because the
named production systems above use it. Some providers use asymmetric
signatures, but the structure is the same: capture the exact signed bytes,
select the key, compute or verify the signature, compare safely, reject on any
failed precondition, and run business logic only after the gate passes.

## 2. Problem and context

A webhook endpoint receives requests from the public internet, usually without a
browser session, an OAuth bearer token, or a mutual TLS client certificate. The
request may trigger money movement, shipment creation, account state changes,
workflow runs, issue transitions, or customer notifications. The receiver must
decide whether the request came from the provider it trusts and whether the
payload was changed in transit before it lets application code act on the
event.

TLS protects the network connection, but many webhook deployments terminate TLS
at a CDN, load balancer, gateway, or platform edge before application code sees
the request. RFC 9421 states the same general problem for HTTP applications:
TLS can protect one connection, while the path between client and application
may contain multiple independent TLS connections
([https://datatracker.ietf.org/doc/html/rfc9421](https://datatracker.ietf.org/doc/html/rfc9421),
verified 2026-08-02). Webhook Signature Verification adds application-layer
integrity and origin checking between the provider and the receiver, even when
infrastructure rewrites transport details.

The context is asynchronous integration. The provider sends an HTTP request
because something happened elsewhere. The receiver does not control the timing,
the body format, the retry behavior, or the header names. The receiver does
control whether it reads the raw bytes before parsing, whether it keeps the
secret out of source code, whether it rejects stale deliveries, and whether it
uses an idempotency key or delivery ID to avoid duplicate side effects.

The pattern is not a general authorization model. A passing signature says the
sender had access to the shared secret or private key at signing time and that
the signed input matches the received input. It does not say the event should be
trusted as business truth, that the referenced object still exists, that the
receiver is entitled to act, or that the event has not already been processed.
Those decisions belong to authorization, reconciliation, and idempotency logic.

## 3. Forces

Judgement. The forces below are engineering trade-offs. The cited sources prove
provider behavior and cryptographic primitives. The weighing is design
judgement.

- **Authenticity.** Favoured. The receiver gets a local check that the sender
  knew the signing secret. GitHub describes webhook secrets as the way to verify
  that a delivery came from GitHub and was not tampered with
  ([https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries),
  verified 2026-08-02).
- **Byte fidelity.** Sacrificed by framework convenience. Stripe says the
  request body must be the UTF-8 body string sent by Stripe without changes, and
  that whitespace changes, key reordering, JSON parsing, or encoding changes can
  cause verification failure
  ([https://docs.stripe.com/webhooks/signature](https://docs.stripe.com/webhooks/signature),
  verified 2026-08-02). The pattern favours raw-byte handling over automatic
  body parsing.
- **Latency.** Mildly sacrificed. HMAC SHA-256 over a request body is cheap for
  normal webhook sizes, but it still adds CPU work and a memory path that reads
  the complete signed input before processing.
- **Coupling.** Sacrificed to provider protocols. Each provider chooses header
  names, timestamp format, base string format, digest encoding, replay window,
  and secret rotation rules. A receiver serving several providers needs
  provider-specific verifiers.
- **Consistency.** Favoured. All handler code runs behind the same gate. A
  handler cannot accidentally process unsigned data when the verifier is placed
  before routing to domain logic.
- **Operability.** Mixed. Failed signatures are easy to count. Root cause is
  harder because the logs must not record the secret, full signature, or full
  sensitive payload.
- **Cost.** Low recurring cost, higher setup cost. Teams must configure
  secrets, route raw bodies around parsers, implement rotation, and teach on-call
  staff the difference between a bad secret, a mutated body, and a stale
  timestamp.
- **Team topology.** Favoured when platform teams own a verifier library and
  product teams own handlers. Sacrificed when every service implements its own
  variation and learns the same edge cases again.
- **Cognitive load.** Sacrificed. Engineers must understand raw request bodies,
  header casing, byte encodings, digest encodings, constant-time comparison, and
  replay windows before changing a route.

The pattern favours authenticity and uniform gating. It pays with protocol
coupling, parser friction, and operational false rejects during framework or
gateway changes.

## 4. Applicability and non-applicability

Reach for Webhook Signature Verification when the following conditions hold.

- A public HTTP endpoint receives provider-initiated events and must reject
  spoofed requests before domain logic runs.
- The sender and receiver can share a high-entropy secret or use an asymmetric
  key that the receiver can verify.
- The receiver can access the exact bytes, timestamp, and headers that the
  provider signs.
- The provider retries deliveries, so the receiver also plans idempotency around
  a delivery ID or event ID.
- The endpoint sits behind gateways or serverless infrastructure where TLS ends
  before application code.
- The receiver needs an audit record for rejected and accepted deliveries
  without logging secrets or sensitive payloads.

Do NOT reach for it in these cases.

- **The sender cannot keep a secret.** Browser JavaScript, mobile apps, and
  downloadable clients cannot protect a shared webhook secret from the user who
  owns the device. Use OAuth, proof-of-possession tokens, or server-side relay
  designs instead.
- **The receiver cannot read the raw signed input.** If a platform parses,
  normalizes, compresses, or reserializes the body before application code can
  see it, HMAC over the raw body will fail. Change the platform path before
  adding this pattern.
- **The problem is user authorization.** A valid webhook signature does not say
  which local account may perform an action. Keep account binding and
  authorization checks in the handler.
- **The event must be confidential from the transport path.** Signatures do not
  encrypt content. RFC 9421 states that signatures do not provide
  confidentiality in its privacy considerations
  ([https://datatracker.ietf.org/doc/html/rfc9421](https://datatracker.ietf.org/doc/html/rfc9421),
  verified 2026-08-02). Use encryption or avoid sending the data.
- **The sender and receiver need non-repudiation.** HMAC is symmetric. Either
  side can create a valid MAC because both know the secret. Use asymmetric
  signatures when proof against the other party matters.
- **The endpoint receives only private network callbacks from infrastructure you
  fully control.** Mutual TLS, service mesh identity, or signed queue messages
  may be the cleaner control. Judgement. Keep HMAC if those controls terminate
  before the application boundary you need to protect.
- **The provider already terminates into a trusted event bus.** Shopify says
  Google Cloud Pub/Sub and Amazon EventBridge deliveries do not require its
  HTTPS HMAC verification path
  ([https://shopify.dev/docs/apps/build/webhooks/verify-deliveries](https://shopify.dev/docs/apps/build/webhooks/verify-deliveries),
  verified 2026-08-02). Verify at the boundary the provider names.
- **The team wants to accept failed signatures during incidents.** Fail open
  turns the pattern into logging. Use replay tooling, provider dashboards, or a
  quarantine queue instead.

## 5. Structure

Name participants by their security role, not by framework class.

- **Webhook Provider.** The remote system that owns the event and signs each
  delivery. It defines the signature scheme, header names, event retry behavior,
  and secret management user interface.
- **Endpoint Secret or Verification Key.** The credential shared with, or
  published to, the receiver. HMAC schemes use a shared secret. Asymmetric
  schemes use a public verification key at the receiver.
- **Raw Request Capture.** The receiver component that reads the request body
  before any JSON parser, form parser, decompressor, or charset converter
  changes it.
- **Signature Extractor.** The small parser for provider headers. It reads the
  signature value, timestamp, key identifier, version, or algorithm marker.
- **Base String Builder.** The provider-specific rule that chooses signed
  bytes. GitHub signs the payload contents for `X-Hub-Signature-256`; Slack
  signs a version, timestamp, and raw body joined by colons; Shopify signs the
  raw request body with the app client secret; Stripe verifies against its
  `Stripe-Signature` header and endpoint secret.
- **Cryptographic Verifier.** The HMAC or signature function plus safe compare.
  RFC 2104 defines HMAC as a MAC with a secret key and hash function
  ([https://datatracker.ietf.org/doc/html/rfc2104](https://datatracker.ietf.org/doc/html/rfc2104),
  verified 2026-08-02).
- **Replay Gate.** The timestamp window or delivery ID cache that rejects old or
  duplicated requests. Slack documents a five minute timestamp check in its
  recipe
  ([https://docs.slack.dev/authentication/verifying-requests-from-slack/](https://docs.slack.dev/authentication/verifying-requests-from-slack/),
  verified 2026-08-02).
- **Verified Event Envelope.** The internal value passed to domain handlers
  after verification. It contains parsed payload, provider name, event ID,
  received time, selected key ID, and verification result metadata.
- **Domain Handler.** The business code. It never reads unverified payloads.
  It still checks authorization, event ordering, and idempotency.
- **Audit Sink.** Logs and metrics that record provider, route, decision,
  reason class, key version, and delivery ID without recording secrets.

The central relationship is ordering. Raw Request Capture and Signature
Extractor run before parsing. Cryptographic Verifier and Replay Gate run before
Domain Handler. Audit Sink records both pass and fail paths.

## 6. ASCII structure diagram

```text
 +------------------+        HTTPS request        +------------------------+
 | Webhook Provider |---------------------------->| Webhook Endpoint       |
 | signs delivery   |                             | public route          |
 +------------------+                             +-----------+------------+
                                                                |
                                                                v
                                                     +----------+---------+
                                                     | Raw Request Capture|
                                                     | body bytes, headers|
                                                     +----------+---------+
                                                                |
                         +------------------------------+-------+------+
                         |                              |              |
                         v                              v              v
              +----------+---------+         +----------+-------+  +---+----+
              | Signature Extractor|         | Base String      |  | Clock  |
              | sig, ts, key id    |         | Builder          |  | Window |
              +----------+---------+         +----------+-------+  +---+----+
                         |                              |              |
                         +--------------+---------------+--------------+
                                        |
                                        v
                             +----------+-----------+
                             | Cryptographic        |
                             | Verifier             |
                             | HMAC or public key   |
                             +----------+-----------+
                                        |
                         reject         | accept
                    +-------------------+-------------------+
                    v                                       v
            +-------+--------+                      +-------+--------+
            | Audit Sink     |                      | Replay Gate    |
            | reason metrics |                      | delivery id    |
            +----------------+                      +-------+--------+
                                                            |
                                                            v
                                                     +------+-------+
                                                     | Domain       |
                                                     | Handler      |
                                                     +--------------+
```

## 7. Dynamics

At runtime the pattern is a gate. The receiver should not parse the body into a
domain object, enqueue work, mutate storage, or call downstream systems until
the gate has accepted the request.

```text
Provider        Edge/Gateway       Receiver Verifier       Domain Handler
   |                 |                    |                       |
   | build body      |                    |                       |
   | compute MAC     |                    |                       |
   | attach headers  |                    |                       |
   |---------------->| terminate TLS      |                       |
   |                 | forward body       |                       |
   |                 |------------------->| read raw bytes        |
   |                 |                    | find signature header |
   |                 |                    | find timestamp        |
   |                 |                    | select key            |
   |                 |                    | build signed input    |
   |                 |                    | compute expected MAC  |
   |                 |                    | safe compare          |
   |                 |                    | check replay window   |
   |                 |                    | check delivery id     |
   |                 |                    |---------------------->|
   |                 |                    | parsed verified event |
   |                 |                    |                       |
   |<----------------|<-------------------| 2xx after durable     |
   |                 |                    | accept or enqueue     |
```

Failure flow matters as much as success flow. Missing header, malformed header,
unknown key ID, stale timestamp, mismatched digest, duplicate delivery ID, and
payload too large all return before the domain handler. Judgement. Use the same
external status for most failures, often `401` or `403`, and put the specific
reason in private logs so attackers do not get a tuning oracle.

The verifier must also respect provider retry contracts. If the event is valid
but processing will be slow, persist the verified envelope or enqueue a job
before returning `2xx`. If persistence fails, return a retryable failure so the
provider can resend.

Judgement. The receiver should make the accept point explicit in code. In a
small service that point may be a call to the domain handler. In a larger
service it is often a durable write to an inbox table or queue. The important
rule is that the external response reflects whether the receiver has taken
responsibility for the verified event. Returning success before either durable
storage or completed side effects creates silent loss when the process crashes
between verification and handling.

## 8. Implementation variants

**Raw body HMAC.** The provider computes HMAC over the exact request body. The
receiver computes the same HMAC over the captured bytes. GitHub, Shopify, and
many Stripe integrations fit this family, with provider-specific header syntax.
This variant is small and fast, but fragile when middleware mutates the body.

**Timestamped base string.** The provider signs a string that includes a
timestamp plus the body. Slack uses `v0`, the timestamp, and the request body in
its documented recipe
([https://docs.slack.dev/authentication/verifying-requests-from-slack/](https://docs.slack.dev/authentication/verifying-requests-from-slack/),
verified 2026-08-02). This variant gives replay defense without storing every
delivery forever, but it requires clock discipline and clear skew policy.

**Header-carried version and multiple signatures.** Stripe's header shape
contains a timestamp and signature versions such as `t=...` and `v1=...`
([https://docs.stripe.com/webhooks/signature](https://docs.stripe.com/webhooks/signature),
verified 2026-08-02). This form supports version migration and secret
rotation. It costs a more careful parser and test vectors for overlapping
secrets.

**Asymmetric request signature.** The provider signs with a private key and the
receiver verifies with a public key. This avoids shared-secret custody by the
receiver, and it supports stronger accountability between parties. It costs key
discovery, key rotation, algorithm policy, and larger signatures. RFC 9421
includes both digital signature and MAC algorithms for HTTP message signatures
([https://datatracker.ietf.org/doc/html/rfc9421](https://datatracker.ietf.org/doc/html/rfc9421),
verified 2026-08-02).

**Canonical JSON signature.** Sender and receiver parse JSON and sign a
canonical form rather than the transport bytes. RFC 8785 defines the JSON
Canonicalization Scheme as an invariant JSON representation for cryptographic
operations
([https://datatracker.ietf.org/doc/html/rfc8785](https://datatracker.ietf.org/doc/html/rfc8785),
verified 2026-08-02). This can survive whitespace and key order differences,
but it only works when both sides implement the same canonicalization rules and
when the signed content is JSON.

**Provider SDK verifier.** The receiver calls the official SDK function.
Stripe tells users to call `constructEvent()` with the request body, signature
header, and endpoint secret
([https://docs.stripe.com/webhooks/signature](https://docs.stripe.com/webhooks/signature),
verified 2026-08-02). This reduces local crypto code. It still needs raw-body
routing, secret loading, observability, and tests around the framework adapter.

**Dual-secret rotation.** During secret rotation the verifier accepts a bounded
set of active secrets and records which key version matched. This variant is a
deployment pattern rather than a cryptographic change. It prevents a race where
the provider starts signing with a new secret before every receiver instance has
loaded it. The trade-off is policy complexity. A long overlap window increases
the value of an old secret. A short overlap window raises outage risk when
configuration propagation is slow. Judgement. Treat rotation as a state machine
with named phases: old only, old plus new, new preferred with old accepted, and
new only. Each phase should have metrics for matched key version and a rollback
path.

**Queue-after-verify.** The endpoint verifies the request, writes a verified
event envelope to durable storage or a queue, and returns before the domain
handler runs. This variant is useful when provider timeouts are short or domain
work is slow. The security boundary remains at the HTTP route. The queue stores
only verified events, so downstream workers do not need access to provider
secrets. The cost is a new failure point: the endpoint must return a retryable
error if it cannot persist the verified envelope.

**Verify-at-edge plus verify-in-app.** Some platforms can run a small verifier
at the edge and forward accepted requests to the application. Judgement. This is
useful for reducing attacker load on application servers, but the application
should still receive evidence of verification, such as a signed internal header
or a trusted service identity. A plain header like `X-Verified: true` is not
enough if callers can reach the application without passing through the edge.

Minimal TypeScript example, GitHub-style HMAC over raw bytes:

```typescript
const { createHmac, timingSafeEqual } = require("crypto");

export function verifyGitHubWebhook(
  secret: string,
  body: Uint8Array,
  header: string | undefined,
): boolean {
  if (!header || !header.startsWith("sha256=")) return false;
  const actualHex = header.slice("sha256=".length);
  if (!/^[0-9a-f]{64}$/i.test(actualHex)) return false;

  const expected = createHmac("sha256", secret).update(body).digest();
  const actual = Buffer.from(actualHex, "hex");
  if (actual.length !== expected.length) return false;
  return timingSafeEqual(actual, expected);
}

const body = Buffer.from("Hello, World!", "utf8");
const ok = verifyGitHubWebhook(
  "It's a Secret to Everybody",
  body,
  "sha256=757107ea0eb2509fc211221cce984b8a37570b6d7586c22c46f4379c8b043e17",
);
if (!ok) throw new Error("signature rejected");
```

Minimal Python example, timestamped Slack-style base string:

```python
import hashlib
import hmac
import time


def verify_slack(secret: str, body: bytes, timestamp: str, header: str) -> bool:
    try:
        sent_at = int(timestamp)
    except ValueError:
        return False
    if abs(int(time.time()) - sent_at) > 60 * 5:
        return False

    base = b"v0:" + timestamp.encode("ascii") + b":" + body
    expected = "v0=" + hmac.new(
        secret.encode("utf-8"), base, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, header)


now = str(int(time.time()))
payload = b"token=xyzz&team_id=T1"
secret_value = "example-webhook-shared-secret-not-real"
base_string = b"v0:" + now.encode("ascii") + b":" + payload
sig = "v0=" + hmac.new(
    secret_value.encode("utf-8"), base_string, hashlib.sha256
).hexdigest()
assert verify_slack(secret_value, payload, now, sig)
```

Minimal Go example, Shopify-style base64 HMAC over raw bytes:

```go
package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"fmt"
)

func verifyShopify(secret string, body []byte, header string) bool {
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write(body)
	expected := mac.Sum(nil)

	actual, err := base64.StdEncoding.DecodeString(header)
	if err != nil {
		return false
	}
	return hmac.Equal(actual, expected)
}

func main() {
	body := []byte(`{"topic":"orders/create","id":123}`)
	secret := "client-secret"
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write(body)
	header := base64.StdEncoding.EncodeToString(mac.Sum(nil))
	if !verifyShopify(secret, body, header) {
		panic("signature rejected")
	}
	fmt.Println("verified")
}
```

Language notes. TypeScript is common at API edges and has Node's
`crypto.timingSafeEqual`, documented as a constant-time byte comparison with
same-length inputs
([https://nodejs.org/api/crypto.html](https://nodejs.org/api/crypto.html),
verified 2026-08-02). Python exposes `hmac.compare_digest` for digest
comparison during verification
([https://docs.python.org/3/library/hmac.html](https://docs.python.org/3/library/hmac.html),
verified 2026-08-02). Go exposes `hmac.Equal` in its standard library; the Go
sample uses it through `crypto/hmac`.

## 9. Known production uses

**Stripe webhooks.** Stripe documents endpoint signature verification with the
`Stripe-Signature` header, the raw request body string, and the endpoint secret.
It also documents common failure causes when frameworks mutate the body before
verification
([https://docs.stripe.com/webhooks/signature](https://docs.stripe.com/webhooks/signature),
verified 2026-08-02).

**GitHub webhooks.** GitHub sends an HMAC signature in
`X-Hub-Signature-256`, generated from the webhook secret token and payload
contents. GitHub recommends safe comparison rather than normal equality and
gives a published test vector for `Hello, World!`
([https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries),
verified 2026-08-02).

**Slack platform requests.** Slack signs requests with an app-specific signing
secret, sends `X-Slack-Signature`, and includes
`X-Slack-Request-Timestamp`. Its validation recipe signs a version, timestamp,
and raw body base string and rejects timestamps outside a five minute window
([https://docs.slack.dev/authentication/verifying-requests-from-slack/](https://docs.slack.dev/authentication/verifying-requests-from-slack/),
verified 2026-08-02).

**Shopify HTTPS webhook deliveries.** Shopify includes a base64 HMAC signature
in `X-Shopify-Hmac-SHA256`, generated with the app client secret and raw
request body. Shopify also tells receivers to use the delivery ID for duplicate
detection
([https://shopify.dev/docs/apps/build/webhooks/verify-deliveries](https://shopify.dev/docs/apps/build/webhooks/verify-deliveries),
verified 2026-08-02).

These production uses are similar enough to prove the pattern and different
enough to warn against a one-size verifier. Header names, encodings, timestamp
rules, and rotation behavior belong to the provider contract.

## 10. Consequences

Positive consequences.

- Spoofed webhook requests fail before they reach business logic.
- Payload tampering across gateways, queues, or debugging proxies becomes
  detectable when the signed input covers the mutated bytes.
- Receivers can validate locally without a network call to the provider.
- Security policy becomes a route-level invariant rather than a convention in
  every handler.
- Provider incidents and attacker traffic become visible as signature failure
  metrics.
- Secret rotation can be handled centrally when the verifier supports multiple
  active keys.
- Idempotency and replay checks fit naturally next to signature verification,
  so duplicate delivery behavior is designed at the same boundary.

Negative consequences.

- Framework body parsers become security-sensitive infrastructure.
- A gateway change that rewrites bodies or strips headers can break all
  deliveries at once.
- Provider differences create repeated code unless the team builds a verifier
  interface.
- Secret custody expands to every receiver environment that accepts webhooks.
- Debugging failed signatures is awkward because the most useful values are
  often sensitive.
- Clock skew can cause false rejects for timestamped schemes.
- Large request bodies may need buffering before they can be verified and
  processed.
- HMAC does not provide confidentiality, sender authorization inside local
  business rules, or non-repudiation.

Judgement. The pattern earns its keep when a webhook can cause durable side
effects. For notification-only endpoints with no state change and no sensitive
data, the cost may exceed the risk.

## 11. Failure modes and misuse

Judgement. These are production failure patterns expressed as observable
symptoms, likely causes, and fixes.

| Symptom | Cause | Fix |
|---|---|---|
| Every delivery from one provider returns `401` after a framework upgrade. | JSON or form parsing now runs before raw-body capture, so the verifier signs changed bytes. | Move the webhook route before body parsers, or configure the route to expose raw bytes. Stripe documents this class of failure for body mutation. |
| Only retries older than a few minutes fail. | Timestamp window rejects delayed provider retries or queue delays. | Check provider retry timing, verify local clocks, and store accepted delivery IDs so replay policy does not rely on a larger time window alone. |
| A valid test vector passes locally but production rejects real payloads with non-ASCII text. | Code converts bytes through the wrong charset or signs a string instead of the raw request body. | Treat the signed input as bytes. Decode only after verification. |
| Attack traffic creates high CPU use even though all signatures fail. | The verifier computes HMAC for huge bodies before enforcing size limits. | Apply a provider-specific maximum body size before reading or hashing the full request. |
| Some valid deliveries fail behind a load balancer. | The load balancer removes, renames, or duplicates signature headers. | Preserve provider headers exactly enough for application lookup, and remember HTTP field names are case-insensitive per RFC 9110. |
| One tenant can validate another tenant's webhook. | Secret lookup uses route-level configuration rather than tenant, app, or account binding. | Select the verification key from the provider account or key ID before comparison, and bind the verified event to that account. |
| Secret rotation causes a multi-hour outage. | The verifier accepts only one active secret, while the provider may sign with old and new secrets during rollout. | Support a grace set of active secrets and log the matched key version. |
| Duplicate side effects occur after provider retries. | Signature verification proves origin but not first processing. | Add Idempotency Key or delivery ID storage after verification and before side effects. Shopify documents a delivery ID for duplicate detection. |
| Incident logs expose secrets or full signatures. | Debug logging prints headers and environment values during verification failures. | Redact secrets, truncate signature digests, and log only reason class, provider, route, and key version. |
| Developers bypass verification in local code and ship the bypass. | Test fixture and production path share a flag with a permissive default. | Make bypass unavailable in production configuration and add a startup check that fails closed. |

Misuse has one recurring shape: treating the signature as proof of more than it
proves. It proves possession of signing material and byte integrity for the
signed input. It does not prove local authorization, event freshness beyond the
chosen replay controls, or business correctness.

## 12. Trade-off matrix

| Force | Webhook Signature Verification | Mutual TLS | IP Allow List | OAuth Bearer Token | HTTP Message Signatures |
|---|---|---|---|---|---|
| Authenticity | Strong for a provider secret or key. | Strong for client certificate identity. | Weak because source networks change and can be proxied. | Strong for caller identity when token issuance is controlled. | Strong and standardized across selected HTTP components. |
| Payload integrity | Strong for signed bytes. | Protects transport hop, not always application-to-application bytes after TLS termination. | None. | None unless token binds request content. | Strong for covered components and digest-covered body. |
| Replay defense | Needs timestamp or delivery ID cache. | Needs protocol or app-level replay controls. | None. | Token expiry helps but does not stop copied requests inside lifetime. | Has signature parameters such as creation and expiry, still needs app policy. |
| Operational cost | Moderate. Raw body, secrets, rotation, metrics. | High. Certificate issuance, renewal, trust stores. | Low setup, high drift. | Moderate. Issuer, validation, scopes, rotation. | Higher. Canonicalization, libraries, key metadata, covered component policy. |
| Provider coupling | High. Provider header and base string rules. | Medium. Certificate profile and CA policy. | High. Provider network ranges. | Medium. Token format and issuer policy. | Lower if both sides adopt RFC 9421, higher during migration. |
| Debuggability | Medium. Deterministic but sensitive. | Medium. TLS handshakes and cert chains can be opaque. | Easy until networks change. | Medium. Token claims help if safely logged. | Harder because canonicalization and covered components add moving parts. |
| Best fit | Public async callbacks with side effects. | Service-to-service calls with managed PKI. | Low-risk coarse filtering as a secondary control. | Caller-initiated API calls with delegated authorization. | Cross-party HTTP signing with selected component coverage. |

Judgement. The named alternatives are controls that often sit near webhook
security. They are not mutually exclusive in all systems. A high-risk receiver
may use an IP allow list as a coarse filter, mutual TLS at the edge, HMAC at the
application boundary, and idempotency in storage.

## 13. Related and incompatible patterns

**Complete Mediation** composes directly. Every webhook request must pass the
verification gate every time, not only during endpoint registration.

**Fail Securely** is the error policy. Missing header, parse error, stale
timestamp, unknown key, and mismatch all reject before side effects.

**Secrets Management** is the custody pattern for HMAC schemes. Secrets belong
in a secret store or platform configuration, not in source code. GitHub tells
users not to hardcode a token or push it to a repository
([https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries),
verified 2026-08-02).

**Idempotency Key** is the sibling pattern for retries. Signatures say a
delivery is authentic. Idempotency says whether its side effects already ran.

**Audit Log** records accepted and rejected deliveries. It must avoid secrets
and full payloads unless the retention and privacy model allows them.

**Mutual TLS** can complement or replace HMAC when both parties can manage
certificates and the application trusts the TLS termination boundary. HMAC is
still useful when the app wants a check over provider-signed bytes after the
edge.

**HTTP Message Signatures** may replace provider-specific webhook signing when
both sides can adopt RFC 9421. It is broader and more standardized, but heavier
than many webhook products need.

**Parse-before-verify** is incompatible. If the parser changes whitespace,
ordering, encoding, or form representation before verification, the receiver is
no longer checking what the provider signed.

**Unsigned webhook endpoint** is incompatible for side-effecting callbacks. A
route that accepts unauthenticated public POSTs and then acts on payload fields
is not using this pattern.

## 14. Refactoring path in and out

To introduce the pattern into an existing unsigned webhook endpoint:

1. Inventory providers, routes, event types, body parsers, gateways, and current
   retry behavior.
2. Add raw-body capture for each webhook route. Keep existing parsing after a
   feature flag so behavior can be compared without side effects.
3. Store provider secrets in the existing secret manager. Do not place them in
   repository files, build logs, or client-visible configuration.
4. Implement a provider verifier interface with methods for extracting metadata,
   building the signed input, checking the signature, and returning a typed
   failure reason.
5. Add provider test vectors. Use GitHub's published `Hello, World!` vector for
   a GitHub-style verifier
   ([https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries),
   verified 2026-08-02).
6. Place the verifier before domain parsing. Return a stable reject response and
   log a redacted private reason.
7. Add delivery ID storage or an Idempotency Key check before side effects.
8. Roll out in report-only mode only if the provider can resend events and the
   endpoint is not high risk. Judgement. For money or privilege changes, prefer
   a maintenance window and fail closed.
9. Remove the old unsigned route or reject requests missing provider signature
   headers.

Refactorings from the refactoring family apply. **Extract Function** separates
header parsing, base string building, and comparison. **Introduce Parameter
Object** can package provider metadata, raw body, and received time. **Replace
Conditional with Polymorphism** helps when one route handles several providers
with different schemes. **Move Function** moves verifier logic from handlers to
an edge adapter owned by the platform team.

To remove the pattern when it no longer earns its cost:

1. Prove the endpoint no longer receives public provider calls or no longer
   creates side effects.
2. Move the receiver behind a stronger boundary, such as a provider-managed
   event bus or mutual TLS service path.
3. Keep idempotency if retries or duplicate messages remain possible.
4. Remove secrets from the secret store after provider configuration no longer
   references the endpoint.
5. Keep historical audit records until retention expires.

Do not remove verification because it is noisy. Fix raw-body handling, secret
rotation, or replay policy instead.

## 15. Testing and verification

Testing starts with fixed vectors. A verifier needs tests for the provider's
known good signature, bad signature, missing signature, malformed header,
wrong algorithm marker, wrong secret, wrong body, timestamp outside the window,
future timestamp, and duplicate delivery ID. GitHub publishes a concrete secret,
payload, and expected SHA-256 signature for validation tests
([https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries),
verified 2026-08-02).

Use byte-level tests, not only JSON-object tests. The same parsed JSON object
can have several byte representations. Stripe warns that whitespace changes,
key reordering, JSON parsing, and encoding changes can break verification
([https://docs.stripe.com/webhooks/signature](https://docs.stripe.com/webhooks/signature),
verified 2026-08-02). Include tests where the JSON object is equivalent but the
bytes differ, and assert that only the exact signed bytes pass.

Use framework integration tests. In Express, FastAPI, Rails, Next.js, serverless
functions, or gateway adapters, test the real route with middleware enabled.
The failure you want to catch is not HMAC math. It is parser ordering, header
lookup, body buffering, compression, or gateway mapping.

Use property-style tests for parser hardening. Generate malformed signature
headers, duplicated attributes, upper and lower case header names, non-hex
characters, base64 errors, empty body, huge body, and repeated signature fields.
The expected outcome is reject without panic and without logging secrets.

Use time control. Inject a clock so timestamp windows can be tested with
deterministic past, present, and future values. Slack's recipe checks whether a
timestamp differs from local time by more than five minutes
([https://docs.slack.dev/authentication/verifying-requests-from-slack/](https://docs.slack.dev/authentication/verifying-requests-from-slack/),
verified 2026-08-02). Do not make tests sleep to cross that boundary.

Use redaction tests. Assert that logs for failures contain provider, route,
reason class, delivery ID hash, and key version, while omitting secret values,
full request bodies, and full signatures.

What becomes easier: unit testing the security gate as a pure function over
headers, bytes, secret, and clock. What becomes harder: end-to-end testing of
framework body behavior and operational rotation because those sit outside the
pure verifier.

## 16. Observability signals

Judgement. A healthy verifier is boring. The dashboard shows steady accepted
delivery counts, low failure rates, stable latency, and zero accepted duplicate
side effects.

Log fields for every rejected delivery:

- provider name
- route
- decision, `reject`
- reason class, such as `missing_signature`, `bad_header`, `stale_timestamp`,
  `unknown_key`, `signature_mismatch`, `duplicate_delivery`, or `body_too_large`
- delivery ID hash if present
- key version or key ID if known
- body byte length
- request received time
- trace ID

Log fields for accepted deliveries:

- provider name
- event type
- delivery ID hash
- key version or key ID
- verification latency
- enqueue or persistence result
- domain handler outcome

Metrics:

- `webhook.verify.accept.count`
- `webhook.verify.reject.count` tagged by provider and reason
- `webhook.verify.latency_ms`
- `webhook.verify.body_bytes`
- `webhook.verify.clock_skew_seconds`
- `webhook.delivery.duplicate.count`
- `webhook.secret.match.count` tagged by key version
- `webhook.handler.duration_ms`
- `webhook.handler.retryable_failure.count`

Trace spans should separate `capture_raw_body`, `parse_signature_header`,
`verify_signature`, `check_replay`, `persist_event`, and `run_handler`. Keep
raw bodies and secrets out of span attributes. Record only sizes, hashes, and
reason classes.

Alert on sudden provider-wide signature mismatch, any accepted request with an
unknown key version, high stale timestamp rate, duplicate spikes, and body size
rejections. A deploy that changes body parsing often appears as an immediate
rise in `signature_mismatch` for one route. A provider secret rotation issue
often appears as mismatch for all routes using one provider account.

## 17. Security and privacy implications

The pattern closes one attack path: unauthenticated public POSTs that spoof a
provider event. It also detects payload tampering for the bytes included in the
signature. GitHub describes this as verifying that deliveries are from GitHub
and were not tampered with
([https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries),
verified 2026-08-02).

It opens or concentrates several responsibilities.

- **Secret exposure.** HMAC verification places a high-value secret in receiver
  runtime configuration. Anyone who reads it can forge events. Store, rotate,
  and audit it like an API credential.
- **Timing side channels.** Normal equality may stop at the first different
  byte. Node documents `crypto.timingSafeEqual` for comparing HMAC digests or
  secret values and warns that surrounding code can still introduce timing
  leaks
  ([https://nodejs.org/api/crypto.html](https://nodejs.org/api/crypto.html),
  verified 2026-08-02). Python recommends `hmac.compare_digest` instead of
  `==` for digest comparison
  ([https://docs.python.org/3/library/hmac.html](https://docs.python.org/3/library/hmac.html),
  verified 2026-08-02).
- **Replay.** A copied valid request may still be harmful if replay controls are
  absent. Use timestamp windows and durable delivery ID checks.
- **Confidentiality.** HMAC does not hide payload contents. RFC 9421 states that
  signatures do not provide confidentiality
  ([https://datatracker.ietf.org/doc/html/rfc9421](https://datatracker.ietf.org/doc/html/rfc9421),
  verified 2026-08-02). Treat webhook bodies as data that may need encryption,
  minimization, or short retention.
- **Canonicalization attacks.** If a scheme signs selected fields or
  canonicalized JSON rather than raw bytes, parser differences can become an
  attack surface. RFC 8785 exists because cryptographic operations need an
  invariant data representation
  ([https://datatracker.ietf.org/doc/html/rfc8785](https://datatracker.ietf.org/doc/html/rfc8785),
  verified 2026-08-02).
- **Algorithm downgrade.** Accept only the provider-approved algorithm and
  version. GitHub recommends `X-Hub-Signature-256` with HMAC SHA-256 and treats
  the older `X-Hub-Signature` SHA-1 header as legacy
  ([https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries),
  verified 2026-08-02).
- **Privacy in logs.** Rejected webhooks often contain customer data. Logging
  the full body to debug signature failures can create a larger privacy incident
  than the failed delivery.

Judgement. The strongest practical posture is deny by default, verify before
parse, compare safely, bind to the correct tenant, reject stale or duplicate
deliveries, and log enough to debug without exposing the signed material.

## 18. References

- Backman, A., Richer, J., and Sporny, M. RFC 9421, *HTTP Message Signatures*,
  February 2024, sections 1, 3, 7, and 8.
  [https://datatracker.ietf.org/doc/html/rfc9421](https://datatracker.ietf.org/doc/html/rfc9421),
  verified 2026-08-02.
- Fielding, R., Nottingham, M., and Reschke, J. RFC 9110, *HTTP Semantics*,
  June 2022, section 5.1.
  [https://datatracker.ietf.org/doc/html/rfc9110](https://datatracker.ietf.org/doc/html/rfc9110),
  verified 2026-08-02.
- GitHub Docs, *Validating webhook deliveries*.
  [https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries),
  verified 2026-08-02.
- Krawczyk, H., Bellare, M., and Canetti, R. RFC 2104, *HMAC.
  Keyed-Hashing for Message Authentication*, February 1997, sections 1 and 2.
  [https://datatracker.ietf.org/doc/html/rfc2104](https://datatracker.ietf.org/doc/html/rfc2104),
  verified 2026-08-02.
- Node.js Project, *Crypto*, `crypto.timingSafeEqual`.
  [https://nodejs.org/api/crypto.html](https://nodejs.org/api/crypto.html),
  verified 2026-08-02.
- Python Software Foundation, *hmac. Keyed-Hashing for Message Authentication*,
  `hmac.compare_digest`.
  [https://docs.python.org/3/library/hmac.html](https://docs.python.org/3/library/hmac.html),
  verified 2026-08-02.
- Rundgren, A., Jordan, B., and Erdtman, S. RFC 8785, *JSON Canonicalization
  Scheme*, June 2020, abstract and status.
  [https://datatracker.ietf.org/doc/html/rfc8785](https://datatracker.ietf.org/doc/html/rfc8785),
  verified 2026-08-02.
- Shopify Developer Docs, *Verify webhook deliveries*.
  [https://shopify.dev/docs/apps/build/webhooks/verify-deliveries](https://shopify.dev/docs/apps/build/webhooks/verify-deliveries),
  verified 2026-08-02.
- Slack Developer Docs, *Verifying requests from Slack*.
  [https://docs.slack.dev/authentication/verifying-requests-from-slack/](https://docs.slack.dev/authentication/verifying-requests-from-slack/),
  verified 2026-08-02.
- Stripe Docs, *Resolve webhook signature verification errors*.
  [https://docs.stripe.com/webhooks/signature](https://docs.stripe.com/webhooks/signature),
  verified 2026-08-02.
