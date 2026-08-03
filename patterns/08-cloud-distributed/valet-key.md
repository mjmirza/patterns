---
name: Valet Key
slug: valet-key
family: 08-cloud-distributed
category: Security
aliases: [Pre-Signed URL, Signed URL, Scoped Access Token]
first_described: "Homer, Sharp, Brader, Narumoto, Swanson, Cloud Design Patterns, Microsoft patterns and practices, 2014"
maturity: canonical
related: [gatekeeper, federated-identity, gateway-routing, ambassador, claim-check, static-content-hosting]
incompatible_with: []
verified: 2026-08-03
---

# Valet Key

## 1. Name, aliases, and lineage

The canonical name is Valet Key, drawn directly from the everyday object it is
named after. A car valet hands a driver a second key that starts the engine
and releases the parking brake but does not open the glovebox or the trunk.
The driver never learns the master key, and the valet's authority over the
car expires the moment the driver reclaims it. The pattern applies the same
idea to a client that needs to move data in or out of a store the application
does not want to sit in the middle of. Microsoft's patterns and practices
group documented the pattern under this exact name in the book *Cloud Design
Patterns. Prescriptive Architecture Guidance for Cloud Applications*, written
by Alex Homer, John Sharp, Larry Brader, Masashi Narumoto and Trent Swanson,
first published by Microsoft in 2014 and maintained since as a living
reference on the Azure Architecture Center (Microsoft, "Valet Key pattern,"
Azure Architecture Center, verified 2026-08-03,
https://learn.microsoft.com/en-us/azure/architecture/patterns/valet-key).

Outside the Microsoft catalog the same mechanism is described under a
provider-specific name rather than a pattern name, and each of those names is
in real, current, widely read documentation rather than folklore. Amazon Web
Services calls the same construct a presigned URL and states plainly that the
credentials used to sign it "are those of the AWS user who generated the URL"
(Amazon Web Services, "Sharing objects with presigned URLs," Amazon S3 User
Guide, verified 2026-08-03,
https://docs.aws.amazon.com/AmazonS3/latest/userguide/ShareObjectPreSignedURL.html).
Google Cloud calls it a signed URL and states that "anyone in possession of
the signed URL can use it while it's active, regardless of whether they have
a valid account" (Google Cloud, "Signed URLs," Cloud Storage documentation,
verified 2026-08-03,
https://docs.cloud.google.com/storage/docs/access-control/signed-urls).
Cloudflare, building an S3-compatible object store, reuses the AWS term
directly and describes the mechanism as being "generated client-side with no
communication with R2, requiring only your R2 API credentials and an
implementation of the AWS Signature Version 4 signing algorithm" (Cloudflare,
"Presigned URLs," R2 API documentation, verified 2026-08-03,
https://developers.cloudflare.com/r2/api/s3/presigned-urls/). Azure's own
concrete implementation of a valet key is the shared access signature, a
string of query parameters appended to a storage URL and cryptographically
signed with an account key or, in the preferred current form, a short-lived
delegation key tied to a Microsoft Entra ID managed identity (Microsoft,
"Valet Key pattern," Azure Architecture Center, verified 2026-08-03).

Three distinct names, four vendors, one shape, a short-lived, narrowly
scoped, cryptographically unforgeable token that a broker issues once and a
resource server verifies on every subsequent request without ever contacting
the broker again. This entry treats "presigned URL" and "signed URL" as
implementation-level synonyms rather than a different pattern, because each
vendor's own documentation describes the identical problem, the identical
solution shape, and the identical set of considerations that the Microsoft
catalog entry lists under the Valet Key name.

## 2. Problem and context

An application sits between a client, a browser, a mobile app, a worker
process, and a data store or messaging service, object storage, a queue, a
database export target. The client needs to move a payload, often a large
one, into or out of that store. The obvious first implementation routes the
transfer through the application. The client uploads to an API endpoint, the
application authenticates the caller, then the application itself streams the
bytes onward to storage; downloads run in reverse. This is the shape every
web framework tutorial teaches, and it is correct for small, infrequent
payloads where the application legitimately needs to see every byte, such as
validating a form submission.

It stops being correct once payload size or request volume grows. Every byte
that passes through the application consumes the application's own compute,
memory and outbound bandwidth, and every concurrent transfer holds an
application server thread, a connection pool slot or a container instance
open for as long as the slowest client on that connection takes to finish.
Azure's own framing of the context states this precisely, the application
"absorbs valuable resources such as compute, memory, and bandwidth" when it
sits in the data path, and doing so "requires the application to scale to
meet demand" even though the actual work, moving bytes, is something the
storage tier can already do natively (Microsoft, "Valet Key pattern," Azure
Architecture Center, verified 2026-08-03). Letting the storage tier handle
the transfer directly removes that bottleneck, but naive direct access
introduces a worse problem. The client would need the storage account's own
credentials to talk to it, and once a credential is handed to an untrusted
client, that credential is no longer under the application's control. It
cannot expire on a schedule the application chooses, it cannot be scoped to
one object, and revoking it typically means rotating a shared secret that
every other legitimate client also depends on.

The context that produces this problem has three recurring shapes. The first
is bulk media upload and download, video, images, large documents, where
payload volume is the entire cost driver and the application performs no
per-byte logic. The second is background export or import, a nightly job that
hands a client a link to a generated report or accepts a client-supplied
dataset for batch ingestion, where the transfer window is long but the
application's involvement should be limited to authorization at the start.
The third is a multi-tenant SaaS product that must let each tenant's users
reach only their own tenant's slice of a shared bucket or table, where a
single shared credential covering the whole store would give every tenant
implicit access to every other tenant's data the moment that credential
leaked into client-side code, a browser network tab, or a mobile app binary.

## 3. Forces

The pattern balances five forces that pull in different directions, and it is
honest to say up front which of them the pattern favors and which it
sacrifices.

**Server load against operability.** Removing the application from the data
path is the entire point, and it produces a real, measurable win, no proxy
compute, no doubled bandwidth bill for data that transits the application
before reaching the client, no thread or connection held open for the
duration of a slow upload. Azure names this directly as motivation, stating
the pattern helps "maximize scalability and performance" (Microsoft, "Valet
Key pattern," verified 2026-08-03). The pattern gives this up nowhere, but it
buys that win at the cost of operability. Once a client holds a valid valet
key, the application has no further say over that specific transfer until the
key expires. There is no "kill this upload mid-stream" control unless the
application separately built a completion or cancellation channel.

**Security surface against convenience.** A time-limited, resource-scoped,
capability-bearing token narrows the blast radius of a credential leak
enormously compared to a long-lived shared secret. A leaked valet key exposes
one object, for one permission, for one short window; a leaked storage master
key exposes the whole account, forever, until someone notices and rotates it.
Azure's guidance is explicit that "the important factors are to limit the
validity period, and especially the location of the resource, as tightly as
possible" (Microsoft, "Valet Key pattern," verified 2026-08-03). This is the
pattern's strongest force, and it is not free. Every axis of narrowing,
shorter TTL, tighter scope, single-verb permission, is an axis of added
friction for a legitimate client whose network is slow, whose clock drifts,
or whose operation genuinely spans a longer window than the issuer
anticipated.

**Auditability against decoupling.** Because the resource server, not the
application, terminates every request after issuance, the application loses
the ability to observe or log individual bytes as they move, and in most
implementations it loses the ability to count how many times a key was used
unless the underlying store separately emits access logs or events back to
the application. Azure lists this as an explicit, unresolved limitation. "If
the client doesn't, or can't, notify the server of completion of the
operation, and the only limit is the expiration period of the key, the
application won't be able to perform auditing operations such as counting the
number of uploads or downloads" (Microsoft, "Valet Key pattern," verified
2026-08-03). A design that needs a hard audit trail of every access, not only
a log of who was authorized, is fighting this force rather than being served
by it.

**Cost against granularity of control.** Presigned and shared-access tokens
are cheap to generate, a symmetric-key signing operation with no round trip
to the store itself, which is why AWS, Google Cloud and Cloudflare all
generate them entirely client-side with no network call to the storage
service at issuance time (Cloudflare, "Presigned URLs," verified 2026-08-03).
That cheapness is bought by giving up fine-grained runtime control. The
token format each vendor supports typically expresses time, verb and
resource path, and nothing richer, so the pattern cannot express "allow this
upload only if it is under 50 megabytes" without a separate enforcement
mechanism, a limit every vendor's own documentation calls out (Microsoft,
"Valet Key pattern," verified 2026-08-03; Amazon Web Services, "Sharing
objects with presigned URLs," verified 2026-08-03).

**Coupling against reach.** The pattern deliberately couples the client to
the concrete shape of the resource server's protocol, its URL scheme, its
signature algorithm, its query parameter names, because the client is talking
to that resource server directly rather than through an application-defined
API. This is a coupling the Gatekeeper and Gateway Routing patterns exist
specifically to avoid, at the cost of reintroducing the proxy that Valet Key
removes. Choosing Valet Key is choosing reach and throughput over protocol
independence.

## 4. Applicability and non-applicability

Reach for Valet Key when all three of these hold at once.

- The store itself, not the application, is the natural place to enforce
  fine-grained access, because the store already speaks a protocol, an
  object storage REST API, a message queue's native client, that supports
  scoped, signed, time-limited tokens as a first-class primitive rather than
  something the application has to bolt on.
- Payload size or transfer volume is large enough, or frequent enough, that
  routing it through the application is a genuine and measurable cost, in
  compute, in bandwidth billing, in held-open connections, or in the number
  of application instances required purely to shuttle bytes. Azure names this
  explicitly as the deciding case, "when clients regularly upload or download
  data, particularly where there's a large volume or when each operation
  involves large files" (Microsoft, "Valet Key pattern," verified
  2026-08-03).
- The application can correctly determine, at the moment of issuance, the
  full scope of what the client should be allowed to do, because after
  issuance the application has no further opportunity to intervene in that
  specific transfer.

Do not reach for it, and treat each of these as a real disqualifier rather
than a nuance to work around, for the following reasons, several of which
Azure states directly as considerations against the pattern (Microsoft,
"Valet Key pattern," verified 2026-08-03).

- **The client already holds a durable, first-class identity with the
  backend, and role-based access control already reaches the store.** If a
  client authenticates to the application with a session or token that the
  storage layer can itself validate, for example an identity-aware storage
  layer wired to the same identity provider, issuing a second, separate
  scoped credential adds a moving part without adding security, because the
  identity-aware path already gives per-request, revocable, audited access.
  Azure states this plainly. "If clients can already uniquely authenticate to
  your backend service, with Azure role-based access control, for example,
  don't use this pattern."
- **The application must inspect, transform, validate or reject the payload
  before it lands, or before it reaches the client.** A valet key hands the
  client a direct pipe to the store; there is no hook in the middle for
  virus scanning an upload before it is durably written, resizing an image
  on the way in, or redacting a field on the way out. Any of those needs
  puts the application back in the data path by definition, which removes
  the reason to use this pattern in the first place.
- **The transfer must be individually metered, capped in size, or counted
  per client with hard enforcement, not only a coarse expiring key.** No
  major vendor's signed-URL primitive can express "reject this upload past
  50 MB" or "this token may be used exactly once" as a native property; the
  closest native control is a create-only permission that prevents
  overwrite, which is a weaker guarantee than a true single-use token
  (Microsoft, "Valet Key pattern," verified 2026-08-03, "Issues and
  considerations").
- **The resource has no native support for scoped, time-limited, signed
  access tokens at all**, which is true of some legacy stores, self-hosted
  databases with only static credentials, and many internal microservices
  that were never built with this capability. Retrofitting the property this
  pattern depends on is often a larger project than the pattern is meant to
  solve.
- **The transfer is small, rare, or already synchronous with request
  processing that the application must perform anyway**, a form field
  written to a database row as part of a transaction, for instance. The
  operational overhead of a second credential-issuing round trip is not
  repaid by any bandwidth or compute saving worth measuring.
- **A strict, non-negotiable audit trail of every individual access is a
  compliance requirement**, and the store cannot itself emit that trail back
  to a system the application controls. Because the application is not on
  the data path, it can only audit what it was told about, either the
  issuance event or a client-reported completion notice, neither of which
  proves the transfer actually happened as authorized.

## 5. Structure

Three participants recur in every implementation of this pattern, named by
the role they play rather than by a specific product.

- **The requester.** The client that ultimately performs the direct
  operation against the resource, a browser uploading a file, a mobile app
  downloading a report, a batch worker writing an export. The requester
  never holds a durable credential to the resource; it only ever holds a
  valet key with a bounded lifetime.
- **The issuer.** A lightweight application component, frequently a single
  serverless function, that authenticates and authorizes the requester using
  whatever mechanism the application already trusts, then mints a valet key
  scoped to exactly the operation being authorized, one resource path, one
  permission, one expiry. The issuer is the only participant that ever holds
  the long-lived signing credential or account key, and in the strongest
  current implementations it never holds even that, instead requesting a
  short-lived delegation key from the resource service's own identity system
  at issuance time (Microsoft, "Valet Key pattern," verified 2026-08-03,
  "Example" section, describing a user delegation key obtained from the
  Azure Function's managed identity).
- **The resource service.** The data store or messaging endpoint, object
  storage, a queue, a table, that natively understands the valet key format
  and validates signature, scope, verb and expiry on every request it
  receives, with zero communication back to the issuer at validation time.
  This is the property that makes the pattern scale. Verification is a local
  cryptographic check the resource service performs against a key it never
  needed the issuer's help to check, not a lookup against a central session
  store.

A fourth, optional participant appears in implementations that care about
revocation or usage counting, a **completion listener**, a mechanism by
which the requester, or the resource service itself through an event, tells
the issuer that the operation finished, so the issuer can log it, invalidate
the key early, or trigger downstream processing such as a virus scan.

## 6. ASCII structure diagram

```
+----------+   1. auth'd request    +------------------------+
|          |----------------------->|                        |
| Requester|                        |  Issuer (application)  |
| (client) |<-----------------------|  validates identity,    |
|          |  2. signed valet key   |  chooses scope + TTL,   |
+----+-----+  (URL/token, scope,    |  signs with account key |
     |         verb, expiry)        |  or delegated key       |
     |                              +-----------+-------------+
     | 3. direct request                        |
     | (PUT/GET/etc), no app                     | signing key or
     | in the middle                              | delegation-key
     v                                             | request only
+------------------------------------+             v
|         Resource Service           |   (no per-request call
|  (object storage, queue, table)    |    back to issuer)
|  validates signature, scope,       |
|  verb, and expiry locally          |
+------------------------------------+
             ^
             |  optional
             |  completion event / notice
             +----------------------------> Completion Listener
                                              (invalidate, log,
                                               trigger next step)
```

## 7. Dynamics

The runtime flow has a strict two-phase shape. A brokered issuance phase that
is slow, authenticated and application-controlled, followed by a direct
access phase that is fast, unauthenticated by the application and entirely
governed by the token itself.

In the issuance phase the requester calls the issuer over whatever channel
the application already secures, typically an authenticated HTTPS endpoint.
The issuer performs its normal authorization check, exactly as it would for
any other protected endpoint, then decides the precise scope the requester
is entitled to for this one operation, which container or table, which
object key or row range, which single verb (read, or create, or write, never
a broader set than the operation requires), and how long the window should
stay open. It signs that scope into a token, using either a long-held account
signing key or, in the pattern's stronger current form, a short-lived
delegation key it first requests from the resource service's own identity
system (Microsoft, "Valet Key pattern," verified 2026-08-03). It returns the
signed token, or a URL with the token embedded as a query string, to the
requester and is then, deliberately, out of the loop.

In the direct access phase the requester presents the token straight to the
resource service, with no further involvement from the issuer or the rest of
the application. The resource service recomputes the expected signature from
the token's own claims and its own copy of the signing material, compares it
to the signature presented, checks the current time against the expiry claim,
and checks the requested verb and path against the scope claim. If every
check passes, it performs the operation directly; if any check fails, it
rejects the request with no application involvement at all. This is the
property that removes the application from the data path. Verification is a
local, stateless cryptographic comparison, not a call back to a session
store or to the issuer.

An optional third phase closes the loop for applications that need it. If
the operation is one the application must know completed, such as a file
upload that must trigger a downstream virus scan or a database write-back,
the requester, or an event mechanism on the resource service itself where
one exists, notifies the issuer, which can then log the completion, mark the
scope's create-only permission as consumed, or, on stores that support it,
invalidate the key early rather than waiting out its natural expiry
(Microsoft, "Valet Key pattern," verified 2026-08-03, "Issues and
considerations").

```
Requester           Issuer (Application)          Resource Service
   |                        |                             |
   |--1. authenticated----->|                             |
   |   request for op       |                             |
   |                        |--(optional) request--------->|
   |                        |  delegation key from         |
   |                        |  resource identity system     |
   |                        |<--short-lived delegation------|
   |                        |  key                          |
   |                        | sign token: resource path,    |
   |                        | permission, expiry             |
   |<--2. valet key---------|                             |
   |   (signed token/URL)   |                             |
   |                        |                             |
   |--3. direct op (PUT/GET) with valet key -------------->|
   |                        |                             | verify signature,
   |                        |                             | scope, verb, expiry
   |<--4. result (2xx / 403 / expired) ---------------------|
   |                        |                             |
   |--5. optional completion notice------------------------>|
   |                        |<--(or event from store)------|
   |                        | log, invalidate early,        |
   |                        | trigger next step              |
```

## 8. Implementation variants

**Symmetric HMAC signing over a synthetic policy string.** The issuer holds a
shared secret, builds a canonical string encoding resource path, permission
and expiry, computes an HMAC over it, and appends the signature and the
claims as query parameters. This is the mechanism underlying Amazon S3
presigned URLs, where the SDK signs using AWS Signature Version 4 and the
requester's AWS credentials directly (Amazon Web Services, "Sharing objects
with presigned URLs," verified 2026-08-03), and it is the mechanism
Cloudflare R2 reuses wholesale for S3 API compatibility, stating that
presigned URLs there require only "your R2 API credentials and an
implementation of the AWS Signature Version 4 signing algorithm" with no
network call to R2 at generation time (Cloudflare, "Presigned URLs,"
verified 2026-08-03). This is the cheapest variant to implement and the
easiest to reason about, and it is the variant most exposed to the risk that
a leaked long-term account key compromises every token ever signed with it,
retroactively and forward, until the key is rotated.

**Delegated, identity-bound signing.** Instead of signing with a long-lived
account key, the issuer first requests a short-lived delegation key from the
resource service's own identity provider, using its own managed identity or
service account, and signs the token with that delegation key instead. Azure
Blob Storage's user delegation shared access signature is the reference
implementation. The issuing Azure Function calls a delegation-key API
against the storage account using its own Microsoft Entra ID managed
identity, narrows the resulting key to a three minute window, and signs the
container, blob name, create-only permission and expiry into the token from
that delegation key rather than a static account key (Microsoft, "Valet Key
pattern," verified 2026-08-03, "Example" code sample). This variant bounds
the blast radius of a compromised signing key to that key's own short
lifetime, at the cost of one additional round trip per issuance batch and a
dependency on the resource service exposing a delegation-key API, which not
every store does.

**Opaque server-side token with lookup.** Rather than encoding the scope
directly into a self-verifying signature, the issuer generates a random
opaque token, stores the scope, expiry and a usage counter server-side,
typically in a fast key-value store, and the resource service, or a thin
proxy in front of it, calls back to that store on every access to validate
and decrement. This reintroduces a network hop the pure signed-URL variants
avoid, which sacrifices the pattern's main throughput advantage, but it
buys precise, real-time revocation and true single-use enforcement, which
the self-contained signature variants cannot express natively. This is a
reasonable trade when the granularity Azure's own considerations flag as
unavailable, hard usage caps and mid-flight revocation, is a genuine
requirement (Microsoft, "Valet Key pattern," verified 2026-08-03, "Control
the level of access the key will provide").

**Capability URL with no separate signature parameter.** Some
implementations fold the entire capability into the path segment itself, a
long, unguessable, cryptographically random path component that functions
as both identifier and proof of authorization, rather than a base resource
path plus a separate signature query parameter. This is common for one-off
download links, a generated report, a password reset confirmation, where the
issuer wants the simplest possible verification, membership in a set of
issued identifiers, rather than a verifiable HMAC. It sacrifices the
self-verifying property, a resource service that only checks whether a path
exists cannot itself enforce an expiry or scope without server-side state,
in exchange for simplicity, and it collapses in practice into the opaque
server-side token variant above.

**Client-composed multipart or resumable variants.** For very large
uploads, several object stores extend the basic single-request valet key
into a multi-step flow. The issuer signs an initial start-multipart-upload
operation, the requester then receives per-part signed URLs, sometimes
issued in a single batch, sometimes on demand as each part completes, and a
final signed complete operation stitches the parts together. This keeps
every individual request within the pattern's stateless verification model
while accommodating uploads that would otherwise exceed a single request's
practical size or a single token's practical validity window.

## 9. Known production uses

**Amazon S3 presigned URLs.** AWS's own user guide documents generating a
presigned URL through the console, the CLI (`aws s3 presign`) or any of the
AWS SDKs, and states that "the credentials used by the presigned URL are
those of the AWS user who generated the URL." The console path caps
expiration at 12 hours from creation; the CLI and SDK path allows up to 7
days, expressed in seconds through the `--expires-in` parameter (Amazon Web
Services, "Sharing objects with presigned URLs," Amazon S3 User Guide,
verified 2026-08-03,
https://docs.aws.amazon.com/AmazonS3/latest/userguide/ShareObjectPreSignedURL.html).

**Azure Blob Storage shared access signatures.** This is the pattern's
reference implementation, published by the same team that named the pattern.
The current recommended shape issues a user delegation SAS, signed with a
delegation key obtained through the storage account's own managed identity
system rather than a static account key, scoped to a single container, a
single blob name, create-only permission, and roughly a three minute
validity window in the worked example, so that "the token can only be used
with, at most, one file" (Microsoft, "Valet Key pattern," Azure Architecture
Center, verified 2026-08-03,
https://learn.microsoft.com/en-us/azure/architecture/patterns/valet-key).

**Google Cloud Storage signed URLs.** Google's documentation states signed
URLs "provide time-limited access to specific Cloud Storage resources
without requiring users to have valid accounts," that "anyone in possession
of the signed URL can use it while it's active," and that "the longest
expiration value is 604800 seconds (7 days)," with access restricted to the
XML API surface of Cloud Storage (Google Cloud, "Signed URLs," Cloud Storage
documentation, verified 2026-08-03,
https://docs.cloud.google.com/storage/docs/access-control/signed-urls).

**Cloudflare R2 presigned URLs.** Cloudflare's S3-compatible object store
reuses the AWS Signature Version 4 mechanism directly, supporting GET, HEAD,
PUT and DELETE with a documented expiration range from 1 second to 7 days,
604,800 seconds, and states the signature parameters embedded in the URL
cannot be altered without invalidating the signature (Cloudflare, "Presigned
URLs," R2 API documentation, verified 2026-08-03,
https://developers.cloudflare.com/r2/api/s3/presigned-urls/).

The fact that four independently built, commercially competing storage
platforms converged on the identical shape, a signature over a canonical
string encoding resource, verb and expiry, embedded in a URL that the
resource server itself validates with no callback, is itself evidence that
this is a settled, load-bearing production pattern rather than a
theoretical construct that appears only in a pattern catalog.

## 10. Consequences

**Positive.**

- Removes the application from the data path for the transfer itself,
  which is the single largest driver of the pattern's adoption. Compute,
  memory and bandwidth that would otherwise be spent proxying bytes are
  spent zero times, because the resource service handles the transfer
  directly (Microsoft, "Valet Key pattern," verified 2026-08-03).
- Narrows the blast radius of a leaked credential from "the whole account,
  indefinitely" to "one resource, one permission, one short window," which
  is a qualitative security improvement over any design that hands a client
  the account's own long-lived key.
- Removes the operational burden of provisioning, tracking and revoking
  per-user standing credentials to the resource service; the issuer mints
  tokens on demand and the resource service needs no notion of individual
  client identity at all.
- Scales to an effectively unbounded number of concurrent transfers with no
  per-transfer state on the issuer, because verification is local to the
  resource service and requires no lookup.
- Composes cleanly with a CDN or edge cache in front of the resource service
  for the read path, since a scoped, time-limited URL is exactly the shape
  most CDNs already know how to cache and pass through.

**Negative.**

- The application loses real-time visibility and control over an individual
  transfer once the key is issued; there is no native "cancel this upload"
  or "pause this download" once the requester has a valid token.
- Auditing and usage counting are, by default, weak or absent. Without a
  completion notice from the requester or an event from the resource
  service, the application cannot reliably know how many times a key was
  used, only that it was valid for its window (Microsoft, "Valet Key
  pattern," verified 2026-08-03).
- The client is coupled directly to the resource service's own protocol,
  which is a coupling the application had previously insulated the client
  from; a future migration to a different storage provider now touches
  client code, not only server code.
- Payload validation, transformation and inspection cannot happen inline,
  because the application is not in the data path; any such need must be
  moved to an asynchronous, post-write step, which introduces a window
  during which an unvalidated object exists in the store.
- A key's expressive power is limited to what the resource service's own
  signing scheme supports, typically time, verb and path; size limits, rate
  limits and single-use semantics beyond a create-only permission are not
  natively expressible and must be layered on separately if they are needed.

## 11. Failure modes and misuse

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | Unexpectedly large storage or bandwidth bills traced to one client, with no obvious abuse in the application's own logs. | The valet key granted a broad permission for the full validity window rather than a single, narrow operation, so a buggy client retry loop, or a compromised client, repeatedly overwrote or re-uploaded the same object using the same still-valid key. | Scope every key to the narrowest permission that accomplishes the one intended operation, and where the resource service supports it, use a create-only permission rather than a general write permission, since create-only "doesn't allow overwrites, so each token can only be used for one write activity," making the token effectively single-use even without a server-side revocation lookup (Microsoft, "Valet Key pattern," verified 2026-08-03, "Consider how to control users' behavior"). |
| 2 | Legitimate users report intermittent access-denied or link-expired errors specifically on slow networks or large files, while the same operation succeeds reliably on fast connections. | The token's time-to-live was chosen to be tight for security reasons without accounting for the real-world distribution of client network speeds, so operations that legitimately need longer than the median case fail near the end of their transfer. | Separate the token's issuance-side authorization window from its usage-side completion window where the resource service allows it, a short window to begin the operation, a longer window to finish an already-started multipart operation, or expose a renewal endpoint the client can call before expiry if the transfer is still in progress, while keeping the initial window as tight as the security requirement demands (Microsoft, "Valet Key pattern," verified 2026-08-03, "Manage the validity status and period of the key"). |
| 3 | A security review finds valet key URLs, including their embedded signatures, sitting in plaintext in load balancer access logs, application performance monitoring traces, or a shared analytics pipeline, long after the tokens themselves have expired. | Because the token is carried in the URL's query string, every intermediary that logs request URLs, proxies, gateways, CDNs, log aggregators, captures it by default, and if that log data is retained or forwarded before the token's own expiry, the token reads as a live credential. | Prefer delivering the token in a request header or a POST body where the resource service's protocol allows it, keep validity windows short enough that the exposure window closes quickly, and where the URL-in-query-string shape cannot be avoided, restrict and delay log retention so that logs are not queryable until after every plausible token in them has already expired (Microsoft, "Valet Key pattern," verified 2026-08-03, "Deliver the key securely"). |
| 4 | A malicious or malformed file lands durably in the resource store and is later served to other users or ingested by a downstream pipeline before anyone notices it should have been rejected. | The valet key grants the requester a direct, application-free write path, so no inline virus scan, content-type check or schema validation ran before the bytes were durably written, which is the trade-off the pattern makes by removing the application from the data path. | Treat every object written through a valet key as untrusted until an asynchronous post-write step, triggered by an event on the resource service where one exists, has validated it; quarantine or gate visibility of the object until that step passes, composing this pattern with a Gatekeeper-style validation stage that runs after the write rather than before it (Microsoft, "Valet Key pattern," verified 2026-08-03, "Validate, and optionally sanitize, all uploaded data"). |
| 5 | A multi-tenant application discovers, during an incident review, that a token issued for one tenant's object could also be replayed against a sibling object in a different tenant's container. | The resource path encoded into the token's signed scope was built from user-supplied input without being canonicalized or bound to the authenticated tenant's own namespace, so a requester who could influence the resource path at issuance time obtained access outside the intended scope. | Derive the scoped resource path entirely from server-side, authenticated context, the tenant ID resolved from the caller's own identity, never from a client-supplied field, and treat the signed path as authoritative and immutable once issued, since "it's critical to accurately specify the resource or the set of resources to which the key applies" (Microsoft, "Valet Key pattern," verified 2026-08-03, "Control the level of access the key will provide"). |

## 12. Trade-off matrix

The alternatives compared here are named, real architectural choices for the
same problem, giving an untrusted client access to a resource without
handing it a standing credential.

| Force | Valet Key | Gatekeeper (broker proxies all traffic) | Gateway Routing (reverse proxy forwards to backend) | Federated Identity (client authenticates directly to the store via an identity provider) | Static shared credential (anti-pattern baseline) |
|---|---|---|---|---|---|
| Application load per transfer | None after issuance | High, every byte passes through the broker | Moderate, every request passes through the gateway even if the payload streams | None, client talks to the store directly using its own federated token | None |
| Latency for large transfers | Low, direct path | Higher, extra network hop through the broker | Higher, extra hop through the gateway | Low, direct path | Low, direct path |
| Credential exposure if leaked | One resource, one permission, one short window | Nothing leaks; the broker never hands out a credential | Nothing leaks; the gateway never hands out a credential | Depends on the identity token's own scope and lifetime, often broader than a valet key's single-resource scope | Entire account, indefinitely, until manually rotated |
| Inline validation of payload | Not possible, must be asynchronous, post-write | Possible; broker inspects every request | Possible at the gateway layer (headers, routing rules), limited on payload body without buffering | Not possible; client talks straight to the store | Not possible |
| Revocation granularity | Coarse, usually only wait for expiry unless the store supports early invalidation | Fine; broker can reject any specific caller instantly | Fine; gateway can reject any specific caller instantly | Depends on the identity provider's token revocation support | None short of rotating the shared secret for everyone |
| Operational complexity | Low; issuer is a thin, stateless-at-verification-time function | Higher; broker must scale with total transfer volume, not only request count | Moderate; gateway must scale with total transfer volume | Moderate; depends on federation setup with the resource service | Lowest to build, highest to operate safely |
| Best fit | High-volume, large-payload transfers where per-request inspection is not required | Payloads needing per-request inspection, sanitization or protocol translation | Traffic needing routing, aggregation or protocol adaptation more than raw throughput | Clients that already have a durable, revocable identity the store itself can validate | Never; included only as the baseline this pattern replaces |

Gatekeeper and Valet Key are frequently confused because both broker access
to a backend resource, but they sit at opposite ends of the same trade-off.
Gatekeeper keeps every request flowing through a validating proxy at the
cost of that proxy's own scaling, while Valet Key removes the proxy from
the data path entirely and accepts the loss of per-request inspection in
exchange. A single system can, and often should, use both, Gatekeeper for
requests that need inspection, Valet Key for high-volume transfers that do
not.

## 13. Related and incompatible patterns

**Gatekeeper.** The structural opposite for the same problem class. Where
Valet Key removes the application from the data path, Gatekeeper keeps a
dedicated, hardened validating component in the path for every request. The
two compose naturally in a single system. Gatekeeper protects the narrow
authenticated endpoint that issues valet keys, and a Valet Key removes the
Gatekeeper from the bulk data transfer that follows issuance.

**Federated Identity.** A parallel but distinct approach to the same goal,
letting an untrusted client authenticate directly against the resource
service using a token issued by a separate identity provider, rather than
against a resource-scoped signature issued by the application. Federated
Identity typically grants broader, role-shaped access; Valet Key grants
narrower, single-operation-shaped access. The delegated-signing variant of
Valet Key (dimension 8) is, in effect, a hybrid. The issuer uses a
federated identity of its own, a managed identity or service account, to
obtain the narrow, resource-scoped delegation key it then hands to the
client.

**Gateway Routing.** A reverse proxy pattern that forwards requests to
different backend services based on routing rules, without necessarily
inspecting or transforming the payload. Azure's own Valet Key documentation
names Gateway Routing directly as the alternative a team reaches for when
Valet Key is ruled out, noting it "might not be adding additional value to
the transaction" for pure large-file transfer, which is exactly the case
Valet Key is built for (Microsoft, "Valet Key pattern," verified
2026-08-03, "Example").

**Ambassador.** A client-side proxy, typically a sidecar, that can hold and
manage a valet key on the requester's behalf, refreshing it before
expiry and retrying failed requests, so that application code calling
through the Ambassador does not need to know the token exists. This is a
common pairing in service-to-service scenarios where a background worker,
rather than a human-driven browser, is the requester.

**Claim Check.** A messaging pattern that replaces a large payload in a
message with a reference to where the payload can be retrieved, keeping the
message bus itself lightweight. Claim Check and Valet Key are frequently
used together. The reference the Claim Check pattern hands downstream
consumers is often itself a valet key, letting a consumer retrieve the
actual payload directly from storage without routing it back through the
messaging infrastructure.

**Static Content Hosting.** Shares the same underlying motivation, letting a
client reach storage or a CDN directly rather than through the application,
but for content that is public and does not need per-client scoping. Valet
Key is the variant of the same idea for content that must be scoped to one
client, one operation, and one short window; Static Content Hosting is the
variant for content anyone with the URL may fetch indefinitely.

**Incompatible with.** No pattern in this catalog is structurally
incompatible with Valet Key; the closest tension is with any design that
insists on inline, synchronous inspection of every byte of a transfer, since
that requirement, by definition, contradicts the pattern's premise that the
application is not on the data path. That tension is a reason to choose a
different pattern for that specific transfer, not a conflict that arises
from combining the two within one system.

## 14. Refactoring path in and out

**Introducing the pattern into an application that currently proxies
transfers through itself.** Start by identifying the exact scope every
existing proxied transfer actually needs, one resource, one verb, a
realistic time window, derived from server-side context rather than
client-supplied input. Stand up the issuance endpoint first, behind the
same authentication and authorization the proxied endpoint already used, so
that the authorization decision itself does not change, only where the
bytes flow afterward. Verify the resource service's native token support
covers the verbs actually needed, many stores support scoped read and write
independently; fewer support arbitrary scoped delete. Ship the new
issuance endpoint and the direct-access client code behind a feature flag,
running the old proxied path and the new direct path side by side against a
subset of traffic, and compare error rates, latency and, if the store
exposes it, access logs, before cutting over the remaining traffic. Keep the
old proxied endpoint in place, disabled by default, until the new path has
run in production long enough that its failure modes, from dimension 11,
have each been observed and handled at least once, since those failure
modes rarely all surface in a staging environment.

**Removing the pattern once it stops earning its place.** The signal that a
Valet Key implementation should be refactored out is almost always one of
the disqualifiers from dimension 4 becoming true after the fact rather than
being anticipated up front. A compliance requirement for a hard, per-access
audit trail lands, a virus-scanning or content-validation requirement
appears that must run before the object is durably written rather than
after, or the resource service's own access-control model matures to the
point where it can validate the client's existing durable identity directly,
making the pattern's own reason for existing, avoiding a standing
credential, moot. The removal path mirrors the introduction path in
reverse, reintroduce an application-side endpoint for the operation,
running it alongside the still-live direct path, and migrate client traffic
over gradually rather than revoking direct access all at once, since any
client holding a still-valid, unexpired valet key at cutover time must be
allowed to finish naturally rather than being abruptly cut off mid-transfer.

## 15. Testing and verification

**What becomes easy.** The issuer's authorization logic is a plain, pure
function once separated from the network call it makes, given a caller's
authenticated identity and the resource they are requesting, does this
scope-and-permission combination get returned. This is trivially unit
testable with no need to stand up the actual resource service, and the
matrix of cases, correct tenant scoping, correct verb restriction, correct
expiry, rejection of an unauthorized resource path, is exactly the kind of
table-driven test suite this pattern rewards, because the entire security
model of the pattern lives in this one function.

**What becomes harder.** The end-to-end behavior, does a token this
function produces actually work against the real resource service and
actually get rejected once expired, cannot be verified by a pure unit test
of the issuer alone, because correctness depends on the resource service's
own signature verification agreeing with the issuer's own signing. This
needs an integration test against either the real resource service, in a
disposable or namespaced test account, or a high-fidelity emulator that
implements the same signing algorithm, and a naive mock that simply returns
success for any well-formed token will not catch a signing algorithm
mismatch, a clock-skew bug, or a scope that the resource service interprets
more loosely than the issuer intended.

**Test doubles that apply.** For unit tests of the issuer's authorization
logic, a plain in-memory fake standing in for the caller's authenticated
identity is sufficient and preferred over mocking any part of the signing
process. For integration coverage, prefer the real resource service's own
local emulator where the vendor ships one, since that is the only double
that actually implements the identical signature verification the
production resource service performs; a hand-rolled mock server that only
checks whether some signature was present gives false confidence and will
not catch the class of bug where a scope is technically valid but broader
than intended. Time-dependent behavior, specifically expiry, should be
tested by injecting a controllable clock into the issuer's signing function
rather than by sleeping the test suite past a real token's real expiry,
which is slow and flaky by construction.

**A specific regression worth pinning as a test.** Every deployment of this
pattern should carry at least one test that asserts a token issued for
resource A, when replayed verbatim against resource B, same permission,
same expiry, only the target path changed, is rejected by the resource
service. This directly targets the failure mode from dimension 11 where an
under-scoped or improperly canonicalized resource path lets a token issued
for one tenant's data be replayed against a sibling tenant's data.

## 16. Observability signals

A healthy Valet Key deployment shows a distinctive, boring shape on a
dashboard, a steady rate of issuance calls at the application tier and a
much larger, cheap-to-serve rate of direct operations at the resource tier
that the application never sees individually, only in aggregate through the
resource service's own metrics.

**What to log at issuance.** The issuer should log, for every key it mints,
the resource path granted, the permission granted, the requested TTL, the
caller's authenticated identity, and a correlation identifier the client can
later present back on a completion notice. This log is the only record the
application will ever have of what was authorized, since the resource
service's own access log, where one exists, typically records the request
that was made, not the identity that requested the issuance.

**What to log at the resource service.** Object storage and queue services
generally expose their own access logs or events independently of the
application, and those logs should be enabled and retained, since they are
the only record of whether an issued key was actually used, how many times,
and whether any request was rejected for an expired or malformed signature.
A rising rate of signature-rejected requests at the resource service, with
no corresponding rise in issuance calls at the application, is the single
strongest signal of either a client-side clock skew problem or an active
attempt to forge or replay a token.

**What a healthy instance looks like.** Issuance latency stays low and flat,
typically a single cryptographic signing operation plus, in the delegated
variant, one call to obtain a delegation key. The ratio of issued keys to
successfully completed operations, measured through completion notices
where the application collects them, stays close to one; a ratio well below
one over time suggests either keys are being issued and abandoned, wasting
nothing structurally but worth investigating, or completion notices are
being lost.

**What a failing instance looks like.** A spike in resource-service-side
authorization failures with a flat or declining issuance rate points at
either widespread clock skew or a leaked or reused signing key being probed
by an attacker. A spike in issuance calls with no corresponding rise in
resource-service traffic points at a client that is requesting keys it
never uses, worth investigating for a retry loop or a misconfigured
prefetch. A rising p99 issuance latency, isolated to the delegated-signing
variant, most often traces to the resource service's own identity system
being under load or throttling delegation-key requests, which the issuer
should treat as a dependency worth its own circuit breaker rather than
letting a slow delegation call degrade every issuance request.

## 17. Security and privacy implications

**Signing key custody is the whole security model.** Whoever holds the
material used to sign a valet key can mint a token for anything that
material's own scope permits, so the issuer's own compute environment
becomes as sensitive as the resource service's master credentials would be
in a design with no valet key at all. The delegated-signing variant
(dimension 8) narrows this exposure because the issuer itself never
holds a long-lived account key, only a short-lived delegation key it
requests immediately before use, which bounds how much damage a compromise of the
issuer's own environment can do (Microsoft, "Valet Key pattern," verified
2026-08-03).

**The URL, not only the resource, is the secret.** Because most
implementations embed the signature directly in a URL's query string, that
URL is a bearer credential. Anyone who obtains it, by shoulder-surfing a
screen, by reading an intercepted log line, by a browser extension that
harvests page URLs, can use it exactly as the intended requester could,
with no further authentication check. Google Cloud's own documentation
states this without qualification. "Anyone in possession of the signed URL
can use it while it's active" (Google Cloud, "Signed URLs," verified
2026-08-03). This is the reason every vendor's guidance converges on the
same two mitigations, keep the validity window as short as the operation
genuinely needs, and always deliver the URL over an encrypted channel,
never over plain HTTP or an unencrypted message (Microsoft, "Valet Key
pattern," verified 2026-08-03, "Deliver the key securely").

**Logs are a leak vector the pattern does not close on its own.** A signed
URL in a query string is captured by default by proxies, load balancers,
CDN access logs and application performance monitoring tools that were
never designed to treat request URLs as sensitive. This is a genuine,
named risk in the pattern's own reference documentation, not a
hypothetical. "The URL containing the key might be recorded in server log
files" (Microsoft, "Valet Key pattern," verified 2026-08-03). Any system
using this pattern at scale needs an explicit answer for how long those
logs are retained relative to the shortest token TTL it issues, and whether
log data forwarded to a third-party analytics or observability platform is
itself a system this pattern's threat model needs to account for.

**Untrusted write paths need a downstream trust boundary.** Because the
application never inspects a payload written through a valet key before it
lands, every object created this way must be treated as untrusted at the
moment it becomes visible to any other consumer, exactly as any other
user-supplied upload would be. This has real privacy implications beyond
malware. A client with a scoped write permission for an object path they do
not fully control, for example a path partly derived from another user's
identifier through an insufficiently validated parameter, could overwrite
or pollute data belonging to someone else, which is why the resource path
bound into the signed scope must be derived entirely from server-side,
authenticated context and never from client-supplied input (Microsoft,
"Valet Key pattern," verified 2026-08-03, "Control the level of access the
key will provide").

**Clock trust is part of the trust boundary.** Expiry enforcement depends
on the resource service's clock agreeing, within tolerance, with the
issuer's clock at signing time. Azure's own guidance recommends specifying
a start time slightly earlier than the current server time specifically to
tolerate client and server clock drift (Microsoft, "Valet Key pattern,"
verified 2026-08-03), which is a small but real acknowledgment that the
security guarantee this pattern provides is bounded by the accuracy of
clocks the application does not fully control.

## Code

The pattern is shown here in TypeScript, Python, Go and Java, an issuer that
signs a narrow, time-limited scope with HMAC-SHA256, and a verifier that
recomputes the signature, checks the expiry, and accepts or rejects, the
same shape every production implementation in dimension 9 uses under its
own vendor-specific signing algorithm. Rust is omitted here because its
standard library carries no HMAC or SHA-256 primitive, only third-party
crates provide one, and this repository's code samples avoid an external
dependency where the pattern itself does not require one; Swift and C# are
omitted because the mechanism is identical to the languages shown, with no
distinct idiom this pattern introduces in either.

### TypeScript

```typescript
import { createHmac, randomBytes } from "node:crypto";

interface ValetKeyParams {
  readonly resourcePath: string;
  readonly permission: "read" | "write";
  readonly ttlSeconds: number;
}

interface SignedValetKey {
  readonly resourcePath: string;
  readonly permission: string;
  readonly expiresAtEpoch: number;
  readonly signature: string;
}

class ValetKeyIssuer {
  constructor(private readonly signingKey: Buffer) {}

  issue(
    params: ValetKeyParams,
    nowEpoch: number = Math.floor(Date.now() / 1000)
  ): SignedValetKey {
    const expiresAtEpoch = nowEpoch + params.ttlSeconds;
    const payload = `${params.resourcePath}\n${params.permission}\n${expiresAtEpoch}`;
    const signature = createHmac("sha256", this.signingKey)
      .update(payload)
      .digest("base64url");
    return {
      resourcePath: params.resourcePath,
      permission: params.permission,
      expiresAtEpoch,
      signature,
    };
  }
}

function verifyValetKey(
  key: SignedValetKey,
  signingKey: Buffer,
  nowEpoch: number
): boolean {
  if (nowEpoch > key.expiresAtEpoch) {
    return false;
  }
  const payload = `${key.resourcePath}\n${key.permission}\n${key.expiresAtEpoch}`;
  const expected = createHmac("sha256", signingKey)
    .update(payload)
    .digest("base64url");
  return expected === key.signature;
}

const signingKey = randomBytes(32);
const issuer = new ValetKeyIssuer(signingKey);
const nowEpoch = Math.floor(Date.now() / 1000);
const key = issuer.issue(
  { resourcePath: "uploads/report-2026-08.pdf", permission: "write", ttlSeconds: 180 },
  nowEpoch
);
const allowed = verifyValetKey(key, signingKey, nowEpoch);
console.log(`valet key valid ${allowed}`);
```

### Python

```python
import base64
import hashlib
import hmac
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class ValetKey:
    resource_path: str
    permission: str
    expires_at: int
    signature: str


def _canonical_payload(resource_path: str, permission: str, expires_at: int) -> bytes:
    return f"{resource_path}\n{permission}\n{expires_at}".encode("utf-8")


def issue_valet_key(
    signing_key: bytes, resource_path: str, permission: str, ttl_seconds: int, now: int
) -> ValetKey:
    expires_at = now + ttl_seconds
    payload = _canonical_payload(resource_path, permission, expires_at)
    digest = hmac.new(signing_key, payload, hashlib.sha256).digest()
    signature = base64.urlsafe_b64encode(digest).decode("ascii")
    return ValetKey(resource_path, permission, expires_at, signature)


def verify_valet_key(signing_key: bytes, key: ValetKey, now: int) -> bool:
    if now > key.expires_at:
        return False
    payload = _canonical_payload(key.resource_path, key.permission, key.expires_at)
    digest = hmac.new(signing_key, payload, hashlib.sha256).digest()
    expected = base64.urlsafe_b64encode(digest).decode("ascii")
    return hmac.compare_digest(expected, key.signature)


if __name__ == "__main__":
    signing_key = b"a-32-byte-test-signing-key-here"
    now = int(time.time())
    valet = issue_valet_key(signing_key, "uploads/report.pdf", "write", 180, now)
    print("valet key valid", verify_valet_key(signing_key, valet, now))
```

### Go

```go
package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"fmt"
	"time"
)

type ValetKey struct {
	ResourcePath string
	Permission   string
	ExpiresAt    int64
	Signature    string
}

func canonicalPayload(resourcePath, permission string, expiresAt int64) []byte {
	return []byte(fmt.Sprintf("%s\n%s\n%d", resourcePath, permission, expiresAt))
}

func sign(signingKey []byte, resourcePath, permission string, expiresAt int64) string {
	mac := hmac.New(sha256.New, signingKey)
	mac.Write(canonicalPayload(resourcePath, permission, expiresAt))
	return base64.URLEncoding.EncodeToString(mac.Sum(nil))
}

func IssueValetKey(signingKey []byte, resourcePath, permission string, ttl time.Duration, now time.Time) ValetKey {
	expiresAt := now.Add(ttl).Unix()
	return ValetKey{
		ResourcePath: resourcePath,
		Permission:   permission,
		ExpiresAt:    expiresAt,
		Signature:    sign(signingKey, resourcePath, permission, expiresAt),
	}
}

func VerifyValetKey(signingKey []byte, k ValetKey, now time.Time) bool {
	if now.Unix() > k.ExpiresAt {
		return false
	}
	expected := sign(signingKey, k.ResourcePath, k.Permission, k.ExpiresAt)
	return hmac.Equal([]byte(expected), []byte(k.Signature))
}

func main() {
	signingKey := []byte("a-32-byte-test-signing-key-here")
	now := time.Now()
	valet := IssueValetKey(signingKey, "uploads/report.pdf", "write", 3*time.Minute, now)
	fmt.Println("valet key valid", VerifyValetKey(signingKey, valet, now))
}
```

### Java

```java
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.util.Base64;

public final class ValetKeyService {
    private static final String ALGORITHM = "HmacSHA256";

    private final byte[] signingKey;

    public ValetKeyService(byte[] signingKey) {
        this.signingKey = signingKey;
    }

    public record ValetKey(String resourcePath, String permission, long expiresAt, String signature) {}

    public ValetKey issue(String resourcePath, String permission, long ttlSeconds, long now) {
        long expiresAt = now + ttlSeconds;
        String signature = sign(resourcePath, permission, expiresAt);
        return new ValetKey(resourcePath, permission, expiresAt, signature);
    }

    public boolean verify(ValetKey key, long now) {
        if (now > key.expiresAt()) {
            return false;
        }
        String expected = sign(key.resourcePath(), key.permission(), key.expiresAt());
        return expected.equals(key.signature());
    }

    private String sign(String resourcePath, String permission, long expiresAt) {
        try {
            Mac mac = Mac.getInstance(ALGORITHM);
            mac.init(new SecretKeySpec(signingKey, ALGORITHM));
            String payload = resourcePath + "\n" + permission + "\n" + expiresAt;
            byte[] digest = mac.doFinal(payload.getBytes(StandardCharsets.UTF_8));
            return Base64.getUrlEncoder().withoutPadding().encodeToString(digest);
        } catch (Exception e) {
            throw new IllegalStateException("signing failed", e);
        }
    }

    public static void main(String[] args) {
        byte[] signingKey = "a-32-byte-test-signing-key-here".getBytes(StandardCharsets.UTF_8);
        ValetKeyService service = new ValetKeyService(signingKey);
        long now = System.currentTimeMillis() / 1000;
        ValetKey key = service.issue("uploads/report.pdf", "write", 180, now);
        System.out.println("valet key valid " + service.verify(key, now));
    }
}
```

## 18. References

1. Homer, A., Sharp, J., Brader, L., Narumoto, M., Swanson, T., "Valet Key
   pattern," in *Cloud Design Patterns. Prescriptive Architecture Guidance
   for Cloud Applications*, Microsoft patterns and practices, first
   published 2014, maintained on the Azure Architecture Center, verified
   2026-08-03. https://learn.microsoft.com/en-us/azure/architecture/patterns/valet-key
2. Amazon Web Services, "Sharing objects with presigned URLs," Amazon S3
   User Guide, verified 2026-08-03.
   https://docs.aws.amazon.com/AmazonS3/latest/userguide/ShareObjectPreSignedURL.html
3. Google Cloud, "Signed URLs," Cloud Storage documentation, verified
   2026-08-03. https://docs.cloud.google.com/storage/docs/access-control/signed-urls
4. Cloudflare, "Presigned URLs," R2 API documentation, verified 2026-08-03.
   https://developers.cloudflare.com/r2/api/s3/presigned-urls/
5. Microsoft, Azure Architecture Center, "Cloud Design Patterns" index,
   verified 2026-08-03. https://learn.microsoft.com/en-us/azure/architecture/patterns/
